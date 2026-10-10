import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database.database as database


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "auth.sqlite3"
        self.database_patch = patch.object(
            database,
            "DATABASE_PATH",
            self.database_path,
        )
        self.database_patch.start()
        self.environment_patch = patch.dict(os.environ, {}, clear=True)
        self.environment_patch.start()

    def tearDown(self):
        self.environment_patch.stop()
        self.database_patch.stop()
        self.temporary_directory.cleanup()

    def test_generated_passwords_are_hashed_and_persistent(self):
        bootstrap_passwords = database.initialize_authentication()

        self.assertEqual(set(bootstrap_passwords), {"ADMIN", "STAFF"})
        self.assertNotEqual(
            bootstrap_passwords["ADMIN"],
            bootstrap_passwords["STAFF"],
        )
        self.assertEqual(
            database.authenticate(bootstrap_passwords["ADMIN"]),
            "ADMIN",
        )
        self.assertEqual(
            database.authenticate(bootstrap_passwords["STAFF"]),
            "STAFF",
        )
        self.assertEqual(database.initialize_authentication(), {})

        connection = sqlite3.connect(database.DATABASE_PATH)
        stored_passwords = connection.execute(
            "SELECT password_hash, password_salt FROM auth_users"
        ).fetchall()
        connection.close()
        self.assertTrue(
            all(len(password_hash) == 64 for password_hash, _ in stored_passwords)
        )
        self.assertTrue(all(len(salt) == 64 for _, salt in stored_passwords))
        self.assertTrue(
            all(
                password not in {password_hash, salt}
                for password in bootstrap_passwords.values()
                for password_hash, salt in stored_passwords
            )
        )

    def test_password_changes_keep_roles_separate(self):
        bootstrap_passwords = database.initialize_authentication()
        new_admin_password = "New-Admin-Access-2026"
        database.change_password("ADMIN", new_admin_password)

        self.assertEqual(database.get_pending_password_roles(), {"STAFF"})
        self.assertIsNone(
            database.authenticate(bootstrap_passwords["ADMIN"])
        )
        self.assertEqual(database.authenticate(new_admin_password), "ADMIN")
        self.assertEqual(
            database.authenticate(bootstrap_passwords["STAFF"]),
            "STAFF",
        )

        with self.assertRaisesRegex(ValueError, "must be different"):
            database.change_password("ADMIN", bootstrap_passwords["STAFF"])
        with self.assertRaisesRegex(ValueError, "6 characters"):
            database.change_password("STAFF", "12345")
        database.change_password("STAFF", "123456")
        self.assertEqual(database.authenticate("123456"), "STAFF")
        with self.assertRaisesRegex(ValueError, "Invalid authentication role"):
            database.change_password("NURSE", "long-enough-password")

        self.assertEqual(database.get_pending_password_roles(), set())

    def test_environment_passwords_are_used_without_being_returned(self):
        os.environ["NURSEROSTER_ADMIN_PASSWORD"] = "Admin-Seed-Password-2026"
        os.environ["NURSEROSTER_STAFF_PASSWORD"] = "Staff-Seed-Password-2026"

        bootstrap_passwords = database.initialize_authentication()

        self.assertEqual(bootstrap_passwords, {})
        self.assertEqual(
            database.authenticate("Admin-Seed-Password-2026"),
            "ADMIN",
        )
        self.assertEqual(
            database.authenticate("Staff-Seed-Password-2026"),
            "STAFF",
        )

    def test_bootstrap_rejects_matching_environment_passwords(self):
        os.environ["NURSEROSTER_ADMIN_PASSWORD"] = "Same-Seed-Password-2026"
        os.environ["NURSEROSTER_STAFF_PASSWORD"] = "Same-Seed-Password-2026"

        with self.assertRaisesRegex(ValueError, "must be different"):
            database.initialize_authentication()

    def test_bootstrap_accepts_six_character_passwords(self):
        os.environ["NURSEROSTER_ADMIN_PASSWORD"] = "admin6"
        os.environ["NURSEROSTER_STAFF_PASSWORD"] = "staff6"

        self.assertEqual(database.initialize_authentication(), {})
        self.assertEqual(database.authenticate("admin6"), "ADMIN")
        self.assertEqual(database.authenticate("staff6"), "STAFF")


if __name__ == "__main__":
    unittest.main()
