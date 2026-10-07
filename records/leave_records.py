from datetime import date
from database.database import get_connection

VALID_LEAVE_STATUSES = [
    "Approved",
    "Pending",
    "Rejected",
]


def create_leave_record(
    nurse_id,
    start_date,
    end_date,
    reason,
    status="Approved",
):
    if start_date > end_date:
        raise ValueError(
            "Start date cannot be after the end date."
        )
    try:
        date.fromisoformat(start_date)
        date.fromisoformat(end_date)
    except ValueError:
        raise ValueError(
            "Invalid leave date."
        )

    if status not in VALID_LEAVE_STATUSES:
        raise ValueError(
            "Invalid leave status."
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
        INSERT INTO leave_records (
            nurse_id,
            start_date,
            end_date,
            reason,
            status
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        nurse_id,
        start_date,
        end_date,
        reason,
        status,
    ))

    connection.commit()

    record_id = cursor.lastrowid

    connection.close()

    return record_id


def get_leave_records(
    start_date=None,
    end_date=None,
):
    connection = get_connection()
    cursor = connection.cursor()
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
                "Invalid leave date range."
            )

        cursor.execute("""
            SELECT
                leave_records.id,
                leave_records.nurse_id,
                nurses.name,
                nurses.staff_id,
                leave_records.start_date,
                leave_records.end_date,
                leave_records.reason,
                leave_records.status,
                nurses.staff_type
            FROM leave_records
            INNER JOIN nurses
                ON leave_records.nurse_id = nurses.id
            WHERE leave_records.end_date >= ?
              AND leave_records.start_date <= ?
            ORDER BY leave_records.start_date ASC
        """, (
            start_date,
            end_date,
        ))

    else:
        cursor.execute("""
            SELECT
                leave_records.id,
                leave_records.nurse_id,
                nurses.name,
                nurses.staff_id,
                leave_records.start_date,
                leave_records.end_date,
                leave_records.reason,
                leave_records.status,
                nurses.staff_type
            FROM leave_records
            INNER JOIN nurses
                ON leave_records.nurse_id = nurses.id
            ORDER BY leave_records.start_date ASC
        """)

    records = cursor.fetchall()

    connection.close()

    return records


def update_leave_record(
    record_id,
    start_date,
    end_date,
    reason,
    status,
):
    if start_date > end_date:
        raise ValueError(
            "Start date cannot be after the end date."
        )
    try:
        date.fromisoformat(start_date)
        date.fromisoformat(end_date)
    except ValueError:
        raise ValueError(
            "Invalid leave date."
        )

    if status not in VALID_LEAVE_STATUSES:
        raise ValueError(
            "Invalid leave status."
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE leave_records
        SET
            start_date = ?,
            end_date = ?,
            reason = ?,
            status = ?
        WHERE id = ?
    """, (
        start_date,
        end_date,
        reason,
        status,
        record_id,
    ))

    connection.commit()

    updated = cursor.rowcount

    connection.close()

    return updated


def delete_leave_record(record_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        DELETE FROM leave_records
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
        "create_leave_record",
        "get_leave_records",
        "update_leave_record",
        "delete_leave_record",
    ):
        local_function = globals()[function_name]

        @wraps(local_function)
        def routed(*args, __name=function_name, __local=local_function, **kwargs):
            if is_remote_client():
                return remote_call("records.leave_records", __name, args, kwargs)
            return __local(*args, **kwargs)

        globals()[function_name] = routed


_enable_remote_access()