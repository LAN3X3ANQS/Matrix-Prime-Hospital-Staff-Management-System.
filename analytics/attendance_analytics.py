from datetime import date, timedelta

from database.database import (
    get_active_nurses,
    get_attendance_by_date_range
)

from records.leave_records import (
    get_leave_records
)

from roster.scheduler import generate_roster


def date_from_string(value):
    return date.fromisoformat(
        value
    )


def get_attendance_summary(
    start_date,
    end_date
):
    if start_date > end_date:
        raise ValueError(
            "Start date cannot be after the end date."
        )

    nurses = get_active_nurses()

    number_of_days = (
        end_date - start_date
    ).days + 1

    roster = generate_roster(
        nurses,
        start_date,
        number_of_days
    )

    attendance = get_attendance_by_date_range(
        start_date.isoformat(),
        end_date.isoformat()
    )

    leave_records = get_leave_records(
        start_date.isoformat(),
        end_date.isoformat()
    )

    scheduled_shifts = 0
    present = 0
    approved_leave = 0

    scheduled_by_nurse = {}
    present_by_nurse = {}
    leave_by_nurse = {}

    for nurse in nurses:
        nurse_id = nurse[0]

        scheduled_by_nurse[nurse_id] = 0
        present_by_nurse[nurse_id] = 0
        leave_by_nurse[nurse_id] = 0

    approved_leave_dates = {}

    for record in leave_records:
        nurse_id = record[1]

        leave_start = date_from_string(
            record[4]
        )

        leave_end = date_from_string(
            record[5]
        )

        status = record[7]

        if status != "Approved":
            continue

        if nurse_id not in approved_leave_dates:
            approved_leave_dates[nurse_id] = set()

        current_date = leave_start

        while current_date <= leave_end:

            if start_date <= current_date <= end_date:
                approved_leave_dates[nurse_id].add(
                    current_date
                )

            current_date += timedelta(
                days=1
            )

    for day_roster in roster:
        roster_date = day_roster["date"]

        for nurse_entry in day_roster["nurses"]:
            nurse = nurse_entry["nurse"]
            shift = nurse_entry["shift"]

            nurse_id = nurse[0]

            if shift == "Off":
                continue

            scheduled_shifts += 1
            scheduled_by_nurse[nurse_id] += 1

            if (
                roster_date
                in approved_leave_dates.get(
                    nurse_id,
                    set()
                )
            ):
                approved_leave += 1
                leave_by_nurse[nurse_id] += 1

    for record in attendance:
        nurse_id = record[1]
        status = record[6]

        if nurse_id not in present_by_nurse:
            continue

        if status == "Present":
            present += 1
            present_by_nurse[nurse_id] += 1

    absent = (
        scheduled_shifts
        - present
        - approved_leave
    )

    effective_scheduled = (
        scheduled_shifts
        - approved_leave
    )

    if effective_scheduled > 0:
        attendance_rate = (
            present
            / effective_scheduled
            * 100
        )
    else:
        attendance_rate = 0

    nurse_summaries = []

    for nurse in nurses:
        nurse_id = nurse[0]

        scheduled = scheduled_by_nurse[nurse_id]
        nurse_present = present_by_nurse[nurse_id]
        nurse_leave = leave_by_nurse[nurse_id]

        nurse_absent = (
            scheduled
            - nurse_present
            - nurse_leave
        )

        nurse_effective_scheduled = (
            scheduled
            - nurse_leave
        )

        if nurse_effective_scheduled > 0:
            nurse_rate = (
                nurse_present
                / nurse_effective_scheduled
                * 100
            )
        else:
            nurse_rate = 0

        nurse_summaries.append({
            "nurse_id": nurse_id,
            "name": nurse[1],
            "staff_id": nurse[2],
            "staff_type": nurse[6],
            "scheduled_shifts": scheduled,
            "present": nurse_present,
            "absent": nurse_absent,
            "approved_leave": nurse_leave,
            "attendance_rate": nurse_rate
        })

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_nurses": len(nurses),
        "total_staff": len(nurses),
        "scheduled_shifts": scheduled_shifts,
        "present": present,
        "absent": absent,
        "approved_leave": approved_leave,
        "attendance_rate": attendance_rate,
        "nurses": nurse_summaries
    }


def get_staff_attendance_score(staff_record_id, as_of=None):
    as_of = as_of or date.today()
    start_date = as_of - timedelta(days=29)
    staff = next(
        (
            person
            for person in get_active_nurses()
            if person[0] == staff_record_id
        ),
        None,
    )
    if staff is None:
        raise ValueError("The selected staff member is not active.")

    scheduled_days = (
        (as_of - start_date).days + 1
    )
    roster = generate_roster(
        [staff],
        start_date,
        scheduled_days,
    )
    scheduled_shifts = {
        day["date"]: day["nurses"][0]["shift"]
        for day in roster
        if day["nurses"][0]["shift"] != "Off"
    }
    leave_records = get_leave_records(
        start_date.isoformat(),
        as_of.isoformat(),
    )
    approved_leave_dates = set()
    for record in leave_records:
        if record[1] != staff_record_id or record[7] != "Approved":
            continue
        leave_date = date.fromisoformat(record[4])
        leave_end = date.fromisoformat(record[5])
        while leave_date <= leave_end:
            if start_date <= leave_date <= as_of:
                approved_leave_dates.add(leave_date)
            leave_date += timedelta(days=1)

    approved_leave_shifts = len(
        set(scheduled_shifts).intersection(approved_leave_dates)
    )
    scheduled_dates = set(scheduled_shifts)
    scheduled_dates.difference_update(approved_leave_dates)
    attendance = get_attendance_by_date_range(
        start_date.isoformat(),
        as_of.isoformat(),
    )
    staff_records = [
        record
        for record in attendance
        if record[1] == staff_record_id
        and date.fromisoformat(record[4]) in scheduled_shifts
        and record[8] == scheduled_shifts[date.fromisoformat(record[4])]
    ]
    on_time = sum(record[6] == "Present" for record in staff_records)
    late = sum(record[6] == "Late" for record in staff_records)
    completed_sign_outs = sum(record[9] is not None for record in staff_records)
    eligible_shifts = len(scheduled_dates)
    score = (
        round(on_time / eligible_shifts * 100)
        if eligible_shifts
        else None
    )
    return {
        "score": score,
        "period_start": start_date,
        "period_end": as_of,
        "scheduled_shifts": eligible_shifts,
        "on_time_check_ins": on_time,
        "late_check_ins": late,
        "absent_shifts": max(
            eligible_shifts - on_time - late,
            0,
        ),
        "completed_sign_outs": completed_sign_outs,
        "approved_leave_shifts": approved_leave_shifts,
        "is_consistent": score is not None and score >= 90,
    }