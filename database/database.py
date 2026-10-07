import sqlite3
import hashlib
import secrets
import os
import sys
import threading
from datetime import date
from pathlib import Path

if getattr(sys, "frozen", False):
    DATABASE_PATH = (
        Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        / "Matrix Prime Hospital"
        / "nurse_roster.db"
    )
else:
    DATABASE_PATH = Path(__file__).parent.parent / "data" / "nurse_roster.db"

VALID_NURSE_STATUSES = [
    "Active",
    "Inactive",
]

VALID_ATTENDANCE_STATUSES = [
    "Present",
    "Absent",
    "Late",
]

VALID_ROLES = [
    "ADMIN",
    "STAFF",
]

VALID_STAFF_TYPES = [
    "Admin",
    "Janitor",
    "Front Desk",
    "Nurse",
    "Lab Tech",
    "Doctor",
]

STAFF_ID_PREFIXES = {
    "Admin": "ADM",
    "Janitor": "JAN",
    "Front Desk": "FD",
    "Nurse": "NUR",
    "Lab Tech": "LAB",
    "Doctor": "DOC",
}

VALID_SHIFTS = ["Morning", "Night", "Legacy"]
_database_path_override = threading.local()

def get_connection():
    from networking.config import is_remote_client

    if is_remote_client():
        raise RuntimeError(
            "Direct database access is disabled on a paired workstation."
        )
    database_path = getattr(
        _database_path_override,
        "path",
        DATABASE_PATH,
    )
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    return connection


def hash_password(password, salt=None):
    if not isinstance(password, str) or not password:
        raise ValueError("Password is required.")
    if salt is None:
        salt = secrets.token_bytes(32)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600000,
    )

    return (
        password_hash.hex(),
        salt.hex(),
    )


def verify_password(password, stored_hash, stored_salt):
    if not isinstance(password, str) or not password:
        return False
    try:
        salt = bytes.fromhex(stored_salt)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600000,
        )

        return secrets.compare_digest(
            password_hash.hex(),
            stored_hash,
        )

    except (ValueError, TypeError):
        return False


def initialize_authentication():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            must_change INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(auth_users)")
    columns = {row[1] for row in cursor.fetchall()}
    if "must_change" not in columns:
        cursor.execute("""
            ALTER TABLE auth_users
            ADD COLUMN must_change INTEGER NOT NULL DEFAULT 1
        """)

    cursor.execute("SELECT role FROM auth_users")
    existing_roles = {row[0] for row in cursor.fetchall()}
    bootstrap_passwords = {}

    for role in VALID_ROLES:
        if role in existing_roles:
            continue

        environment_name = f"NURSEROSTER_{role}_PASSWORD"
        password = os.environ.get(environment_name)
        if not password:
            password = secrets.token_urlsafe(18)
            bootstrap_passwords[role] = password
        if len(password) < 12:
            connection.close()
            raise ValueError(
                f"{environment_name} must contain at least 12 characters."
            )

        other_role = "STAFF" if role == "ADMIN" else "ADMIN"
        if (
            other_role in bootstrap_passwords
            and password == bootstrap_passwords[other_role]
        ):
            connection.close()
            raise ValueError("Admin and Staff passwords must be different.")
        cursor.execute(
            """
            SELECT password_hash, password_salt
            FROM auth_users
            WHERE role = ?
            """,
            (other_role,),
        )
        other_credentials = cursor.fetchone()
        if other_credentials and verify_password(
            password,
            other_credentials[0],
            other_credentials[1],
        ):
            connection.close()
            raise ValueError("Admin and Staff passwords must be different.")

        password_hash, password_salt = hash_password(password)
        cursor.execute(
            """
            INSERT INTO auth_users (
                role,
                password_hash,
                password_salt,
                must_change
            )
            VALUES (?, ?, ?, 1)
            """,
            (role, password_hash, password_salt),
        )

    connection.commit()
    connection.close()
    return bootstrap_passwords


def authenticate(password):
    if not password:
        return None
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            role,
            password_hash,
            password_salt
        FROM auth_users
        ORDER BY
            CASE
                WHEN role = 'ADMIN' THEN 1
                WHEN role = 'STAFF' THEN 2
                ELSE 3
            END
    """)

    users = cursor.fetchall()
    connection.close()

    for role, password_hash, password_salt in users:
        if verify_password(
            password,
            password_hash,
            password_salt,
        ):
            return role

    return None


def get_pending_password_roles():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT role
        FROM auth_users
        WHERE must_change = 1
        ORDER BY role
    """)
    roles = {row[0] for row in cursor.fetchall()}
    connection.close()
    return roles


def change_password(role, new_password):
    if role not in VALID_ROLES:
        raise ValueError("Invalid authentication role.")
    if not isinstance(new_password, str):
        raise ValueError("Password must be text.")

    if len(new_password) < 12 or not new_password.strip():
        raise ValueError(
            "Password must contain at least 12 characters."
        )

    password_hash, password_salt = hash_password(
        new_password
    )

    connection = get_connection()
    cursor = connection.cursor()

    other_role = "STAFF" if role == "ADMIN" else "ADMIN"
    cursor.execute(
        """
        SELECT password_hash, password_salt
        FROM auth_users
        WHERE role = ?
        """,
        (other_role,),
    )
    other_credentials = cursor.fetchone()
    if other_credentials and verify_password(
        new_password,
        other_credentials[0],
        other_credentials[1],
    ):
        connection.close()
        raise ValueError(
            "Admin and Staff passwords must be different."
        )

    cursor.execute(
        """
        UPDATE auth_users
        SET
            password_hash = ?,
            password_salt = ?,
            must_change = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE role = ?
        """,
        (password_hash, password_salt, role),
    )

    updated = cursor.rowcount
    if updated:
        connection.commit()
    connection.close()

    if updated == 0:
        raise ValueError(
            "The selected authentication role does not exist."
        )


def _initialize_database():
    from networking.config import is_remote_client

    if is_remote_client():
        raise RuntimeError(
            "A paired workstation cannot initialize or modify a local database."
        )
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nurses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            staff_id TEXT UNIQUE NOT NULL,
            phone TEXT,
            status TEXT NOT NULL DEFAULT 'Active',
            rotation_position INTEGER,
            staff_type TEXT NOT NULL DEFAULT 'Nurse',
            unit TEXT NOT NULL DEFAULT '',
            profile_photo BLOB
        )
    """)

    cursor.execute("""
        PRAGMA table_info(nurses)
    """)

    columns = [column[1] for column in cursor.fetchall()]

    if "rotation_position" not in columns:
        cursor.execute("""
            ALTER TABLE nurses
            ADD COLUMN rotation_position INTEGER
        """)

    if "staff_type" not in columns:
        cursor.execute("""
            ALTER TABLE nurses
            ADD COLUMN staff_type TEXT NOT NULL DEFAULT 'Nurse'
        """)

    if "unit" not in columns:
        cursor.execute("""
            ALTER TABLE nurses
            ADD COLUMN unit TEXT NOT NULL DEFAULT ''
        """)

    if "profile_photo" not in columns:
        cursor.execute("""
            ALTER TABLE nurses
            ADD COLUMN profile_photo BLOB
        """)

    cursor.execute("""
        SELECT id
        FROM nurses
        WHERE rotation_position IS NULL
        ORDER BY staff_id
    """)

    unassigned_nurses = cursor.fetchall()

    for index, row in enumerate(unassigned_nurses):
        nurse_id = row[0]

        if index < 3:
            cursor.execute(
                """
                UPDATE nurses
                SET rotation_position = ?
                WHERE id = ?
                """,
                (
                    index,
                    nurse_id,
                ),
            )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nurse_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            attendance_time TEXT,
            status TEXT NOT NULL,
            shift TEXT NOT NULL DEFAULT 'Legacy',
            sign_out_time TEXT,
            UNIQUE(nurse_id, attendance_date, shift),
            FOREIGN KEY(nurse_id) REFERENCES nurses(id)
        )
    """)
    cursor.execute("PRAGMA table_info(attendance)")
    attendance_columns = {column[1] for column in cursor.fetchall()}
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'attendance'"
    )
    attendance_sql = cursor.fetchone()[0] or ""
    if (
        "shift" not in attendance_columns
        or "sign_out_time" not in attendance_columns
        or "UNIQUE(nurse_id, attendance_date, shift)" not in attendance_sql
    ):
        cursor.execute("ALTER TABLE attendance RENAME TO attendance_old")
        cursor.execute("""
            CREATE TABLE attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nurse_id INTEGER NOT NULL,
                attendance_date TEXT NOT NULL,
                attendance_time TEXT,
                status TEXT NOT NULL,
                shift TEXT NOT NULL DEFAULT 'Legacy',
                sign_out_time TEXT,
                UNIQUE(nurse_id, attendance_date, shift),
                FOREIGN KEY(nurse_id) REFERENCES nurses(id)
            )
        """)
        old_columns = {
            column[1]
            for column in cursor.execute("PRAGMA table_info(attendance_old)")
        }
        old_shift = "shift" if "shift" in old_columns else "'Legacy'"
        old_sign_out = (
            "sign_out_time" if "sign_out_time" in old_columns else "NULL"
        )
        cursor.execute(f"""
            INSERT INTO attendance (
                id,
                nurse_id,
                attendance_date,
                attendance_time,
                status,
                shift,
                sign_out_time
            )
            SELECT
                id,
                nurse_id,
                attendance_date,
                attendance_time,
                status,
                {old_shift},
                {old_sign_out}
            FROM attendance_old
        """)
        cursor.execute("DROP TABLE attendance_old")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nurse_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            reason TEXT,
            status TEXT NOT NULL DEFAULT 'Approved',
            FOREIGN KEY(nurse_id) REFERENCES nurses(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shift_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nurse_id INTEGER NOT NULL,
            shift_date TEXT NOT NULL,
            original_shift TEXT NOT NULL,
            new_shift TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(nurse_id) REFERENCES nurses(id)
        )
    """)

    connection.commit()
    connection.close()

    return initialize_authentication()


def initialize_database(database_path=None):
    from networking.config import is_remote_client

    if is_remote_client():
        raise RuntimeError(
            "A paired workstation cannot initialize or modify a local database."
        )
    if database_path is None:
        return _initialize_database()

    previous_path = getattr(_database_path_override, "path", None)
    _database_path_override.path = Path(database_path)
    try:
        return _initialize_database()
    finally:
        if previous_path is None:
            del _database_path_override.path
        else:
            _database_path_override.path = previous_path


def add_nurse(
    nurse,
    rotation_position=None,
    staff_type="Nurse",
    unit="",
    profile_photo=None,
):
    if not nurse.name.strip():
        raise ValueError("Nurse name is required.")
    if not nurse.staff_id.strip():
        raise ValueError("Staff ID is required.")
    if nurse.status not in VALID_NURSE_STATUSES:
        raise ValueError("Invalid nurse status.")
    if staff_type not in VALID_STAFF_TYPES:
        raise ValueError("Invalid staff category.")

    if rotation_position is not None:
        if rotation_position not in [0, 1, 2]:
            raise ValueError("Rotation position must be 0, 1, or 2.")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO nurses (
                name,
                staff_id,
                phone,
                status,
                rotation_position,
                staff_type,
                unit,
                profile_photo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nurse.name.strip(),
                nurse.staff_id.strip(),
                nurse.phone.strip() if nurse.phone else "",
                nurse.status,
                rotation_position,
                staff_type,
                unit.strip(),
                profile_photo,
            ),
        )

        connection.commit()

    except sqlite3.IntegrityError as error:
        connection.close()
        raise ValueError(
            "A nurse with this Staff ID already exists."
        ) from error

    connection.close()


def get_nurses():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT
    id,
    name,
    staff_id,
    phone,
    status,
    rotation_position,
    staff_type,
    unit,
    profile_photo
    FROM nurses
    ORDER BY name
    """)
    nurses = cursor.fetchall()
    connection.close()

    return nurses


def get_active_nurses():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT
    id,
    name,
    staff_id,
    phone,
    status,
    rotation_position,
    staff_type,
    unit,
    profile_photo
    FROM nurses
    WHERE status = 'Active'
    ORDER BY rotation_position
    """)
    nurses = cursor.fetchall()
    connection.close()

    return nurses


def get_nurse_by_id(nurse_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT
        id,
        name,
        staff_id,
        phone,
        status,
        rotation_position,
        staff_type,
        unit,
        profile_photo
        FROM nurses
        WHERE id = ?
        """,
        (nurse_id,),
    )
    nurse = cursor.fetchone()
    connection.close()

    return nurse


def get_staff():
    return get_nurses()


def get_staff_by_id(staff_record_id):
    return get_nurse_by_id(staff_record_id)


def get_active_staff():
    return get_active_nurses()


def generate_staff_id(staff_type, cursor=None):
    if staff_type not in STAFF_ID_PREFIXES:
        raise ValueError("Invalid staff category.")
    prefix = f"MPH-{STAFF_ID_PREFIXES[staff_type]}-"
    owns_connection = cursor is None
    connection = get_connection() if owns_connection else None
    active_cursor = cursor or connection.cursor()
    active_cursor.execute(
        "SELECT staff_id FROM nurses WHERE staff_id LIKE ?",
        (f"{prefix}%",),
    )
    largest_number = 0
    for (existing_id,) in active_cursor.fetchall():
        try:
            largest_number = max(
                largest_number,
                int(existing_id.rsplit("-", 1)[1]),
            )
        except (IndexError, ValueError):
            continue
    if owns_connection:
        connection.close()
    return f"{prefix}{largest_number + 1:06d}"


def add_staff(
    staff,
    rotation_position=None,
    staff_type="Nurse",
    unit="",
    profile_photo=None,
):
    if not staff.name.strip():
        raise ValueError("Staff name is required.")
    if staff.status not in VALID_NURSE_STATUSES:
        raise ValueError("Invalid staff status.")
    if staff_type not in VALID_STAFF_TYPES:
        raise ValueError("Invalid staff category.")
    if rotation_position is not None and rotation_position not in [0, 1, 2]:
        raise ValueError("Rotation position must be 0, 1, or 2.")

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        staff_id = generate_staff_id(staff_type, cursor)
        staff.staff_id = staff_id
        cursor.execute(
            """
            INSERT INTO nurses (
                name,
                staff_id,
                phone,
                status,
                rotation_position,
                staff_type,
                unit,
                profile_photo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                staff.name.strip(),
                staff_id,
                staff.phone.strip() if staff.phone else "",
                staff.status,
                rotation_position,
                staff_type,
                unit.strip(),
                profile_photo,
            ),
        )
        connection.commit()
    except sqlite3.IntegrityError as error:
        connection.rollback()
        raise ValueError("Could not assign a unique Staff ID.") from error
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return staff_id


def update_nurse(
    nurse_id,
    name,
    staff_id,
    phone,
    status,
    rotation_position,
    staff_type="Nurse",
    unit="",
    profile_photo=None,
    clear_profile_photo=False,
):
    if not name.strip():
        raise ValueError("Nurse name is required.")
    if not staff_id.strip():
        raise ValueError("Staff ID is required.")
    if status not in VALID_NURSE_STATUSES:
        raise ValueError("Invalid nurse status.")
    if staff_type not in VALID_STAFF_TYPES:
        raise ValueError("Invalid staff category.")

    if rotation_position is not None:
        if rotation_position not in [0, 1, 2]:
            raise ValueError("Rotation position must be 0, 1, or 2.")

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE nurses
            SET
                name = ?,
                staff_id = ?,
                phone = ?,
                status = ?,
                rotation_position = ?,
                staff_type = ?,
                unit = ?,
                profile_photo = CASE
                    WHEN ? THEN NULL
                    WHEN ? IS NOT NULL THEN ?
                    ELSE profile_photo
                END
            WHERE id = ?
            """,
            (
                name.strip(),
                staff_id.strip(),
                phone.strip() if phone else "",
                status,
                rotation_position,
                staff_type,
                unit.strip(),
                int(clear_profile_photo),
                profile_photo,
                profile_photo,
                nurse_id,
            ),
        )

        connection.commit()
        updated = cursor.rowcount

    except sqlite3.IntegrityError as error:
        connection.close()
        raise ValueError(
            "A nurse with this Staff ID already exists."
        ) from error

    connection.close()

    return updated


def update_staff(
    staff_record_id,
    name,
    staff_id,
    phone,
    status,
    rotation_position,
    staff_type,
    unit="",
    profile_photo=None,
    clear_profile_photo=False,
):
    return update_nurse(
        staff_record_id,
        name,
        staff_id,
        phone,
        status,
        rotation_position,
        staff_type,
        unit,
        profile_photo,
        clear_profile_photo,
    )


def deactivate_nurse(nurse_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE nurses
        SET status = 'Inactive'
        WHERE id = ?
        """,
        (nurse_id,),
    )
    connection.commit()
    updated = cursor.rowcount
    connection.close()

    return updated


def deactivate_staff(staff_id):
    return deactivate_nurse(staff_id)


def mark_attendance(
    nurse_id,
    attendance_date,
    attendance_time,
    status,
    shift="Legacy",
):
    if status not in VALID_ATTENDANCE_STATUSES:
        raise ValueError("Invalid attendance status.")
    if shift not in VALID_SHIFTS:
        raise ValueError("Invalid attendance shift.")
    try:
        date.fromisoformat(attendance_date)
    except ValueError:
        raise ValueError("Invalid attendance date.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM nurses
        WHERE id = ?
        """,
        (nurse_id,),
    )

    nurse = cursor.fetchone()

    if nurse is None:
        connection.close()
        raise ValueError("The selected nurse does not exist.")

    cursor.execute(
        """
        INSERT INTO attendance (
            nurse_id,
            attendance_date,
            attendance_time,
            status,
            shift
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            nurse_id,
            attendance_date,
            attendance_time,
            status,
            shift,
        ),
    )

    connection.commit()
    connection.close()


def record_sign_out(nurse_id, attendance_date, shift, sign_out_time):
    try:
        date.fromisoformat(attendance_date)
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid attendance date.") from error
    if shift not in {"Morning", "Night"}:
        raise ValueError("Invalid attendance shift.")
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE attendance
        SET sign_out_time = ?
        WHERE nurse_id = ?
          AND attendance_date = ?
          AND shift = ?
          AND sign_out_time IS NULL
        """,
        (sign_out_time, nurse_id, attendance_date, shift),
    )
    updated = cursor.rowcount
    connection.commit()
    connection.close()
    if not updated:
        raise ValueError(
            "No active sign-in was found for this shift, or it was already signed out."
        )


def get_attendance_for_staff_shift(nurse_id, attendance_date, shift):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT id, attendance_time, status, sign_out_time
        FROM attendance
        WHERE nurse_id = ? AND attendance_date = ? AND shift = ?
        """,
        (nurse_id, attendance_date, shift),
    )
    record = cursor.fetchone()
    connection.close()
    return record


def get_attendance_for_date(attendance_date):
    try:
        date.fromisoformat(attendance_date)
    except ValueError:
        raise ValueError("Invalid attendance date.")
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            attendance.id,
            attendance.nurse_id,
            nurses.name,
            nurses.staff_id,
            attendance.attendance_date,
            attendance.attendance_time,
            attendance.status,
            nurses.staff_type,
            attendance.shift,
            attendance.sign_out_time,
            nurses.unit
        FROM attendance
        INNER JOIN nurses
            ON attendance.nurse_id = nurses.id
        WHERE attendance.attendance_date = ?
        ORDER BY nurses.name
        """,
        (attendance_date,),
    )

    attendance = cursor.fetchall()
    connection.close()

    return attendance


def get_attendance_by_date_range(start_date, end_date):
    try:
        date.fromisoformat(start_date)
        date.fromisoformat(end_date)
    except ValueError:
        raise ValueError("Invalid attendance date range.")
    if start_date > end_date:
        raise ValueError("Start date cannot be after the end date.")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            attendance.id,
            attendance.nurse_id,
            nurses.name,
            nurses.staff_id,
            attendance.attendance_date,
            attendance.attendance_time,
            attendance.status,
            nurses.staff_type,
            attendance.shift,
            attendance.sign_out_time,
            nurses.unit
        FROM attendance
        INNER JOIN nurses
            ON attendance.nurse_id = nurses.id
        WHERE attendance.attendance_date BETWEEN ? AND ?
        ORDER BY
            attendance.attendance_date ASC,
            nurses.name ASC
        """,
        (
            start_date,
            end_date,
        ),
    )

    attendance = cursor.fetchall()
    connection.close()

    return attendance


def get_attendance_by_nurse(nurse_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT
        id,
        nurse_id,
        attendance_date,
        attendance_time,
        status
        FROM attendance
        WHERE nurse_id = ?
        ORDER BY attendance_date DESC
        """,
        (nurse_id,),
    )
    attendance = cursor.fetchall()
    connection.close()

    return attendance


def _enable_remote_access():
    from functools import wraps

    from networking.config import is_remote_client
    from networking.transport import remote_call, remote_login

    remote_methods = (
        "get_pending_password_roles",
        "change_password",
        "add_nurse",
        "get_nurses",
        "add_nurse",
        "get_active_nurses",
        "get_nurse_by_id",
        "get_staff",
        "get_staff_by_id",
        "get_active_staff",
        "generate_staff_id",
        "add_staff",
        "update_nurse",
        "update_staff",
        "deactivate_nurse",
        "deactivate_staff",
        "mark_attendance",
        "record_sign_out",
        "get_attendance_for_staff_shift",
        "get_attendance_for_date",
        "get_attendance_by_date_range",
        "get_attendance_by_nurse",
    )

    for function_name in remote_methods:
        local_function = globals()[function_name]

        @wraps(local_function)
        def routed(*args, __name=function_name, __local=local_function, **kwargs):
            if is_remote_client():
                return remote_call(
                    "database.database",
                    __name,
                    args,
                    kwargs,
                )
            return __local(*args, **kwargs)

        globals()[function_name] = routed

    local_authenticate = authenticate

    @wraps(local_authenticate)
    def routed_authenticate(password):
        if is_remote_client():
            return remote_login(password)
        return local_authenticate(password)

    globals()["authenticate"] = routed_authenticate


_enable_remote_access()