from datetime import date
from database.database import get_connection

VALID_SHIFTS = [
    "Morning",
    "Night",
    "Off"
]


def create_shift_record(
    nurse_id,
    shift_date,
    original_shift,
    new_shift,
    reason
):
    if not shift_date:
        raise ValueError(
            "Shift date is required."
        )
    try:
        date.fromisoformat(shift_date)
    except ValueError:
        raise ValueError(
            "Invalid shift date."
        )

    if original_shift not in VALID_SHIFTS:
        raise ValueError(
            "Invalid original shift."
        )

    if new_shift not in VALID_SHIFTS:
        raise ValueError(
            "Invalid new shift."
        )

    if original_shift == new_shift:
        raise ValueError(
            "The original and new shifts cannot be the same."
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM nurses
        WHERE id = ?
    """, (
        nurse_id,
    ))

    nurse = cursor.fetchone()

    if nurse is None:
        connection.close()

        raise ValueError(
            "The selected nurse does not exist."
        )

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

    cursor.execute("""
        INSERT INTO shift_records (
            nurse_id,
            shift_date,
            original_shift,
            new_shift,
            reason
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        nurse_id,
        shift_date,
        original_shift,
        new_shift,
        reason
    ))

    connection.commit()

    record_id = cursor.lastrowid

    connection.close()

    return record_id


def get_shift_records(
    start_date=None,
    end_date=None
):
    connection = get_connection()
    cursor = connection.cursor()
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

    if start_date is not None and end_date is not None:

        if start_date > end_date:
            connection.close()

            raise ValueError(
                "Start date cannot be after the end date."
            )

        try:
            date.fromisoformat(start_date)
            date.fromisoformat(end_date)
        except ValueError:
            connection.close()

            raise ValueError(
                "Invalid date range."
            )

        cursor.execute("""
            SELECT
                shift_records.id,
                shift_records.nurse_id,
                nurses.name,
                nurses.staff_id,
                shift_records.shift_date,
                shift_records.original_shift,
                shift_records.new_shift,
                shift_records.reason,
                shift_records.created_at,
                nurses.staff_type
            FROM shift_records
            INNER JOIN nurses
                ON shift_records.nurse_id = nurses.id
            WHERE shift_records.shift_date BETWEEN ? AND ?
            ORDER BY shift_records.shift_date ASC
        """, (
            start_date,
            end_date
        ))

    else:
        cursor.execute("""
            SELECT
                shift_records.id,
                shift_records.nurse_id,
                nurses.name,
                nurses.staff_id,
                shift_records.shift_date,
                shift_records.original_shift,
                shift_records.new_shift,
                shift_records.reason,
                shift_records.created_at,
                nurses.staff_type
            FROM shift_records
            INNER JOIN nurses
                ON shift_records.nurse_id = nurses.id
            ORDER BY shift_records.shift_date ASC
        """)

    records = cursor.fetchall()

    connection.close()

    return records


def update_shift_record(
    record_id,
    shift_date,
    original_shift,
    new_shift,
    reason
):
    if not shift_date:
        raise ValueError(
            "Shift date is required."
        )
    try:
        date.fromisoformat(shift_date)
    except ValueError:
        raise ValueError(
            "Invalid shift date."
        )

    if original_shift not in VALID_SHIFTS:
        raise ValueError(
            "Invalid original shift."
        )

    if new_shift not in VALID_SHIFTS:
        raise ValueError(
            "Invalid new shift."
        )

    if original_shift == new_shift:
        raise ValueError(
            "The original and new shifts cannot be the same."
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE shift_records
        SET
            shift_date = ?,
            original_shift = ?,
            new_shift = ?,
            reason = ?
        WHERE id = ?
    """, (
        shift_date,
        original_shift,
        new_shift,
        reason,
        record_id
    ))

    connection.commit()

    updated = cursor.rowcount

    connection.close()

    return updated


def delete_shift_record(record_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        DELETE FROM shift_records
        WHERE id = ?
    """, (record_id,))

    connection.commit()

    deleted = cursor.rowcount

    connection.close()

    return deleted


def _enable_remote_access():
    from functools import wraps

    from networking.config import is_remote_client
    from networking.transport import remote_call

    for function_name in (
        "create_shift_record",
        "get_shift_records",
        "update_shift_record",
        "delete_shift_record",
    ):
        local_function = globals()[function_name]

        @wraps(local_function)
        def routed(*args, __name=function_name, __local=local_function, **kwargs):
            if is_remote_client():
                return remote_call("records.shift_records", __name, args, kwargs)
            return __local(*args, **kwargs)

        globals()[function_name] = routed


_enable_remote_access()