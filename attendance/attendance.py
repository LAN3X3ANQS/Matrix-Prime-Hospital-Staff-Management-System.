from datetime import date, datetime, time, timedelta
import sqlite3
from database.database import (
    get_active_nurses,
    get_attendance_for_staff_shift,
    get_attendance_for_date,
    mark_attendance,
    record_sign_out,
)
from roster.scheduler import generate_roster

MORNING_START = time(8, 0)
MORNING_END = time(19, 0)
DAILY_STAFF_END = time(18, 0)
NIGHT_START = time(19, 0)
NIGHT_END = time(7, 0)
SIGN_OUT_GRACE_MINUTES = 30
DAILY_DAY_STAFF_TYPES = {"Janitor", "Admin", "Lab Tech", "Front Desk"}


def get_today():
    return date.today()


def find_nurse_by_staff_id(staff_id):
    if not staff_id:
        return None
    nurses = get_active_nurses()

    for nurse in nurses:
        if nurse[2].lower() == staff_id.strip().lower():
            return nurse

    return None


def find_staff_by_staff_id(staff_id):
    return find_nurse_by_staff_id(staff_id)


def get_nurse_shift(nurse, roster_date):
    roster = generate_roster([nurse], roster_date, 1)
    return roster[0]["nurses"][0]["shift"]


def get_shift_date(current_date, current_time):
    """Determine which roster date owns the current duty period.

    00:00 - 06:59 belongs to the previous day's Night shift. 07:00 - 18:59 belongs
    to the current day's Morning shift. 19:00 - 23:59 belongs to the current
    day's Night shift.
    """
    if current_time < NIGHT_END:
        return current_date - timedelta(days=1)

    return current_date


def is_within_shift(shift, current_time, staff_type=None):
    if shift == "Morning":
        shift_end = (
            DAILY_STAFF_END
            if staff_type in DAILY_DAY_STAFF_TYPES
            else MORNING_END
        )
        return MORNING_START <= current_time < shift_end
    if shift == "Night":
        return current_time >= NIGHT_START or current_time < NIGHT_END

    return False


def get_duty_information(nurse):
    current_date = get_today()
    current_time = datetime.now().time()
    shift_date = get_shift_date(current_date, current_time)

    shift = get_nurse_shift(nurse, shift_date)

    return shift_date, shift, current_time


LATE_GRACE_MINUTES = 10


def check_in_nurse(staff_id, now=None):
    if not isinstance(staff_id, str):
        return {"success": False, "message": "Staff ID must be text."}
    staff_id = staff_id.strip()

    if not staff_id:
        return {"success": False, "message": "Please enter a Staff ID."}

    nurse = find_nurse_by_staff_id(staff_id)

    if nurse is None:
        return {
            "success": False,
            "message": "Staff ID not found in the active staff directory.",
        }

    now = now or datetime.now()
    shift_date = get_shift_date(now.date(), now.time())
    shift = get_nurse_shift(nurse, shift_date)

    if shift == "Off":
        return {
            "success": False,
            "message": f"{nurse[1]} is scheduled OFF for this duty period.",
            "nurse": nurse,
            "staff": nurse,
            "shift": shift,
            "shift_date": shift_date.isoformat(),
        }

    if not is_within_shift(shift, now.time(), nurse[6]):
        if shift == "Morning":
            end_time = (
                DAILY_STAFF_END
                if nurse[6] in DAILY_DAY_STAFF_TYPES
                else MORNING_END
            )
            formatted_end = end_time.strftime("%I:%M %p").lstrip("0")
            duty_time = f"7:00 AM - {formatted_end}"
        else:
            duty_time = "7:00 PM - 7:00 AM"

        return {
            "success": False,
            "message": (
                f"{nurse[1]} is scheduled for the {shift} shift, but it is currently "
                f"outside their duty hours.\n\nShift hours: {duty_time}"
            ),
            "nurse": nurse,
            "staff": nurse,
            "shift": shift,
            "shift_date": shift_date.isoformat(),
        }

    existing = get_attendance_for_staff_shift(
        nurse[0],
        shift_date.isoformat(),
        shift,
    )
    if existing is not None:
        if existing[3] is None:
            message = (
                f"{nurse[1]} is already signed in for this {shift} shift."
            )
        else:
            message = (
                f"{nurse[1]} has already completed this {shift} shift."
            )
        return {
            "success": False,
            "message": message,
            "nurse": nurse,
            "staff": nurse,
            "shift": shift,
            "shift_date": shift_date.isoformat(),
            "time": existing[1],
        }

    attendance_time = now.strftime("%H:%M:%S")
    shift_start = MORNING_START if shift == "Morning" else NIGHT_START
    shift_start_at = datetime.combine(shift_date, shift_start)
    late_after = shift_start_at + timedelta(minutes=LATE_GRACE_MINUTES)
    status = "Late" if now > late_after else "Present"

    try:
        mark_attendance(
            nurse_id=nurse[0],
            attendance_date=shift_date.isoformat(),
            attendance_time=attendance_time,
            status=status,
            shift=shift,
        )
    except sqlite3.IntegrityError:
        return {
            "success": False,
            "message": f"{nurse[1]} is already signed in for this shift.",
            "nurse": nurse,
            "staff": nurse,
            "shift": shift,
            "shift_date": shift_date.isoformat(),
        }

    return {
        "success": True,
        "message": (
            "Late check-in recorded."
            if status == "Late"
            else "On-time check-in recorded."
        ),
        "nurse": nurse,
        "staff": nurse,
        "shift": shift,
        "shift_date": shift_date.isoformat(),
        "time": attendance_time,
        "status": status,
    }


def check_out_nurse(staff_id, now=None):
    if not isinstance(staff_id, str):
        return {"success": False, "message": "Staff ID must be text."}
    staff_id = staff_id.strip()
    if not staff_id:
        return {"success": False, "message": "Please enter a Staff ID."}

    staff = find_staff_by_staff_id(staff_id)
    if staff is None:
        return {
            "success": False,
            "message": "Staff ID not found in the active staff directory.",
        }

    now = now or datetime.now()
    open_shifts = []
    for attendance_date in (now.date(), now.date() - timedelta(days=1)):
        date_text = attendance_date.isoformat()
        for shift in ("Morning", "Night"):
            record = get_attendance_for_staff_shift(
                staff[0],
                date_text,
                shift,
            )
            if record is not None and record[3] is None:
                signed_in_at = datetime.combine(
                    attendance_date,
                    datetime.strptime(record[1], "%H:%M:%S").time(),
                )
                staff_type = staff[6]
                if shift == "Night":
                    shift_ends_at = datetime.combine(
                        attendance_date + timedelta(days=1),
                        NIGHT_END,
                    )
                else:
                    shift_end = (
                        DAILY_STAFF_END
                        if staff_type in DAILY_DAY_STAFF_TYPES
                        else MORNING_END
                    )
                    shift_ends_at = datetime.combine(
                        attendance_date,
                        shift_end,
                    )
                sign_out_deadline = shift_ends_at + timedelta(
                    minutes=SIGN_OUT_GRACE_MINUTES
                )
                if signed_in_at <= now <= sign_out_deadline:
                    open_shifts.append(
                        (
                            signed_in_at,
                            date_text,
                            shift,
                            record,
                            shift_ends_at,
                        )
                    )

    if not open_shifts:
        return {
            "success": False,
            "message": "No active shift sign-in was found to sign out.",
            "staff": staff,
        }

    _, attendance_date, shift, record, shift_ends_at = max(
        open_shifts,
        key=lambda item: item[0],
    )
    sign_out_time = now.strftime("%H:%M:%S")
    sign_out_status = "Early" if now < shift_ends_at else "On time"
    try:
        record_sign_out(
            staff[0],
            attendance_date,
            shift,
            sign_out_time,
            sign_out_status,
        )
    except ValueError as error:
        return {
            "success": False,
            "message": str(error),
            "staff": staff,
        }

    return {
        "success": True,
        "message": (
            f"Early sign-out recorded for the {shift} shift."
            if sign_out_status == "Early"
            else f"Sign-out recorded for the {shift} shift."
        ),
        "staff": staff,
        "shift": shift,
        "shift_date": attendance_date,
        "time": sign_out_time,
        "sign_in_time": record[1],
        "status": sign_out_status,
        "scheduled_end": shift_ends_at.strftime("%H:%M:%S"),
    }


def get_daily_attendance(attendance_date):
    if isinstance(attendance_date, date):
        attendance_date = attendance_date.isoformat()
    if not isinstance(attendance_date, str):
        raise ValueError("Attendance date must be a date or date string.")

    try:
        date.fromisoformat(attendance_date)
    except ValueError:
        raise ValueError("Invalid attendance date.")

    return get_attendance_for_date(attendance_date)