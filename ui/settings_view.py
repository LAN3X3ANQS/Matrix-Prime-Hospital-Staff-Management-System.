from datetime import datetime, timezone
import hashlib

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from database.database import change_password, get_pending_password_roles
from networking.config import get_client_config
from networking.transport import remote_server_call


class SettingsView(QWidget):
    def __init__(self, parent=None, lan_server=None):
        super().__init__(parent)
        self.lan_server = lan_server
        self.is_remote_client = self.lan_server is None and get_client_config() is not None
        self.initial_setup_pending = bool(get_pending_password_roles())
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(18)

        if self.initial_setup_pending:
            description_text = (
                "Initial access passwords are active. Update each shared "
                "password here. Each must be at least 6 characters, and "
                "the Admin and Staff passwords must differ."
            )
        else:
            description_text = (
                "Update the shared access passwords. Each must be at least "
                "6 characters, and the Admin and Staff passwords must differ."
            )
        description = QLabel(description_text)
        description.setObjectName("settings_description")
        description.setWordWrap(True)
        self.description_label = description
        layout.addWidget(description)

        for role, title, detail in (
            ("ADMIN", "Admin password", "Full access to all application areas."),
            ("STAFF", "Staff password", "Operational access for roster and attendance."),
        ):
            layout.addWidget(self.create_password_card(role, title, detail))

        if self.lan_server is not None or self.is_remote_client:
            layout.addWidget(self.create_network_card())

        layout.addStretch()
        self.setStyleSheet("""
            QLabel#settings_description {
                color: #667085;
                font-size: 13px;
            }
            QFrame#password_card {
                background: #FFFFFF;
                border: 1px solid #E4E7EC;
                border-radius: 10px;
            }
            QLabel#password_title {
                color: #182230;
                font-size: 15px;
                font-weight: 600;
            }
            QLabel#password_detail {
                color: #667085;
                font-size: 12px;
            }
        """)

    def create_password_card(self, role, title, detail):
        card = QFrame()
        card.setObjectName("password_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("password_title")
        detail_label = QLabel(detail)
        detail_label.setObjectName("password_detail")
        layout.addWidget(title_label)
        layout.addWidget(detail_label)

        new_password = QLineEdit()
        new_password.setPlaceholderText("New password (6 characters minimum)")
        new_password.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_password = QLineEdit()
        confirm_password.setPlaceholderText("Confirm new password")
        confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(new_password)
        layout.addWidget(confirm_password)

        button = QPushButton(f"Update {role.title()} password")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(
            lambda checked=False: self.update_password(
                role,
                new_password,
                confirm_password,
            )
        )
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignRight)
        return card

    def create_network_card(self):
        card = QFrame()
        card.setObjectName("password_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        title = QLabel("Connected workstations")
        title.setObjectName("password_title")
        detail = QLabel(
            "Backups are complete only when the workstation has a verified "
            "copy of the current server database. A data change makes older "
            "copies out of date."
        )
        detail.setObjectName("password_detail")
        detail.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(detail)
        actions = QHBoxLayout()
        self.refresh_workstations_button = QPushButton("Refresh")
        self.refresh_workstations_button.clicked.connect(self.refresh_workstations)
        actions.addWidget(self.refresh_workstations_button)
        if self.lan_server is not None:
            pairing_button = QPushButton("Generate pairing PIN")
            pairing_button.clicked.connect(self.show_pairing_code)
            revoke_button = QPushButton("Revoke all workstations")
            revoke_button.clicked.connect(self.revoke_workstations)
            actions.addWidget(pairing_button)
            actions.addWidget(revoke_button)
        layout.addLayout(actions)
        self.workstation_scroll = QScrollArea()
        self.workstation_scroll.setWidgetResizable(True)
        self.workstation_scroll.setMaximumHeight(350)
        self.workstation_container = QWidget()
        self.workstation_list = QVBoxLayout(self.workstation_container)
        self.workstation_list.setContentsMargins(0, 0, 0, 0)
        self.workstation_list.setSpacing(8)
        self.workstation_scroll.setWidget(self.workstation_container)
        layout.addWidget(self.workstation_scroll)
        self.refresh_workstations()
        return card

    def refresh_workstations(self):
        try:
            if self.lan_server is not None:
                workstations = self.lan_server.get_paired_workstations()
            else:
                workstations = remote_server_call("get_paired_workstations")
        except (ConnectionError, OSError, PermissionError, RuntimeError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Could not load workstations",
                f"The server could not return its workstation list:\n{error}",
            )
            return

        while self.workstation_list.count():
            item = self.workstation_list.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if self.lan_server is not None:
            self.workstation_list.addWidget(
                self.create_workstation_row(
                    {"name": "This computer", "is_server": True}
                )
            )
        current_client_id = None
        if self.is_remote_client:
            config = get_client_config()
            current_client_id = hashlib.sha256(
                config["client_key"].encode("utf-8")
            ).hexdigest()
        for workstation in workstations:
            workstation["is_current"] = workstation["id"] == current_client_id
            self.workstation_list.addWidget(
                self.create_workstation_row(workstation)
            )
        if not workstations:
            empty = QLabel("No workstations are paired with this server yet.")
            empty.setObjectName("password_detail")
            self.workstation_list.addWidget(empty)
        self.workstation_list.addStretch()

    def create_workstation_row(self, workstation):
        row = QFrame()
        row.setObjectName("password_card")
        layout = QVBoxLayout(row)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)

        name_row = QHBoxLayout()
        name = QLabel(workstation["name"])
        name.setObjectName("password_title")
        name_row.addWidget(name)
        name_row.addStretch()
        if workstation.get("is_server"):
            status = "BASE SERVER"
        elif workstation.get("blocked"):
            status = "BLOCKED"
        elif workstation.get("is_current"):
            status = "THIS PC"
        else:
            status = "PAIRED"
        status_label = QLabel(status)
        status_label.setObjectName("password_detail")
        name_row.addWidget(status_label)
        layout.addLayout(name_row)

        if not workstation.get("is_server"):
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(workstation.get("backup_progress", 0))
            progress.setFormat("%p% of current server backup")
            layout.addWidget(progress)

            last_backup = workstation.get("backup_completed_at")
            if workstation.get("backup_complete"):
                backup_status = f"Complete · {self.format_timestamp(last_backup)}"
            elif last_backup:
                backup_status = (
                    f"Out of date · last saved {self.format_timestamp(last_backup)}"
                )
            else:
                backup_status = "No verified backup of the current data"
            backup_label = QLabel(backup_status)
            backup_label.setObjectName("password_detail")
            layout.addWidget(backup_label)

            last_seen = workstation.get("last_seen")
            seen_label = QLabel(
                f"Last active: {self.format_timestamp(last_seen)}"
                if last_seen
                else "Last active: unknown"
            )
            seen_label.setObjectName("password_detail")
            layout.addWidget(seen_label)

            actions = QHBoxLayout()
            actions.addStretch()
            if workstation.get("backup_complete") and not workstation.get("blocked"):
                promote_button = QPushButton("Prepare host migration")
                promote_button.clicked.connect(
                    lambda checked=False, item=dict(workstation):
                    self.show_migration_steps(item)
                )
                actions.addWidget(promote_button)
            if not workstation.get("is_current"):
                blocked = workstation.get("blocked", False)
                access_button = QPushButton(
                    "Unblock PC" if blocked else "Block PC"
                )
                access_button.clicked.connect(
                    lambda checked=False, item=dict(workstation), value=not blocked:
                    self.set_workstation_blocked(item, value)
                )
                actions.addWidget(access_button)
            layout.addLayout(actions)
        return row

    @staticmethod
    def format_timestamp(value):
        if not value:
            return "unknown"
        try:
            timestamp = datetime.fromisoformat(value)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            return timestamp.astimezone().strftime("%Y-%m-%d %H:%M")
        except (TypeError, ValueError):
            return "unknown"

    def set_workstation_blocked(self, workstation, blocked):
        name = workstation.get("name", "this workstation")
        if blocked:
            confirmation = QMessageBox.warning(
                self,
                "Block workstation?",
                f"{name} will be disconnected immediately and will not be able "
                "to sign in until an Admin unblocks it.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if confirmation != QMessageBox.StandardButton.Yes:
                return
        try:
            if self.lan_server is not None:
                self.lan_server.set_workstation_blocked(
                    workstation["id"],
                    blocked,
                )
            else:
                remote_server_call(
                    "set_workstation_blocked",
                    (workstation["id"], blocked),
                )
        except (ConnectionError, OSError, PermissionError, RuntimeError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Workstation access not updated",
                f"{name} could not be updated:\n{error}",
            )
            return
        self.refresh_workstations()

    def show_migration_steps(self, workstation):
        QMessageBox.information(
            self,
            "Prepare base-server change",
            f"{workstation['name']} has a verified backup of the current "
            "server data. To complete the change safely:\n\n"
            "1. On that PC, close the app and start it again.\n"
            "2. Choose “Make this computer the shared server”.\n"
            "3. Sign in as Admin, open Data & backups, and restore the "
            "verified backup saved on that PC.\n"
            "4. Pair each workstation to the new server using its new "
            "address, fingerprint, and six-digit PIN.\n\n"
            "Keep the current server running until the backup is restored. "
            "After confirming the new server works, close the old server.",
        )

    def show_pairing_code(self):
        self.lan_server.create_pairing_code()
        details = self.lan_server.get_pairing_details()
        copy_text = (
            f"Server address: {details['host']}\n"
            f"Server port: {details['port']}\n"
            f"Pairing PIN: {details['code']}\n"
            f"TLS fingerprint: {details['fingerprint']}"
        )
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setWindowTitle("Workstation pairing details")
        dialog.setText(
            "Enter the server address and six-digit PIN on each workstation. "
            "Before connecting, compare its TLS fingerprint with this value."
        )
        dialog.setInformativeText(
            f"Server address: {details['host']}\n"
            f"Server port: {details['port']}\n"
            f"Pairing PIN: {details['code']}\n"
            f"TLS fingerprint:\n{details['fingerprint']}\n\n"
            "The PIN expires in five minutes."
        )
        dialog.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        copy_button = dialog.addButton(
            "Copy pairing details",
            QMessageBox.ButtonRole.ActionRole,
        )
        from PySide6.QtGui import QGuiApplication

        copy_button.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(copy_text)
        )
        dialog.addButton(QMessageBox.StandardButton.Close)
        dialog.exec()

    def revoke_workstations(self):
        confirmation = QMessageBox.warning(
            self,
            "Revoke paired workstations?",
            "This will disconnect every paired workstation. They must be "
            "paired again using a new code.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        try:
            self.lan_server.revoke_all_workstations()
        except OSError as error:
            QMessageBox.critical(
                self,
                "Could not revoke workstations",
                f"Paired workstation credentials could not be updated:\n{error}",
            )
            return
        QMessageBox.information(
            self,
            "Workstations revoked",
            "All paired workstations have been disconnected.",
        )

    def update_password(self, role, new_password, confirm_password):
        password = new_password.text()
        if password != confirm_password.text():
            QMessageBox.warning(
                self,
                "Passwords do not match",
                "Enter the same password in both fields.",
            )
            confirm_password.setFocus()
            return

        try:
            change_password(role, password)
        except ValueError as error:
            QMessageBox.warning(self, "Password not updated", str(error))
            new_password.setFocus()
            new_password.selectAll()
            return

        new_password.clear()
        confirm_password.clear()
        QMessageBox.information(
            self,
            "Password updated",
            f"The {role.title()} password has been changed.",
        )
        self.initial_setup_pending = bool(get_pending_password_roles())
        if not self.initial_setup_pending:
            self.description_label.setText(
                "Update the shared access passwords. Each must be at least "
                "6 characters, and the Admin and Staff passwords must differ."
            )
