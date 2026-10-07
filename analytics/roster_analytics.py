from database.database import get_active_nurses
from roster.scheduler import generate_roster


def get_roster_summary(start_date, end_date):

    if start_date > end_date:
        raise ValueError(
            "Start date cannot be after end date."
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

    shift_counts = {
        "Morning": 0,
        "Night": 0,
        "Off": 0
    }

    nurse_summaries = []

    for nurse in nurses:
        nurse_summaries.append({
            "nurse_id": nurse[0],
            "name": nurse[1],
            "staff_id": nurse[2],
            "staff_type": nurse[6],
            "morning": 0,
            "night": 0,
            "off": 0
        })

    nurse_summary_lookup = {
        summary["nurse_id"]: summary
        for summary in nurse_summaries
    }

    for day_roster in roster:
        for nurse_entry in day_roster["nurses"]:
            nurse = nurse_entry["nurse"]
            shift = nurse_entry["shift"]

            nurse_id = nurse[0]

            shift_counts[shift] += 1

            nurse_summary = nurse_summary_lookup[nurse_id]

            if shift == "Morning":
                nurse_summary["morning"] += 1

            elif shift == "Night":
                nurse_summary["night"] += 1

            elif shift == "Off":
                nurse_summary["off"] += 1

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_nurses": len(nurses),
        "total_staff": len(nurses),
        "total_days": number_of_days,
        "total_shifts": (
            shift_counts["Morning"]
            + shift_counts["Night"]
        ),
        "morning_shifts": shift_counts["Morning"],
        "night_shifts": shift_counts["Night"],
        "off_days": shift_counts["Off"],
        "nurses": nurse_summaries
    }