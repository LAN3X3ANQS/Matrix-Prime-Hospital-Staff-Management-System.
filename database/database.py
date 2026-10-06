import sqlite3
from datetime import date
from pathlib import Path

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


def get_connection():
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nurses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            staff_id TEXT UNIQUE NOT NULL,
            phone TEXT,
            status TEXT NOT NULL DEFAULT 'Active',
            rotation_position INTEGER
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
            UNIQUE(nurse_id, attendance_date),
            FOREIGN KEY(nurse_id) REFERENCES nurses(id)
        )
    """)

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


def add_nurse(nurse, rotation_position=None):
    if not nurse.name.strip():
        raise ValueError("Nurse name is required.")
    if not nurse.staff_id.strip():
        raise ValueError("Staff ID is required.")

    if nurse.status not in VALID_NURSE_STATUSES:
        raise ValueError("Invalid nurse status.")

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
                rotation_position
            )
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                nurse.name.strip(),
                nurse.staff_id.strip(),
                nurse.phone.strip() if nurse.phone else "",
                nurse.status,
                rotation_position,
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
            rotation_position
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
            rotation_position
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
            rotation_position
        FROM nurses
        WHERE id = ?
    """,
        (nurse_id,),
    )

    nurse = cursor.fetchone()
    connection.close()

    return nurse


def update_nurse(
    nurse_id,
    name,
    staff_id,
    phone,
    status,
    rotation_position,
):
    if not name.strip():
        raise ValueError("Nurse name is required.")
    if not staff_id.strip():
        raise ValueError("Staff ID is required.")

    if status not in VALID_NURSE_STATUSES:
        raise ValueError("Invalid nurse status.")

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
                rotation_position = ?
            WHERE id = ?
        """,
            (
                name.strip(),
                staff_id.strip(),
                phone.strip() if phone else "",
                status,
                rotation_position,
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


def mark_attendance(
    nurse_id,
    attendance_date,
    attendance_time,
    status,
):
    if status not in VALID_ATTENDANCE_STATUSES:
        raise ValueError("Invalid attendance status.")
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
            status
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(nurse_id, attendance_date)
        DO UPDATE SET
            attendance_time = excluded.attendance_time,
            status = excluded.status
    """,
        (
            nurse_id,
            attendance_date,
            attendance_time,
            status,
        ),
    )

    connection.commit()
    connection.close()


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
            attendance.status
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
            attendance.status
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