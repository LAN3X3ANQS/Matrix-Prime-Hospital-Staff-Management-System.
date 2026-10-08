import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.backups as backups
import database.database as database
import networking.config as network_config
from ui.main_window import MainWindow
from ui.nurse_form import NurseForm
from ui.network_setup_dialog import NetworkSetupDialog


class RoleUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "nurse_roster.db"
        self.database_patch = patch.object(
            database,
            "DATABASE_PATH",
            database_path,
        )
        self.database_patch.start()
        self.backup_patch = patch.object(backups, "DATABASE_PATH", database_path)
        self.backup_patch.start()
        database.initialize_database()

    def tearDown(self):
        self.backup_patch.stop()
        self.database_patch.stop()
        self.temporary_directory.cleanup()

    def test_admin_and_staff_have_separate_navigation(self):
        admin_window = MainWindow("ADMIN")
        staff_window = MainWindow("STAFF")
        try:
            self.assertEqual(
                admin_window.pages.currentWidget(),
                admin_window.pages_by_key["dashboard"],
            )
            self.assertIn("settings", admin_window.pages_by_key)
            self.assertIn("data_tools", admin_window.pages_by_key)
            self.assertIn("help", admin_window.pages_by_key)
            self.assertEqual(
                set(staff_window.pages_by_key),
                {"dashboard", "roster", "attendance", "history", "help"},
            )
            self.assertIn("help", admin_window.navigation_buttons)
            self.assertIn("help", staff_window.navigation_buttons)

            staff_window.show_settings()
            self.assertEqual(
                staff_window.pages.currentWidget(),
                staff_window.pages_by_key["dashboard"],
            )
            staff_window.open_page("help")
            self.assertEqual(
                staff_window.pages.currentWidget(),
                staff_window.pages_by_key["help"],
            )
        finally:
            admin_window.close()
            staff_window.close()

    def test_staff_registration_offers_all_personnel_types(self):
        form = NurseForm()
        try:
            self.assertEqual(
                [
                    form.staff_type_input.itemText(index)
                    for index in range(form.staff_type_input.count())
                ],
                ["Admin", "Janitor", "Front Desk", "Nurse", "Lab Tech", "Doctor"],
            )
        finally:
            form.close()

    def test_network_setup_offers_server_and_client_modes(self):
        with patch.object(
            network_config,
            "CLIENT_CONFIG_PATH",
            Path(self.temporary_directory.name) / "not-paired.json",
        ):
            dialog = NetworkSetupDialog()
        try:
            self.assertEqual(
                dialog.server_button.text(),
                "Make this computer the shared server",
            )
            self.assertEqual(
                dialog.client_button.text(),
                "Connect to a shared server",
            )
            self.assertFalse(dialog.saved_button.isVisible())
        finally:
            dialog.close()


if __name__ == "__main__":
    unittest.main()
