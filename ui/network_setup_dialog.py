from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from networking.config import clear_client_config, get_client_config
from networking.transport import pair_with_server


class NetworkSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode = None
        self.server = None
        self.setWindowTitle("Matrix Prime Hospital - Network setup")
        self.setMinimumWidth(560)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(14)

        title = QLabel("Choose how this computer connects")
        title.setStyleSheet("font-size: 21px; font-weight: 700; color: #17324D;")
        description = QLabel(
            "Use one computer as the hospital LAN server, or connect this "
            "workstation to a server that has already been started."
        )
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 13px; color: #667085;")
        layout.addWidget(title)
        layout.addWidget(description)

        self.local_button = QPushButton("Use this computer only")
        self.server_button = QPushButton("Make this computer the shared server")
        self.client_button = QPushButton("Connect to a shared server")
        self.saved_button = QPushButton("Use saved shared server")
        for button in (
            self.local_button,
            self.server_button,
            self.client_button,
            self.saved_button,
        ):
            button.setMinimumHeight(42)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(button)

        self.pairing_input = QLineEdit()
        self.pairing_input.setPlaceholderText("Paste the server pairing code")
        self.pairing_input.setMinimumHeight(40)
        layout.addWidget(self.pairing_input)

        try:
            config = get_client_config()
        except RuntimeError as error:
            config = None
            QMessageBox.warning(self, "Connection settings", str(error))

        self.has_saved_connection = config is not None
        self.saved_status = QLabel(
            "This computer is paired to a shared server."
            if config
            else "No shared server is currently configured."
        )
        self.saved_button.setVisible(bool(config))
        self.saved_status.setStyleSheet("font-size: 12px; color: #667085;")
        layout.addWidget(self.saved_status)

        self.local_button.clicked.connect(self.use_local)
        self.server_button.clicked.connect(self.make_server)
        self.client_button.clicked.connect(self.connect_to_server)
        self.saved_button.clicked.connect(self.use_saved_server)
        self.pairing_input.returnPressed.connect(self.connect_to_server)

    def use_local(self):
        if self.has_saved_connection:
            confirmation = QMessageBox.warning(
                self,
                "Use a separate local database?",
                "This disconnects this computer from the shared hospital "
                "database. Changes made here will not sync with the server.",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if confirmation != QMessageBox.StandardButton.Yes:
                return
        clear_client_config()
        self.mode = "local"
        self.accept()

    def make_server(self):
        if self.has_saved_connection:
            confirmation = QMessageBox.warning(
                self,
                "Start a separate server?",
                "This computer is currently configured as a client. Starting "
                "a new server will use its local database instead of the "
                "existing shared database.",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if confirmation != QMessageBox.StandardButton.Yes:
                return
        clear_client_config()
        self.mode = "server"
        self.accept()

    def use_saved_server(self):
        self.mode = "client"
        self.accept()

    def connect_to_server(self):
        try:
            self.server = pair_with_server(self.pairing_input.text())
        except (OSError, ValueError, RuntimeError, PermissionError) as error:
            QMessageBox.warning(self, "Could not connect", str(error))
            return
        self.mode = "client"
        self.accept()
