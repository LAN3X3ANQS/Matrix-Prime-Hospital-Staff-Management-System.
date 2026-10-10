import base64
import hashlib
import http.client
import ipaddress
import json
import secrets
import ssl
import socket

from networking.config import get_client_config, save_client_config

_session_token = None
_session_role = None


def _encode(value):
    if isinstance(value, bytes):
        return {"__bytes__": base64.b64encode(value).decode("ascii")}
    if isinstance(value, set):
        return {"__set__": [_encode(item) for item in sorted(value)]}
    if value.__class__.__name__ in {"Staff", "Nurse"} and all(
        hasattr(value, field) for field in ("name", "staff_id", "phone", "status")
    ):
        return {
            "__staff__": {
                "id": value.id,
                "name": value.name,
                "staff_id": value.staff_id,
                "phone": value.phone,
                "status": value.status,
            }
        }
    if isinstance(value, tuple):
        return {"__tuple__": [_encode(item) for item in value]}
    if isinstance(value, list):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _encode(item) for key, item in value.items()}
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


def _connection(config):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    connection = http.client.HTTPSConnection(
        config["host"],
        int(config["port"]),
        context=context,
        timeout=8,
    )
    connection._mph_fingerprint = config["fingerprint"].lower().replace(":", "")
    original_connect = connection.connect

    def pinned_connect():
        original_connect()
        actual = hashlib.sha256(
            connection.sock.getpeercert(binary_form=True)
        ).hexdigest()
        if not secrets.compare_digest(actual, connection._mph_fingerprint):
            connection.close()
            raise ssl.SSLError(
                "The hospital server certificate does not match the verified fingerprint."
            )

    connection.connect = pinned_connect
    return connection


def _post(config, path, body, session=True):
    connection = _connection(config)
    headers = {"Content-Type": "application/json"}
    headers["X-MPH-Client-Key"] = config["client_key"]
    if session and _session_token:
        headers["X-MPH-Session"] = _session_token
    try:
        connection.request(
            "POST",
            path,
            body=json.dumps(_encode(body)).encode("utf-8"),
            headers=headers,
        )
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
    except ssl.SSLError as error:
        raise ConnectionError(str(error)) from error
    except (OSError, http.client.HTTPException, ValueError) as error:
        raise ConnectionError(
            "Could not securely connect to the hospital server. "
            "Check that it is running and both computers are on the hospital network."
        ) from error
    finally:
        connection.close()
    if response.status >= 400:
        message = payload.get("error", "The server rejected the request.")
        if response.status == 403:
            raise PermissionError(message)
        if response.status == 400:
            raise ValueError(message)
        raise RuntimeError(message)
    return _decode(payload.get("result"))


def get_server_fingerprint(host, port=48731):
    try:
        address = ipaddress.ip_address(host.strip())
        port = int(port)
        if not address.is_private or not 1 <= port <= 65535:
            raise ValueError
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("Enter a valid private server address and port.") from error

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((str(address), port), timeout=8) as raw_socket:
            with context.wrap_socket(
                raw_socket,
                server_hostname=str(address),
            ) as connection:
                return hashlib.sha256(
                    connection.getpeercert(binary_form=True)
                ).hexdigest()
    except (OSError, ssl.SSLError) as error:
        raise ConnectionError(
            "Could not read the server fingerprint. Check the address, port, "
            "and that the server is running on the hospital network."
        ) from error


def parse_pairing_code(pairing_code):
    try:
        if not isinstance(pairing_code, str):
            raise ValueError
        prefix, encoded = pairing_code.strip().split(":", 1)
        if prefix == "MPH2":
            raw = base64.b64decode(
                encoded + "=" * (-len(encoded) % 4),
                altchars=b"-_",
                validate=True,
            )
            if len(raw) not in (41, 53):
                raise ValueError
            address_size = len(raw) - 37
            address = ipaddress.ip_address(raw[:address_size])
            port = int.from_bytes(raw[address_size : address_size + 2], "big")
            fingerprint = raw[address_size + 2 : address_size + 34].hex()
            code_number = int.from_bytes(raw[address_size + 34 :], "big")
            if code_number > 999999:
                raise ValueError
            code = f"{code_number:06d}"
        elif prefix == "MPH1":
            raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
            details = json.loads(raw.decode("utf-8"))
            if not isinstance(details, dict) or not isinstance(details.get("host"), str):
                raise ValueError
            address = ipaddress.ip_address(details["host"])
            port = int(details["port"])
            fingerprint = details["fingerprint"]
            code = details["code"]
        else:
            raise ValueError
        if (
            not address.is_private
            or not 1 <= port <= 65535
            or not isinstance(fingerprint, str)
            or len(fingerprint) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in fingerprint)
            or not isinstance(code, str)
            or len(code) != 6
            or not code.isdigit()
        ):
            raise ValueError
        return {
            "host": str(address),
            "port": port,
            "fingerprint": fingerprint,
            "code": code,
        }
    except (
        TypeError,
        KeyError,
        ValueError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        raise ValueError("That is not a valid Matrix Prime Hospital pairing code.") from error


def pair_with_server(
    pairing_pin=None,
    *,
    host=None,
    fingerprint=None,
    port=48731,
):
    if host is None:
        details = parse_pairing_code(pairing_pin)
    else:
        try:
            address = ipaddress.ip_address(host.strip())
            if (
                not address.is_private
                or not isinstance(pairing_pin, str)
                or len(pairing_pin) != 6
                or not pairing_pin.isdigit()
                or not isinstance(fingerprint, str)
                or len(fingerprint) != 64
                or any(
                    character not in "0123456789abcdefABCDEF"
                    for character in fingerprint
                )
                or not 1 <= int(port) <= 65535
            ):
                raise ValueError
        except (AttributeError, TypeError, ValueError) as error:
            raise ValueError(
                "Enter a valid private server address, six-digit PIN, and "
                "64-character TLS fingerprint."
            ) from error
        details = {
            "host": str(address),
            "port": int(port),
            "fingerprint": fingerprint.lower(),
            "code": pairing_pin,
        }
    config = {
        "host": details["host"],
        "port": int(details["port"]),
        "fingerprint": details["fingerprint"],
        "client_key": "",
    }
    result = _post(
        config,
        "/pair",
        {"code": details["code"], "client_name": socket.gethostname()},
        session=False,
    )
    config["client_key"] = result["client_key"]
    save_client_config(config)
    return config


def remote_login(password):
    global _session_token, _session_role
    config = get_client_config()
    result = _post(config, "/login", {"password": password}, session=False)
    _session_token = result["session_token"]
    _session_role = result["role"]
    return _session_role


def remote_logout():
    global _session_token, _session_role
    if _session_token:
        try:
            _post(get_client_config(), "/logout", {}, session=True)
        finally:
            _session_token = None
            _session_role = None


def remote_call(module, function, args, kwargs):
    config = get_client_config()
    if not _session_token:
        raise PermissionError("Sign in to the hospital server to continue.")
    return _post(
        config,
        "/rpc",
        {
            "module": module,
            "function": function,
            "args": args,
            "kwargs": kwargs,
        },
    )


def remote_backup(action, data=None):
    config = get_client_config()
    result = _post(
        config,
        "/backup",
        {"action": action, "data": data},
    )
    return result


def remote_server_call(function, args=(), kwargs=None):
    return remote_call(
        "networking.server",
        function,
        args,
        kwargs or {},
    )
