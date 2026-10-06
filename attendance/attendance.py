from datetime import date, datetime, time, timedelta
from database.database import (
    get_active_nurses,
    get_attendance_for_date,
    mark_attendance,
)
from roster.scheduler import generate_roster

MORNING_START = time(7, 0)
MORNING_END = time(19, 0)
NIGHT_START = time(19, 0)
NIGHT_END = time(7, 0)


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


def is_within_shift(shift, current_time):
    if shift == "Morning":
        return MORNING_START <= current_time < MORNING_END
    if shift == "Night":
        return current_time >= NIGHT_START or current_time < NIGHT_END

    return False


def get_duty_information(nurse):
    current_date = get_today()
    current_time = datetime.now().time()
    shift_date = get_shift_date(current_date, current_time)

    shift = get_nurse_shift(nurse, shift_date)

    return shift_date, shift, current_time


def check_in_nurse(staff_id):
    if not isinstance(staff_id, str):
        return {"success": False, "message": "Staff ID must be text."}
    staff_id = staff_id.strip()

    if not staff_id:
        return {"success": False, "message": "Please enter a Staff ID."}

    nurse = find_nurse_by_staff_id(staff_id)

    if nurse is None:
        return {"success": False, "message": "Staff ID not found."}

    shift_date, shift, current_time = get_duty_information(nurse)

    if shift == "Off":
        return {
            "success": False,
            "message": f"{nurse[1]} is scheduled OFF for this duty period.",
            "nurse": nurse,
            "shift": shift,
            "shift_date": shift_date.isoformat(),
        }

    if not is_within_shift(shift, current_time):
        if shift == "Morning":
            duty_time = "7:00 AM - 7:00 PM"
        else:
            duty_time = "7:00 PM - 7:00 AM"

        return {
            "success": False,
            "message": (
                f"{nurse[1]} is scheduled for the {shift} shift, but it is currently "
                f"outside their duty hours.\n\nShift hours: {duty_time}"
            ),
            "nurse": nurse,
            "shift": shift,
            "shift_date": shift_date.isoformat(),
        }

    existing_attendance = get_attendance_for_date(shift_date.isoformat())

    for record in existing_attendance:
        if record[1] == nurse[0]:
            return {
                "success": False,
                "message": f"{nurse[1]} has already checked in for this shift.",
                "nurse": nurse,
                "shift": shift,
                "shift_date": shift_date.isoformat(),
                "time": record[5],
            }

    attendance_time = datetime.now().strftime("%H:%M:%S")

    mark_attendance(
        nurse_id=nurse[0],
        attendance_date=shift_date.isoformat(),
        attendance_time=attendance_time,
        status="Present",
    )

    return {
        "success": True,
        "message": "Attendance recorded successfully.",
        "nurse": nurse,
        "shift": shift,
        "shift_date": shift_date.isoformat(),
        "time": attendance_time,
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