from datetime import date, timedelta
from roster.scheduler import (
    ROTATION_ANCHOR,
    generate_roster,
    get_shift_for_day,
)


def test_three_nurse_rotation():
    nurses = [
        (1, "Nurse 1", "NRS001", "", "Active", 0),
        (2, "Nurse 2", "NRS002", "", "Active", 1),
        (3, "Nurse 5", "NRS005", "", "Active", 2),
    ]
    start_date = ROTATION_ANCHOR

    roster = generate_roster(
        nurses,
        start_date,
        6,
    )

    expected_shifts = [
        ["Morning", "Night", "Off"],
        ["Morning", "Night", "Off"],
        ["Night", "Off", "Morning"],
        ["Night", "Off", "Morning"],
        ["Off", "Morning", "Night"],
        ["Off", "Morning", "Night"],
    ]

    for day_index, expected in enumerate(expected_shifts):
        actual = [
            entry["shift"]
            for entry in roster[day_index]["nurses"]
        ]

        assert actual == expected


def test_rotation_repeats_after_six_days():
    start_date = ROTATION_ANCHOR
    shifts = []

    for day_offset in range(12):
        current_date = (
            start_date
            + timedelta(days=day_offset)
        )

        shifts.append(
            get_shift_for_day(
                start_date,
                current_date,
            )
        )

    assert shifts[:6] == shifts[6:]


def test_rotation_patterns():
    start_date = ROTATION_ANCHOR
    expected = [
        "Morning",
        "Morning",
        "Night",
        "Night",
        "Off",
        "Off",
    ]

    for day_offset, expected_shift in enumerate(expected):
        current_date = (
            start_date
            + timedelta(days=day_offset)
        )

        actual_shift = get_shift_for_day(
            start_date,
            current_date,
        )

        assert actual_shift == expected_shift


def test_roster_shift_is_independent_of_requested_range():
    staff = (1, "Staff 1", "MPH-NUR-000001", "", "Active", 0)
    target_date = ROTATION_ANCHOR + timedelta(days=4)
    full_range = generate_roster([staff], ROTATION_ANCHOR, 10)
    single_day = generate_roster([staff], target_date, 1)
    expected = next(
        day["nurses"][0]["shift"]
        for day in full_range
        if day["date"] == target_date
    )
    assert single_day[0]["nurses"][0]["shift"] == expected


def test_daily_day_staff_do_not_rotate_or_get_days_off():
    staff = [
        (index, category, f"MPH-{category[:3].upper()}-260001", "",
         "Active", None, category, "", None)
        for index, category in enumerate(
            ["Janitor", "Admin", "Lab Tech", "Front Desk"],
            start=1,
        )
    ]
    roster = generate_roster(staff, ROTATION_ANCHOR, 12)
    assert all(
        entry["shift"] == "Morning"
        for day in roster
        for entry in day["nurses"]
    )


if __name__ == "__main__":
    test_three_nurse_rotation()
    test_rotation_repeats_after_six_days()
    test_rotation_patterns()
    test_roster_shift_is_independent_of_requested_range()
    test_daily_day_staff_do_not_rotate_or_get_days_off()
    print("All scheduler tests passed.")