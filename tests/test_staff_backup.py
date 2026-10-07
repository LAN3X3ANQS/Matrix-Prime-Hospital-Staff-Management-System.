import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database.backups as backups
import database.database as database
from attendance.attendance import check_in_nurse, check_out_nurse
from database.models import Nurse
from records.leave_records import create_leave_record, get_leave_records
from records.shift_records import create_shift_record, get_shift_records
from datetime import date, datetime, timedelta
import analytics.attendance_analytics as attendance_analytics


class StaffAndBackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.database_path = root / "data" / "nurse_roster.db"
        self.database_patch = patch.object(
            database,
            "DATABASE_PATH",
            self.database_path,
        )
        self.database_patch.start()
        self.backup_path_patch = patch.object(
            backups,
            "DATABASE_PATH",
            self.database_path,
        )
        self.backup_path_patch.start()
        self.environment_patch = patch.dict(os.environ, {}, clear=True)
        self.environment_patch.start()
        database.initialize_database()

    def tearDown(self):
        self.environment_patch.stop()
        self.backup_path_patch.stop()
        self.database_patch.stop()
        self.temporary_directory.cleanup()

    def test_staff_categories_are_saved_and_returned(self):
        janitor = Nurse(None, "Jamie Janitor", "JAN001", "")
        lab_tech = Nurse(None, "Taylor Lab", "LAB001", "")
        admin = Nurse(None, "Alex Admin", "ADM001", "")

        database.add_staff(janitor, rotation_position=0, staff_type="Janitor")
        database.add_staff(lab_tech, rotation_position=1, staff_type="Lab Tech")
        database.add_staff(admin, rotation_position=2, staff_type="Admin")

        staff = database.get_staff()
        self.assertEqual(
            {record[6] for record in staff},
            {"Admin", "Janitor", "Lab Tech"},
        )
        self.assertEqual(len({record[2] for record in staff}), 3)
        self.assertEqual(
            {record[2].split("-")[1] for record in staff},
            {"ADM", "JAN", "LAB"},
        )

        with self.assertRaisesRegex(ValueError, "staff category"):
            database.add_staff(
                Nurse(None, "Unknown Worker", "UNK001", ""),
                staff_type="Unknown",
            )

    def test_category_is_preserved_in_attendance_leave_and_shift_records(self):
        lab_tech = Nurse(None, "Taylor Lab", "LAB777", "")
        database.add_staff(lab_tech, rotation_position=1, staff_type="Lab Tech")
        staff_record_id = database.get_staff()[0][0]

        database.mark_attendance(
            staff_record_id,
            "2026-10-07",
            "09:00:00",
            "Present",
        )
        attendance = database.get_attendance_by_date_range(
            "2026-10-07",
            "2026-10-07",
        )
        self.assertEqual(attendance[0][7], "Lab Tech")

        create_leave_record(
            staff_record_id,
            "2026-10-08",
            "2026-10-09",
            "Test",
            "Pending",
        )
        leave = get_leave_records("2026-10-08", "2026-10-09")
        self.assertEqual(leave[0][8], "Lab Tech")

        create_shift_record(
            staff_record_id,
            "2026-10-08",
            "Morning",
            "Night",
            "Test",
        )
        shift = get_shift_records("2026-10-08", "2026-10-08")
        self.assertEqual(shift[0][9], "Lab Tech")

    def test_existing_nurse_schema_migrates_without_losing_records(self):
        legacy_path = Path(self.temporary_directory.name) / "legacy.sqlite3"
        with sqlite3.connect(legacy_path) as connection:
            connection.execute("""
                CREATE TABLE nurses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    staff_id TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    rotation_position INTEGER
                )
            """)
            connection.execute("""
                CREATE TABLE attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nurse_id INTEGER NOT NULL,
                    attendance_date TEXT NOT NULL,
                    attendance_time TEXT,
                    status TEXT NOT NULL,
                    UNIQUE(nurse_id, attendance_date),
                    FOREIGN KEY(nurse_id) REFERENCES nurses(id)
                )
            """)
            connection.execute(
                "INSERT INTO nurses (name, staff_id) VALUES (?, ?)",
                ("Morgan Nurse", "NRS009"),
            )
            connection.execute(
                """
                INSERT INTO attendance (
                    nurse_id, attendance_date, attendance_time, status
                )
                VALUES (1, '2026-10-01', '07:05:00', 'Present')
                """
            )
        connection.close()
        with patch.object(database, "DATABASE_PATH", legacy_path):
            database.initialize_database()
            migrated = database.get_staff()
            attendance = database.get_attendance_by_date_range(
                "2026-10-01",
                "2026-10-01",
            )

        self.assertEqual(migrated[0][1], "Morgan Nurse")
        self.assertEqual(migrated[0][6], "Nurse")
        self.assertEqual(attendance[0][5], "07:05:00")
        self.assertEqual(attendance[0][8], "Legacy")
        self.assertIsNone(attendance[0][9])

    def test_staff_id_unit_and_profile_photo_are_saved(self):
        staff = Nurse(None, "Casey Cleaner", "", "")
        database.add_staff(
            staff,
            rotation_position=0,
            staff_type="Janitor",
            unit="Facilities",
            profile_photo=b"jpeg-data",
        )
        saved = database.get_staff()[0]
        self.assertEqual(saved[2], "MPH-JAN-000001")
        self.assertEqual(saved[7], "Facilities")
        self.assertEqual(saved[8], b"jpeg-data")

    def test_shift_sign_in_and_sign_out_are_recorded(self):
        staff = Nurse(None, "Morgan Nurse", "", "")
        database.add_staff(
            staff,
            rotation_position=0,
            staff_type="Nurse",
            unit="Emergency",
        )
        staff_id = database.get_staff()[0][2]

        check_in = check_in_nurse(
            staff_id,
            datetime(2026, 10, 5, 7, 10, 0),
        )
        self.assertTrue(check_in["success"])
        self.assertEqual(check_in["status"], "Present")
        check_out = check_out_nurse(
            staff_id,
            datetime(2026, 10, 5, 18, 45, 0),
        )
        self.assertTrue(check_out["success"])
        records = database.get_attendance_by_date_range(
            "2026-10-05",
            "2026-10-05",
        )
        self.assertEqual(records[0][8], "Morning")
        self.assertEqual(records[0][9], "18:45:00")

    def test_late_check_in_and_overnight_sign_out(self):
        staff = Nurse(None, "Taylor Lab", "", "")
        database.add_staff(
            staff,
            rotation_position=0,
            staff_type="Lab Tech",
            unit="Laboratory",
        )
        staff_id = database.get_staff()[0][2]
        check_in = check_in_nurse(
            staff_id,
            datetime(2026, 10, 7, 19, 11, 0),
        )
        self.assertTrue(check_in["success"])
        self.assertEqual(check_in["status"], "Late")
        check_out = check_out_nurse(
            staff_id,
            datetime(2026, 10, 8, 6, 30, 0),
        )
        self.assertTrue(check_out["success"])
        records = database.get_attendance_by_date_range(
            "2026-10-07",
            "2026-10-07",
        )
        self.assertEqual(records[0][8], "Night")
        self.assertEqual(records[0][9], "06:30:00")

    def test_reliability_score_matches_attendance_to_scheduled_shifts(self):
        staff = (1, "Morgan Nurse", "MPH-NUR-000001", "", "Active", 0,
                 "Nurse", "Emergency", None)
        attendance_date = date(2026, 10, 5)
        as_of = attendance_date + timedelta(days=5)
        attendance_row = (
            1, staff[0], staff[1], staff[2], attendance_date.isoformat(),
            "07:00:00", "Present", staff[6], "Morning", None, staff[7],
        )
        with (
            patch.object(attendance_analytics, "get_active_nurses", return_value=[staff]),
            patch.object(
                attendance_analytics,
                "get_attendance_by_date_range",
                return_value=[attendance_row],
            ),
            patch.object(attendance_analytics, "get_leave_records", return_value=[]),
        ):
            score = attendance_analytics.get_staff_attendance_score(
                staff[0],
                as_of,
            )

        self.assertEqual(score["on_time_check_ins"], 1)
        self.assertEqual(score["scheduled_shifts"], 20)
        self.assertEqual(score["score"], 5)

    def test_backup_restore_recovers_complete_database(self):
        database.add_staff(
            Nurse(None, "Backup Janitor", "JAN002", ""),
            rotation_position=2,
            staff_type="Janitor",
        )
        destination = Path(self.temporary_directory.name) / "backup.sqlite3"
        backups.create_backup(destination)

        database.add_staff(
            Nurse(None, "Later Lab Tech", "LAB002", ""),
            rotation_position=1,
            staff_type="Lab Tech",
        )
        backups.restore_backup(destination)

        self.assertEqual(
            [record[2] for record in database.get_staff()],
            ["MPH-JAN-000001"],
        )
        self.assertEqual(database.authenticate("unknown-password"), None)

    def test_restore_rejects_non_roster_database_without_replacing_data(self):
        database.add_staff(
            Nurse(None, "Current Nurse", "NRS020", ""),
            staff_type="Nurse",
        )
        invalid_path = Path(self.temporary_directory.name) / "invalid.sqlite3"
        with sqlite3.connect(invalid_path) as connection:
            connection.execute("CREATE TABLE unrelated (id INTEGER)")
        connection.close()

        with self.assertRaisesRegex(ValueError, "not a complete StaffRoster"):
            backups.restore_backup(invalid_path)

        self.assertEqual(
            [record[2] for record in database.get_staff()],
            ["MPH-NUR-000001"],
        )


if __name__ == "__main__":
    unittest.main()
