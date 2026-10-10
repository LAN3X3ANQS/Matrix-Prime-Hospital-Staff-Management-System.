from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import secrets
import socket
import ssl
import threading
import time
import tempfile
from importlib import import_module
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from database.database import authenticate
from networking.config import APP_DATA_DIR
from networking.config import server_request_context

PORT = 48731
CERT_PATH = APP_DATA_DIR / "lan-server-cert.pem"
KEY_PATH = APP_DATA_DIR / "lan-server-key.pem"
CLIENTS_PATH = APP_DATA_DIR / "paired-clients.json"
PAIR_CODE_LIFETIME_SECONDS = 300
MAX_PAIR_ATTEMPTS = 10
MAX_PAIRED_WORKSTATIONS = 500
MAX_REQUEST_BYTES = 128 * 1024 * 1024
_paired_clients = {}
_sessions = {}
_login_failures = {}
_pair_code = None
_pair_deadline = 0
_pair_attempts = 0
_lock = threading.Lock()
_logger = logging.getLogger("matrix_prime_hospital.lan")

ADMIN_ONLY = {
    ("database.database", name)
    for name in (
        "get_nurses", "get_nurse_by_id", "get_staff", "get_staff_by_id",
        "generate_staff_id", "add_staff", "update_staff", "deactivate_staff",
        "change_password", "get_pending_password_roles", "add_nurse",
        "update_nurse", "deactivate_nurse",
    )
} | {
    ("records.leave_records", name)
    for name in (
        "create_leave_record", "get_leave_records", "update_leave_record",
        "delete_leave_record",
    )
} | {
    ("records.shift_records", name)
    for name in (
        "create_shift_record", "get_shift_records", "update_shift_record",
        "delete_shift_record",
    )
} | {
    ("database.backups", "create_backup"),
    ("database.backups", "restore_backup"),
}
RPC_METHODS = {
    ("database.database", name)
    for name in (
        "get_nurses", "get_active_nurses", "get_nurse_by_id", "get_staff",
        "get_staff_by_id", "get_active_staff", "add_staff", "update_staff",
        "deactivate_staff", "add_nurse", "update_nurse", "deactivate_nurse",
        "mark_attendance", "record_sign_out",
        "get_attendance_for_staff_shift", "get_attendance_for_date",
        "get_attendance_by_date_range", "get_attendance_by_nurse",
        "change_password", "get_pending_password_roles",
    )
} | {
    ("records.leave_records", name)
    for name in (
        "create_leave_record", "get_leave_records", "update_leave_record",
        "delete_leave_record",
    )
} | {
    ("records.shift_records", name)
    for name in (
        "create_shift_record", "get_shift_records", "update_shift_record",
        "delete_shift_record",
    )
} | {
    ("networking.server", name)
    for name in ("get_paired_workstations", "set_workstation_blocked")
}
ADMIN_ONLY |= {
    ("networking.server", "get_paired_workstations"),
    ("networking.server", "set_workstation_blocked"),
}


def _encode(value):
    if isinstance(value, bytes):
        return {"__bytes__": base64.b64encode(value).decode("ascii")}
    if isinstance(value, set):
        return {"__set__": [_encode(item) for item in sorted(value)]}
    if isinstance(value, tuple):
        return {"__tuple__": [_encode(item) for item in value]}
    if isinstance(value, list):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _encode(item) for key, item in value.items()}
    if isinstance(value, (datetime,)):
        return value.isoformat()
    return value


def _decode(value):
    if isinstance(value, list):
        return [_decode(item) for item in value]
    if isinstance(value, dict):
        if set(value) == {"__bytes__"}:
            return base64.b64decode(value["__bytes__"], validate=True)
        if set(value) == {"__tuple__"}:
            return tuple(_decode(item) for item in value["__tuple__"])
        if set(value) == {"__set__"}:
            return set(_decode(value["__set__"]))
        if set(value) == {"__staff__"}:
            from database.models import Staff

            fields = value["__staff__"]
            return Staff(
                fields["id"],
                fields["name"],
                fields["staff_id"],
                fields["phone"],
                fields["status"],
            )
        return {key: _decode(item) for key, item in value.items()}
    return value


def _ensure_certificate():
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CERT_PATH.is_file() and KEY_PATH.is_file():
        return
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Matrix Prime Hospital LAN"),
    ])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(minutes=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    KEY_PATH.write_bytes(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    CERT_PATH.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))


def _fingerprint():
    certificate = x509.load_pem_x509_certificate(CERT_PATH.read_bytes())
    return certificate.fingerprint(hashes.SHA256()).hex()


def _load_clients():
    global _paired_clients
    if CLIENTS_PATH.is_file():
        try:
            _paired_clients = json.loads(CLIENTS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError("Paired workstation credentials could not be read.") from error
    else:
        _paired_clients = {}


def _persist_clients():
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=APP_DATA_DIR,
            prefix=".paired-clients-",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(_paired_clients, temporary_file, indent=2)
        os.replace(temporary_path, CLIENTS_PATH)
    except OSError:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def _local_address():
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 80))
        return probe.getsockname()[0]
    finally:
        probe.close()


def _client_allowed(client_key):
    if not isinstance(client_key, str) or len(client_key) < 32:
        return False
    digest = hashlib.sha256(client_key.encode("utf-8")).hexdigest()
    with _lock:
        return any(
            hmac.compare_digest(digest, stored)
            and not details.get("blocked", False)
            for stored, details in _paired_clients.items()
        )


def _database_backup_details():
    from database.backups import create_backup

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "current-database.sqlite3"
        with server_request_context():
            create_backup(path)
        payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest(), len(payload)


def _record_workstation_backup(client_digest, database_digest, backup_bytes):
    if (
        not isinstance(database_digest, str)
        or len(database_digest) != 64
        or any(character not in "0123456789abcdef" for character in database_digest)
        or not isinstance(backup_bytes, int)
        or backup_bytes <= 0
    ):
        raise ValueError("The workstation backup details are invalid.")

    with _lock:
        details = _paired_clients.get(client_digest)
        if details is None or details.get("blocked", False):
            raise PermissionError("This workstation is not paired with the server.")
        previous = dict(details)
        details["backup_digest"] = database_digest
        details["backup_bytes"] = backup_bytes
        details["backup_completed_at"] = datetime.now(timezone.utc).isoformat()
        try:
            _persist_clients()
        except OSError:
            details.clear()
            details.update(previous)
            raise


def _set_workstation_blocked(client_digest, blocked):
    if (
        not isinstance(client_digest, str)
        or len(client_digest) != 64
        or any(character not in "0123456789abcdef" for character in client_digest)
        or not isinstance(blocked, bool)
    ):
        raise ValueError("The workstation selection is invalid.")
    with _lock:
        details = _paired_clients.get(client_digest)
        if details is None:
            raise ValueError("That workstation is no longer paired.")
        previous = details.get("blocked", False)
        details["blocked"] = blocked
        try:
            _persist_clients()
        except OSError:
            details["blocked"] = previous
            raise
        if blocked:
            for token, session in list(_sessions.items()):
                if hmac.compare_digest(session["client_digest"], client_digest):
                    _sessions.pop(token, None)


def _get_paired_workstations():
    database_digest, database_bytes = _database_backup_details()
    with _lock:
        clients = [
            (digest, dict(details))
            for digest, details in _paired_clients.items()
        ]

    workstations = []
    for digest, details in clients:
        backup_complete = details.get("backup_digest") == database_digest
        workstations.append({
            "id": digest,
            "name": details.get("name", "Workstation"),
            "paired_at": details.get("paired_at"),
            "last_seen": details.get("last_seen"),
            "blocked": bool(details.get("blocked", False)),
            "backup_completed_at": details.get("backup_completed_at"),
            "backup_bytes": details.get("backup_bytes", 0),
            "current_database_bytes": database_bytes,
            "backup_progress": 100 if backup_complete else 0,
            "backup_complete": backup_complete,
        })
    return workstations


def get_paired_workstations():
    return _get_paired_workstations()


def set_workstation_blocked(client_digest, blocked):
    _set_workstation_blocked(client_digest, blocked)


class _Handler(BaseHTTPRequestHandler):
    server_version = "MPH-LAN"
    sys_version = ""

    def log_message(self, format_string, *args):
        return

    def _reply(self, status, result=None, error=None):
        payload = {"result": _encode(result)}
        if error is not None:
            payload["error"] = error
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        try:
            source = ipaddress.ip_address(self.client_address[0])
        except ValueError:
            self._reply(403, error="The request did not come from a valid network address.")
            return
        if not source.is_private and not source.is_loopback:
            self._reply(403, error="The LAN server accepts private-network connections only.")
            return
        length = self.headers.get("Content-Length")
        try:
            length = int(length)
        except (TypeError, ValueError):
            self._reply(400, error="Invalid request length.")
            return
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._reply(413, error="Request is too large.")
            return
        try:
            request = _decode(json.loads(self.rfile.read(length).decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            self._reply(400, error="Invalid request.")
            return

        if self.path == "/pair":
            self._pair(request)
        elif self.path == "/login":
            self._login(request)
        elif self.path == "/logout":
            self._logout()
        elif self.path == "/backup":
            self._backup(request)
        elif self.path == "/rpc":
            self._rpc(request)
        else:
            self._reply(404, error="Unknown endpoint.")

    def _pair(self, request):
        global _pair_code, _pair_attempts
        code = request.get("code") if isinstance(request, dict) else None
        with _lock:
            if (
                not _pair_code
                or time.monotonic() > _pair_deadline
                or _pair_attempts >= MAX_PAIR_ATTEMPTS
                or not isinstance(code, str)
                or not hmac.compare_digest(code, _pair_code)
            ):
                _pair_attempts += 1
                if _pair_attempts >= MAX_PAIR_ATTEMPTS:
                    _pair_code = None
                self._reply(403, error="The pairing PIN is invalid or expired.")
                return
            if len(_paired_clients) >= MAX_PAIRED_WORKSTATIONS:
                self._reply(403, error="The server has reached its workstation limit.")
                return
            client_key = secrets.token_urlsafe(32)
            digest = hashlib.sha256(client_key.encode("utf-8")).hexdigest()
            paired_at = datetime.now(timezone.utc).isoformat()
            _paired_clients[digest] = {
                "name": str(request.get("client_name", "Workstation"))[:120],
                "paired_at": paired_at,
                "last_seen": paired_at,
                "blocked": False,
            }
            try:
                _persist_clients()
            except OSError:
                _paired_clients.pop(digest, None)
                self._reply(500, error="The server could not save this workstation pairing.")
                return
        self._reply(200, {"client_key": client_key})

    def _authorized(self, require_session=True):
        client_key = self.headers.get("X-MPH-Client-Key", "")
        if not _client_allowed(client_key):
            self._reply(403, error="This workstation is not paired with the server.")
            return None
        client_digest = hashlib.sha256(client_key.encode("utf-8")).hexdigest()
        with _lock:
            client = _paired_clients.get(client_digest)
            if client is not None:
                client["last_seen"] = datetime.now(timezone.utc).isoformat()
        if not require_session:
            return None
        session = self.headers.get("X-MPH-Session", "")
        entry = _sessions.get(session)
        if (
            not entry
            or entry["expires"] < time.monotonic()
            or not hmac.compare_digest(entry["client_digest"], client_digest)
        ):
            self._reply(403, error="Your session expired. Sign in again.")
            return None
        return entry

    def _login(self, request):
        if not _client_allowed(self.headers.get("X-MPH-Client-Key", "")):
            self._reply(403, error="This workstation is not paired with the server.")
            return
        source_ip = self.client_address[0]
        failures, blocked_until = _login_failures.get(source_ip, (0, 0))
        if time.monotonic() < blocked_until:
            self._reply(429, error="Too many sign-in attempts. Wait one minute and try again.")
            return
        password = request.get("password") if isinstance(request, dict) else None
        with server_request_context():
            role = authenticate(password)
        if role is None:
            failures += 1
            if failures >= 5:
                _login_failures[source_ip] = (0, time.monotonic() + 60)
            else:
                _login_failures[source_ip] = (failures, 0)
            self._reply(403, error="Invalid password.")
            return
        _login_failures.pop(source_ip, None)
        session_token = secrets.token_urlsafe(32)
        _sessions[session_token] = {
            "role": role,
            "client_digest": hashlib.sha256(
                self.headers.get("X-MPH-Client-Key", "").encode("utf-8")
            ).hexdigest(),
            "expires": time.monotonic() + 8 * 60 * 60,
        }
        self._reply(200, {"role": role, "session_token": session_token})

    def _logout(self):
        session_info = self._authorized()
        if session_info is None:
            return
        session = self.headers.get("X-MPH-Session", "")
        _sessions.pop(session, None)
        self._reply(200, True)

    def _backup(self, request):
        session = self._authorized()
        if session is None:
            return
        if session["role"] != "ADMIN":
            self._reply(403, error="Administrator access is required.")
            return
        try:
            from database.backups import create_backup, restore_backup
            import tempfile

            action = request.get("action") if isinstance(request, dict) else None
            if action == "create":
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "hospital-backup.sqlite3"
                    with server_request_context():
                        create_backup(path)
                    result = path.read_bytes()
            elif action == "complete":
                details = request.get("data")
                if not isinstance(details, dict):
                    raise ValueError("The workstation backup details are invalid.")
                _record_workstation_backup(
                    session["client_digest"],
                    details.get("digest"),
                    details.get("size"),
                )
                result = True
            elif action == "restore":
                payload = request.get("data")
                if not isinstance(payload, bytes):
                    raise ValueError("The backup file could not be read.")
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "hospital-backup.sqlite3"
                    path.write_bytes(payload)
                    with server_request_context():
                        restore_backup(path)
                    result = True
            else:
                raise ValueError("Unknown backup operation.")
        except (OSError, ValueError) as error:
            self._reply(400, error=str(error))
        except Exception:
            _logger.exception("LAN backup operation failed")
            self._reply(500, error="The server could not complete the backup operation.")
        else:
            self._reply(200, result=result)

    def _rpc(self, request):
        session = self._authorized()
        if session is None:
            return
        if not isinstance(request, dict):
            self._reply(400, error="Invalid operation request.")
            return
        key = (request.get("module"), request.get("function"))
        if key not in RPC_METHODS:
            self._reply(404, error="This operation is not available through the server.")
            return
        if session["role"] != "ADMIN" and key in ADMIN_ONLY:
            self._reply(403, error="Administrator access is required.")
            return
        try:
            module = import_module(key[0])
            function = getattr(module, key[1])
            with server_request_context():
                result = function(
                    *request.get("args", []),
                    **request.get("kwargs", {}),
                )
            if session["role"] == "STAFF" and key in {
                ("database.database", "get_active_nurses"),
                ("database.database", "get_active_staff"),
            }:
                result = [
                    tuple(
                        (*staff[:3], "", *staff[4:8], None)
                    )
                    for staff in result
                ]
        except (ValueError, PermissionError) as error:
            self._reply(400, error=str(error))
        except Exception:
            _logger.exception("LAN RPC failed for %s.%s", *key)
            self._reply(500, error="The server could not complete the request.")
        else:
            self._reply(200, result=result)


class LanServer:
    def __init__(self, port=PORT):
        global _pair_code, _pair_deadline, _pair_attempts
        _ensure_certificate()
        _load_clients()
        self.server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
        self.port = self.server.server_address[1]
        self.server.daemon_threads = True
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.minimum_version = ssl.TLSVersion.TLSv1_2
        tls.load_cert_chain(str(CERT_PATH), str(KEY_PATH))
        self.server.socket = tls.wrap_socket(self.server.socket, server_side=True)
        _pair_code = f"{secrets.randbelow(1_000_000):06d}"
        _pair_deadline = time.monotonic() + PAIR_CODE_LIFETIME_SECONDS
        _pair_attempts = 0
        self.pairing_code = _pair_code
        self.address = _local_address()
        self.fingerprint = _fingerprint()
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            name="mph-lan-server",
            daemon=True,
        )

    def start(self):
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def create_pairing_code(self):
        global _pair_code, _pair_deadline, _pair_attempts
        with _lock:
            _pair_code = f"{secrets.randbelow(1_000_000):06d}"
            _pair_deadline = time.monotonic() + PAIR_CODE_LIFETIME_SECONDS
            _pair_attempts = 0
            self.pairing_code = _pair_code
        return self.pairing_code

    def get_pairing_details(self):
        return {
            "host": self.address,
            "port": self.port,
            "fingerprint": self.fingerprint,
            "code": self.pairing_code,
        }

    @staticmethod
    def get_paired_workstations():
        return _get_paired_workstations()

    @staticmethod
    def set_workstation_blocked(client_digest, blocked):
        _set_workstation_blocked(client_digest, blocked)

    @staticmethod
    def revoke_all_workstations():
        with _lock:
            previous = dict(_paired_clients)
            _paired_clients.clear()
            try:
                _persist_clients()
            except OSError:
                _paired_clients.update(previous)
                raise
            _sessions.clear()
