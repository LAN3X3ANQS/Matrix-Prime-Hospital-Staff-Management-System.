from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)
from database.database import authenticate


class LoginWindow(QWidget):
    login_successful = Signal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Matrix Prime Hospital | Sign in")
        self.setFixedSize(460, 560)

        self.password_visible = False

        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F8FA;
                color: #1F2933;
                font-family: "Segoe UI";
            }

            QFrame#loginCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 18px;
            }

            QLabel#logoMark {
                background-color: #0B3B82;
                color: white;
                border-radius: 28px;
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#appName {
                color: #0B3B82;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#subtitle {
                color: #64748B;
                font-size: 14px;
            }

            QLabel#loginTitle {
                color: #1F2933;
                font-size: 21px;
                font-weight: 600;
            }

            QLabel#loginDescription {
                color: #64748B;
                font-size: 13px;
            }

            QLabel#passwordLabel {
                color: #334155;
                font-size: 13px;
                font-weight: 600;
            }

            QLineEdit#passwordInput {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 9px;
                padding: 11px 42px 11px 13px;
                font-size: 14px;
                color: #1F2933;
            }

            QLineEdit#passwordInput:focus {
                border: 2px solid #0B3B82;
                padding: 10px 41px 10px 12px;
            }

            QPushButton#togglePasswordButton {
                background-color: transparent;
                color: #64748B;
                border: none;
                padding: 0;
                font-size: 16px;
                font-weight: 600;
            }

            QPushButton#togglePasswordButton:hover {
                color: #0B3B82;
                background-color: transparent;
            }

            QPushButton#loginButton {
                background-color: #00C853;
                color: white;
                border: none;
                border-radius: 9px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton#loginButton:hover {
                background-color: #00B048;
            }

            QPushButton#loginButton:pressed {
                background-color: #00963E;
            }

            QLabel#errorLabel {
                color: #C62828;
                font-size: 13px;
                font-weight: 500;
            }

            QLabel#footer {
                color: #94A3B8;
                font-size: 11px;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(35, 30, 35, 30)
        outer_layout.setSpacing(0)

        outer_layout.addStretch()

        card = QFrame()
        card.setObjectName("loginCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(38, 35, 38, 35)
        card_layout.setSpacing(0)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(12)

        logo = QLabel("N")
        logo.setObjectName("logoMark")
        logo.setFixedSize(56, 56)
        logo.setAlignment(Qt.AlignCenter)

        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(1)

        app_name = QLabel("Matrix Prime Hospital")
        app_name.setObjectName("appName")

        subtitle = QLabel("Hospital Staff Management System")
        subtitle.setObjectName("subtitle")

        brand_layout.addWidget(app_name)
        brand_layout.addWidget(subtitle)

        logo_row.addWidget(logo)
        logo_row.addLayout(brand_layout)
        logo_row.addStretch()

        card_layout.addLayout(logo_row)
        card_layout.addSpacing(38)

        login_title = QLabel("Welcome back")
        login_title.setObjectName("loginTitle")

        login_description = QLabel(
            "Enter your access password to continue."
        )
        login_description.setObjectName("loginDescription")
        login_description.setWordWrap(True)

        card_layout.addWidget(login_title)
        card_layout.addSpacing(6)
        card_layout.addWidget(login_description)
        card_layout.addSpacing(26)

        password_label = QLabel("Password")
        password_label.setObjectName("passwordLabel")

        card_layout.addWidget(password_label)
        card_layout.addSpacing(7)

        password_container = QWidget()
        password_container.setFixedHeight(44)

        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(0)

        self.password_input = QLineEdit()
        self.password_input.setObjectName("passwordInput")
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.handle_login)

        self.toggle_password_button = QPushButton("◉")
        self.toggle_password_button.setObjectName("togglePasswordButton")
        self.toggle_password_button.setFixedSize(38, 38)
        self.toggle_password_button.setCursor(Qt.PointingHandCursor)
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)

        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.toggle_password_button)

        card_layout.addWidget(password_container)
        card_layout.addSpacing(8)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setMinimumHeight(20)
        self.error_label.setWordWrap(True)

        card_layout.addWidget(self.error_label)
        card_layout.addSpacing(12)

        login_button = QPushButton("Sign In")
        login_button.setObjectName("loginButton")
        login_button.setCursor(Qt.PointingHandCursor)
        login_button.setMinimumHeight(44)
        login_button.clicked.connect(self.handle_login)

        card_layout.addWidget(login_button)

        outer_layout.addWidget(card)

        outer_layout.addSpacing(22)

        footer = QLabel("Secure local access · Hospital staff operations")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignCenter)

        outer_layout.addWidget(footer)

        outer_layout.addStretch()

        self.password_input.setFocus()

    def toggle_password_visibility(self):
        self.password_visible = not self.password_visible

        if self.password_visible:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_button.setText("○")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_button.setText("◉")

        self.password_input.setFocus()

    def handle_login(self):
        password = self.password_input.text()

        if not password:
            self.error_label.setText("Please enter your password.")
            self.password_input.setFocus()
            return

        try:
            role = authenticate(password)
        except (ConnectionError, PermissionError, RuntimeError) as error:
            QMessageBox.warning(
                self,
                "Sign-in unavailable",
                str(error),
            )
            return

        if role is None:
            self.error_label.setText("Incorrect password. Please try again.")
            self.password_input.selectAll()
            self.password_input.setFocus()
            return

        self.error_label.clear()
        self.login_successful.emit(role)