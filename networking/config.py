import json
import ipaddress
import os
from pathlib import Path
import tempfile
import threading


APP_DATA_DIR = Path(
    os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
) / "Matrix Prime Hospital"
CLIENT_CONFIG_PATH = APP_DATA_DIR / "server-connection.json"
_server_request_state = threading.local()


def is_remote_client():
    return (
        not getattr(_server_request_state, "active", False)
        and get_client_config() is not None
    )


class server_request_context:
    def __enter__(self):
        self.previous = getattr(_server_request_state, "active", False)
        _server_request_state.active = True

    def __exit__(self, exception_type, exception, traceback):
        _server_request_state.active = self.previous


def get_client_config():
    if not CLIENT_CONFIG_PATH.is_file():
        return None
    try:
        with CLIENT_CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "The saved hospital server connection could not be read."
        ) from error
    if not isinstance(config, dict) or not all(
        config.get(key)
        for key in ("host", "port", "fingerprint", "client_key")
    ):
        raise RuntimeError("The saved hospital server connection is incomplete.")
    if not all(
        isinstance(config[key], str)
        for key in ("host", "fingerprint", "client_key")
    ):
        raise RuntimeError("The saved hospital server connection is invalid.")
    try:
        address = ipaddress.ip_address(config["host"])
        port = int(config["port"])
    except (ValueError, TypeError) as error:
        raise RuntimeError("The saved hospital server address is invalid.") from error
    if (
        not address.is_private
        or not 1 <= port <= 65535
        or not isinstance(config["fingerprint"], str)
        or len(config["fingerprint"]) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in config["fingerprint"])
        or not isinstance(config["client_key"], str)
        or len(config["client_key"]) < 32
    ):
        raise RuntimeError("The saved hospital server connection is invalid.")
    return config


def save_client_config(config):
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=APP_DATA_DIR,
            prefix=".server-connection-",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(config, temporary_file)
        os.replace(temporary_path, CLIENT_CONFIG_PATH)
    except OSError:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def clear_client_config():
    CLIENT_CONFIG_PATH.unlink(missing_ok=True)
