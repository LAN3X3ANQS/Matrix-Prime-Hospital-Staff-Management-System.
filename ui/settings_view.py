from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from database.database import change_password, get_pending_password_roles
from PySide6.QtWidgets import QInputDialog


class SettingsView(QWidget):
    def __init__(self, parent=None, lan_server=None):
        super().__init__(parent)
        self.lan_server = lan_server
        self.initial_setup_pending = bool(get_pending_password_roles())
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(18)

        if self.initial_setup_pending:
            description_text = (
                "Initial access passwords are active. Update each shared "
                "password here. Each must be at least 12 characters, and "
                "the Admin and Staff passwords must differ."
            )
        else:
            description_text = (
                "Update the shared access passwords. Each must be at least "
                "12 characters, and the Admin and Staff passwords must differ."
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

        if self.lan_server is not None:
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
        new_password.setPlaceholderText("New password (12 characters minimum)")
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
        title = QLabel("Shared LAN server")
        title.setObjectName("password_title")
        detail = QLabel(
            "Generate a short-lived workstation pairing code or revoke all "
            "currently paired workstations."
        )
        detail.setObjectName("password_detail")
        detail.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(detail)
        actions = QHBoxLayout()
        pairing_button = QPushButton("Generate pairing code")
        pairing_button.clicked.connect(self.show_pairing_code)
        revoke_button = QPushButton("Revoke all workstations")
        revoke_button.clicked.connect(self.revoke_workstations)
        actions.addWidget(pairing_button)
        actions.addWidget(revoke_button)
        layout.addLayout(actions)
        return card

    def show_pairing_code(self):
        pairing_code = self.lan_server.create_pairing_code()
        code, accepted = QInputDialog.getText(
            self,
            "Workstation pairing code",
            "Copy this short-lived code to the hospital workstations to pair them:",
            text=pairing_code,
        )
        if accepted:
            from PySide6.QtGui import QGuiApplication

            QGuiApplication.clipboard().setText(code)

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
                "12 characters, and the Admin and Staff passwords must differ."
            )
