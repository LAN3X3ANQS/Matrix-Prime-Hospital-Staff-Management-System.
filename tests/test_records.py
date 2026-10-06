from datetime import date
from database.database import (
    get_connection,
    initialize_database,
)
from records.leave_records import (
    create_leave_record,
    update_leave_record,
)
from records.shift_records import (
    create_shift_record,
    update_shift_record,
)


def get_test_nurse_id():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id
        FROM nurses
        LIMIT 1
    """)

    nurse = cursor.fetchone()
    connection.close()

    if nurse is None:
        raise AssertionError(
            "No nurse exists in the database."
        )

    return nurse[0]


def test_leave_date_validation():
    nurse_id = get_test_nurse_id()
    try:
        create_leave_record(
            nurse_id=nurse_id,
            start_date="2026-10-10",
            end_date="2026-10-05",
            reason="Test",
            status="Approved",
        )
    except ValueError:
        return

    raise AssertionError(
        "Invalid leave date range was accepted."
    )


def test_leave_status_validation():
    nurse_id = get_test_nurse_id()
    try:
        create_leave_record(
            nurse_id=nurse_id,
            start_date="2026-10-05",
            end_date="2026-10-06",
            reason="Test",
            status="Invalid",
        )
    except ValueError:
        return

    raise AssertionError(
        "Invalid leave status was accepted."
    )


def test_shift_validation():
    nurse_id = get_test_nurse_id()
    try:
        create_shift_record(
            nurse_id=nurse_id,
            shift_date="2026-10-05",
            original_shift="Morning",
            new_shift="Morning",
            reason="Test",
        )
    except ValueError:
        return

    raise AssertionError(
        "A shift change with identical shifts was accepted."
    )


def test_shift_name_validation():
    nurse_id = get_test_nurse_id()
    try:
        create_shift_record(
            nurse_id=nurse_id,
            shift_date="2026-10-05",
            original_shift="Invalid",
            new_shift="Night",
            reason="Test",
        )
    except ValueError:
        return

    raise AssertionError(
        "Invalid original shift was accepted."
    )


def test_leave_update_validation():
    nurse_id = get_test_nurse_id()
    record_id = create_leave_record(
        nurse_id=nurse_id,
        start_date="2026-10-05",
        end_date="2026-10-06",
        reason="Test record",
        status="Pending",
    )

    try:
        update_leave_record(
            record_id=record_id,
            start_date="2026-10-10",
            end_date="2026-10-05",
            reason="Test record",
            status="Pending",
        )
    except ValueError:
        return

    raise AssertionError(
        "Invalid leave update was accepted."
    )


def test_shift_update_validation():
    nurse_id = get_test_nurse_id()
    record_id = create_shift_record(
        nurse_id=nurse_id,
        shift_date="2026-10-05",
        original_shift="Morning",
        new_shift="Night",
        reason="Test record",
    )

    try:
        update_shift_record(
            record_id=record_id,
            shift_date="2026-10-05",
            original_shift="Night",
            new_shift="Night",
            reason="Test record",
        )
    except ValueError:
        return

    raise AssertionError(
        "Invalid shift update was accepted."
    )


if __name__ == "__main__":
    initialize_database()
    test_leave_date_validation()
    test_leave_status_validation()
    test_shift_validation()
    test_shift_name_validation()
    test_leave_update_validation()
    test_shift_update_validation()

    print("All record validation tests passed.")