from contextlib import closing
import hashlib
import os
import sqlite3
import tempfile
from pathlib import Path

from database.database import DATABASE_PATH


REQUIRED_TABLES = {
    "auth_users",
    "nurses",
}


def create_backup(destination):
    destination = Path(destination)
    if destination.resolve() == DATABASE_PATH.resolve():
        raise ValueError("Choose a different location for the backup file.")

    from networking.config import is_remote_client

    if is_remote_client():
        from networking.transport import remote_backup

        payload = remote_backup("create")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=destination.parent,
                prefix=f".{destination.stem}-",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(payload)
            os.replace(temporary_path, destination)
        except OSError:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
        digest = hashlib.sha256()
        backup_size = 0
        with destination.open("rb") as backup_file:
            for chunk in iter(lambda: backup_file.read(1024 * 1024), b""):
                digest.update(chunk)
                backup_size += len(chunk)
        database_digest = hashlib.sha256(payload).hexdigest()
        if backup_size != len(payload) or digest.hexdigest() != database_digest:
            raise OSError("The saved backup does not match the server snapshot.")
        try:
            remote_backup(
                "complete",
                {
                    "digest": database_digest,
                    "size": backup_size,
                },
            )
        except (ConnectionError, OSError, RuntimeError, ValueError) as error:
            raise RuntimeError(
                f"The backup was saved to {destination}, but the server "
                "could not verify its completion."
            ) from error
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{destination.stem}-",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        with closing(sqlite3.connect(DATABASE_PATH)) as source:
            with closing(sqlite3.connect(temporary_path)) as backup:
                source.backup(backup)
                result = backup.execute("PRAGMA integrity_check").fetchone()
                if result is None or result[0] != "ok":
                    raise sqlite3.DatabaseError(
                        "The database integrity check failed."
                    )

        os.replace(temporary_path, destination)
        return destination
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def restore_backup(source_path):
    source_path = Path(source_path)
    from networking.config import is_remote_client

    if is_remote_client():
        from networking.transport import remote_backup

        remote_backup("restore", source_path.read_bytes())
        return source_path

    if source_path.resolve() == DATABASE_PATH.resolve():
        raise ValueError(
            "Select a separate backup file, not the active database."
        )
    if not source_path.is_file():
        raise ValueError("The selected backup file does not exist.")

    temporary_path = None
    try:
        source_uri = f"{source_path.resolve().as_uri()}?mode=ro"
        with closing(sqlite3.connect(source_uri, uri=True)) as source:
            integrity = source.execute("PRAGMA integrity_check").fetchone()
            if integrity is None or integrity[0] != "ok":
                raise ValueError("The selected file is not a healthy database.")

            tables = {
                row[0]
                for row in source.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if not REQUIRED_TABLES.issubset(tables):
                raise ValueError(
                    "The selected file is not a complete StaffRoster backup."
                )

            auth_columns = {
                row[1] for row in source.execute("PRAGMA table_info(auth_users)")
            }
            staff_columns = {
                row[1] for row in source.execute("PRAGMA table_info(nurses)")
            }
            if not {"role", "password_hash", "password_salt"}.issubset(
                auth_columns
            ):
                raise ValueError(
                    "The backup does not contain valid authentication data."
                )
            if not {"name", "staff_id"}.issubset(staff_columns):
                raise ValueError(
                    "The backup does not contain a staff directory."
                )

            DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                prefix=f".{DATABASE_PATH.stem}-restore-",
                suffix=".tmp",
                dir=DATABASE_PATH.parent,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)

            with closing(sqlite3.connect(temporary_path)) as restored:
                source.backup(restored)
                restored_integrity = restored.execute(
                    "PRAGMA integrity_check"
                ).fetchone()
                if (
                    restored_integrity is None
                    or restored_integrity[0] != "ok"
                ):
                    raise sqlite3.DatabaseError(
                        "The restored database integrity check failed."
                    )

        from database.database import initialize_database

        initialize_database(database_path=temporary_path)
        with closing(sqlite3.connect(temporary_path)) as restored:
            restored_integrity = restored.execute(
                "PRAGMA integrity_check"
            ).fetchone()
            if restored_integrity is None or restored_integrity[0] != "ok":
                raise sqlite3.DatabaseError(
                    "The migrated database integrity check failed."
                )

        os.replace(temporary_path, DATABASE_PATH)
        return DATABASE_PATH
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
