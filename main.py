from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from database.database import initialize_database
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from ui.network_setup_dialog import NetworkSetupDialog
from ui.app_icon import get_app_icon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from PySide6.QtGui import QGuiApplication


class ApplicationController:

    def __init__(self):
        self.login_window = None
        self.main_window = None
        self.lan_server = None

    def start(self):
        self.show_login()

    def show_login(self):
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.handle_login_success)
        self.login_window.show()

    def handle_login_success(self, role):
        self.main_window = MainWindow(role=role, lan_server=self.lan_server)
        self.main_window.login_requested.connect(self.handle_logout)

        self.login_window.close()
        self.login_window = None

        self.main_window.show()

    def handle_logout(self):
        from networking.transport import remote_logout

        try:
            remote_logout()
        except (ConnectionError, RuntimeError) as error:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self.main_window,
                "Server sign-out unavailable",
                f"This workstation was signed out locally, but the server "
                f"could not confirm sign-out:\n{error}",
            )
        self.main_window.close()
        self.main_window = None
        self.show_login()


def main():
    app = QApplication([])
    app.setWindowIcon(get_app_icon())
    setup = NetworkSetupDialog()
    if not setup.exec():
        return

    lan_server = None
    bootstrap_passwords = {}
    if setup.mode in {"local", "server"}:
        bootstrap_passwords = initialize_database()
    if setup.mode == "server":
        try:
            from networking.server import LanServer

            lan_server = LanServer()
            lan_server.start()
        except (OSError, RuntimeError) as error:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(
                None,
                "Could not start shared server",
                f"The LAN server could not be started:\n{error}\n\n"
                "Check whether the server port is already in use and ask "
                "hospital IT to allow the app through the private-network firewall.",
            )
            return
        app.aboutToQuit.connect(lan_server.stop)
        pairing = QDialog()
        pairing.setWindowTitle("Matrix Prime Hospital - Pair workstations")
        pairing.setMinimumWidth(620)
        pairing_layout = QVBoxLayout(pairing)
        details = lan_server.get_pairing_details()
        copy_text = (
            f"Server address: {details['host']}\n"
            f"Server port: {details['port']}\n"
            f"Pairing PIN: {details['code']}\n"
            f"TLS fingerprint: {details['fingerprint']}"
        )
        pairing_layout.addWidget(QLabel(
            "Shared server is running. On each workstation, enter the server "
            "address and six-digit PIN below, then compare the TLS fingerprint "
            "with this screen before connecting. The PIN expires after five "
            "minutes and can pair multiple computers during that window."
        ))
        address_field = QLabel(f"Server address: {details['host']}")
        port_field = QLabel(f"Server port: {details['port']}")
        pin_field = QLabel(f"Pairing PIN: {details['code']}")
        fingerprint_field = QLabel(
            f"TLS fingerprint (verify on every workstation):\n"
            f"{details['fingerprint']}"
        )
        fingerprint_field.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        fingerprint_field.setWordWrap(True)
        for field in (address_field, port_field, pin_field, fingerprint_field):
            field.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            field.setStyleSheet(
                "font-family: Consolas; padding: 10px; "
                "background: #F2F4F7; border: 1px solid #D0D5DD;"
            )
            pairing_layout.addWidget(field)
        actions = QHBoxLayout()
        copy_button = QPushButton("Copy pairing details")
        done_button = QPushButton("Continue")
        copy_button.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(copy_text)
        )
        done_button.clicked.connect(pairing.accept)
        actions.addWidget(copy_button)
        actions.addStretch()
        actions.addWidget(done_button)
        pairing_layout.addLayout(actions)
        pairing.exec()

    if bootstrap_passwords:
        from PySide6.QtWidgets import QMessageBox

        password_message = QMessageBox(
            QMessageBox.Icon.Information,
            "Initial shared passwords",
            "The first-run shared passwords are shown below. Save them "
            "securely and change them immediately in Admin Settings.",
            QMessageBox.StandardButton.Ok,
        )
        password_message.setInformativeText(
            "\n".join(
                f"{role}: {password}"
                for role, password in bootstrap_passwords.items()
            )
        )
        password_message.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        password_message.exec()
        print(
            "Matrix Prime Hospital initial access passwords "
            "(change these in Settings after signing in):"
        )
        for role, password in bootstrap_passwords.items():
            print(f"{role}: {password}")

    controller = ApplicationController()
    controller.lan_server = lan_server
    controller.start()

    app.exec()


if __name__ == "__main__":
    main()