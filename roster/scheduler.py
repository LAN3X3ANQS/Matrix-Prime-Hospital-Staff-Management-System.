from datetime import date, timedelta


ROTATION = [
    "Morning",
    "Morning",
    "Night",
    "Night",
    "Off",
    "Off"
]

ROTATION_ANCHOR = date(2026, 10, 5)


def get_shift_for_day(rotation_start, day):
    days_since_start = (day - rotation_start).days

    rotation_position = days_since_start % len(ROTATION)

    return ROTATION[rotation_position]


def generate_roster(nurses, start_date, number_of_days):
    roster = []

    for day_number in range(number_of_days):
        current_date = start_date + timedelta(days=day_number)

        day_roster = {
            "date": current_date,
            "nurses": []
        }

        for nurse in nurses:
            rotation_position = nurse[5]

            if rotation_position is None:
                rotation_position = 0

            nurse_start_date = (
                ROTATION_ANCHOR
                - timedelta(days=rotation_position * 2)
            )

            shift = get_shift_for_day(
                nurse_start_date,
                current_date
            )

            day_roster["nurses"].append({
                "nurse": nurse,
                "shift": shift
            })

        roster.append(day_roster)

    return roster