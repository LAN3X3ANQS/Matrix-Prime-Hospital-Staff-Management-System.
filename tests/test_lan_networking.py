import hashlib
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import database.backups as backups
import database.database as database
import networking.config as network_config
import networking.server as network_server
import networking.transport as network_transport
from attendance.attendance import check_in_nurse
from database.backups import create_backup, restore_backup
from database.models import Staff


class LanNetworkingTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.database_path = root / "hospital.sqlite3"
        self.database_patch = patch.object(database, "DATABASE_PATH", self.database_path)
        self.database_patch.start()
        self.backup_patch = patch.object(backups, "DATABASE_PATH", self.database_path)
        self.backup_patch.start()
        self.config_path_patch = patch.object(
            network_config,
            "CLIENT_CONFIG_PATH",
            root / "client.json",
        )
        self.config_path_patch.start()
        self.config_dir_patch = patch.object(network_config, "APP_DATA_DIR", root)
        self.config_dir_patch.start()
        self.server_dir_patch = patch.object(network_server, "APP_DATA_DIR", root)
        self.server_dir_patch.start()
        self.cert_patch = patch.object(network_server, "CERT_PATH", root / "cert.pem")
        self.cert_patch.start()
        self.key_patch = patch.object(network_server, "KEY_PATH", root / "key.pem")
        self.key_patch.start()
        self.clients_patch = patch.object(
            network_server,
            "CLIENTS_PATH",
            root / "paired-clients.json",
        )
        self.clients_patch.start()
        self.environment_patch = patch.dict(
            os.environ,
            {
                "NURSEROSTER_ADMIN_PASSWORD": "TestAdminPassword_2026!",
                "NURSEROSTER_STAFF_PASSWORD": "TestStaffPassword_2026!",
            },
        )
        self.environment_patch.start()
        database.initialize_database()
        self.server = network_server.LanServer(port=0)
        self.server.start()

    def tearDown(self):
        network_transport.remote_logout()
        self.server.stop()
        self.environment_patch.stop()
        self.clients_patch.stop()
        self.key_patch.stop()
        self.cert_patch.stop()
        self.server_dir_patch.stop()
        self.config_dir_patch.stop()
        self.config_path_patch.stop()
        self.backup_patch.stop()
        self.database_patch.stop()
        self.temporary_directory.cleanup()

    def test_pairing_and_data_are_shared_through_server_api(self):
        code = self.server.pairing_code
        details = network_transport.parse_pairing_code(code)
        details["port"] = self.server.port
        import base64
        import json

        encoded = base64.urlsafe_b64encode(
            json.dumps(details, separators=(",", ":")).encode()
        ).decode().rstrip("=")
        network_transport.pair_with_server(f"MPH1:{encoded}")
        self.assertEqual(
            database.authenticate("TestAdminPassword_2026!"),
            "ADMIN",
        )
        with self.assertRaises(ValueError):
            create_backup(self.database_path)

        staff = Staff(None, "Morgan Nurse", "", "")
        database.add_staff(
            staff,
            rotation_position=0,
            staff_type="Nurse",
            unit="Emergency",
            profile_photo=b"small-test-photo",
        )
        result = database.get_staff()
        self.assertEqual(result[0][1], "Morgan Nurse")
        self.assertEqual(result[0][2], "MPH-NUR-000001")
        self.assertEqual(result[0][8], b"small-test-photo")
        sign_in = check_in_nurse(
            result[0][2],
            datetime(2026, 10, 5, 7, 5, 0),
        )
        self.assertTrue(sign_in["success"])
        attendance = database.get_attendance_by_date_range(
            "2026-10-05",
            "2026-10-05",
        )
        self.assertEqual(attendance[0][8], "Morning")

        backup_path = Path(self.temporary_directory.name) / "shared-backup.sqlite3"
        create_backup(backup_path)
        workstation = self.server.get_paired_workstations()[0]
        self.assertTrue(workstation["backup_complete"])
        self.assertEqual(workstation["backup_progress"], 100)
        database.deactivate_staff(result[0][0])
        workstation = self.server.get_paired_workstations()[0]
        self.assertFalse(workstation["backup_complete"])
        self.assertEqual(workstation["backup_progress"], 0)
        restore_backup(backup_path)
        self.assertEqual(database.get_active_staff()[0][1], "Morgan Nurse")

    def test_admin_can_block_and_unblock_a_paired_workstation(self):
        network_transport.pair_with_server(self.server.pairing_code)
        config = network_config.get_client_config()
        client_digest = hashlib.sha256(
            config["client_key"].encode("utf-8")
        ).hexdigest()

        self.server.set_workstation_blocked(client_digest, True)
        self.assertFalse(network_server._client_allowed(config["client_key"]))
        with self.assertRaises(PermissionError):
            network_transport.remote_login("TestAdminPassword_2026!")

        self.server.set_workstation_blocked(client_digest, False)
        self.assertTrue(network_server._client_allowed(config["client_key"]))

    def test_staff_session_is_blocked_from_admin_directory_reads(self):
        database.add_staff(
            Staff(None, "Morgan Nurse", "", "+15550001111"),
            rotation_position=0,
            staff_type="Nurse",
            unit="Emergency",
            profile_photo=b"private-photo",
        )
        code = self.server.pairing_code
        network_transport.pair_with_server(code)
        self.assertEqual(
            database.authenticate("TestStaffPassword_2026!"),
            "STAFF",
        )
        with self.assertRaises(PermissionError):
            database.get_staff()
        visible_staff = database.get_active_staff()
        self.assertEqual(visible_staff[0][3], "")
        self.assertIsNone(visible_staff[0][8])
        with self.assertRaises(PermissionError):
            network_transport.remote_server_call("get_paired_workstations")


if __name__ == "__main__":
    unittest.main()
