from datetime import date, timedelta
from roster.scheduler import (
    generate_roster,
    get_shift_for_day,
)


def test_three_nurse_rotation():
    nurses = [
        (1, "Nurse 1", "NRS001", "", "Active", 0),
        (2, "Nurse 2", "NRS002", "", "Active", 1),
        (3, "Nurse 5", "NRS005", "", "Active", 2),
    ]
    start_date = date(2026, 10, 5)

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
    start_date = date(2026, 10, 5)
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
    start_date = date(2026, 10, 5)
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


if __name__ == "__main__":
    test_three_nurse_rotation()
    test_rotation_repeats_after_six_days()
    test_rotation_patterns()
    print("All scheduler tests passed.")