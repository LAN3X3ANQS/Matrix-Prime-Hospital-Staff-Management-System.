from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from database.backups import create_backup, restore_backup


class DataToolsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(18)

        description = QLabel(
            "Create a complete, portable database backup or restore this "
            "computer from a Matrix Prime Hospital backup. Backups include staff records, "
            "attendance, leave, shifts, and password hashes."
        )
        description.setObjectName("data_tools_description")
        description.setWordWrap(True)
        layout.addWidget(description)

        backup_card = self.create_card(
            "Create a backup",
            "Save a database copy as a SQLite file. The backup is not "
            "encrypted, so store it in a secure location.",
            "Save backup",
            self.create_backup,
        )
        restore_card = self.create_card(
            "Restore a backup",
            "Replace the current Matrix Prime Hospital database with a "
            "previously created backup. In shared-server mode, this replaces "
            "the database used by every connected workstation.",
            "Choose backup to restore",
            self.restore_backup,
        )
        layout.addWidget(backup_card)
        layout.addWidget(restore_card)
        layout.addStretch()

        self.setStyleSheet("""
            QLabel#data_tools_description {
                color: #667085;
                font-size: 13px;
            }
            QFrame#data_tools_card {
                background: #FFFFFF;
                border: 1px solid #E4E7EC;
                border-radius: 10px;
            }
            QLabel#data_tools_title {
                color: #182230;
                font-size: 15px;
                font-weight: 600;
            }
            QLabel#data_tools_detail {
                color: #667085;
                font-size: 12px;
            }
        """)

    @staticmethod
    def create_card(title, detail, button_text, callback):
        card = QFrame()
        card.setObjectName("data_tools_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("data_tools_title")
        detail_label = QLabel(detail)
        detail_label.setObjectName("data_tools_detail")
        detail_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(detail_label)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button = QPushButton(button_text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(callback)
        button_row.addWidget(button)
        layout.addLayout(button_row)
        return card

    def create_backup(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Matrix Prime Hospital backup",
            "Matrix-Prime-Hospital-backup.sqlite3",
            "Matrix Prime Hospital backup (*.sqlite3 *.db)",
        )
        if not file_path:
            return
        try:
            backup_path = create_backup(file_path)
        except (OSError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Backup failed",
                f"Could not create the backup:\n\n{error}",
            )
            return
        QMessageBox.information(
            self,
            "Backup created",
            f"Database backup saved to:\n{backup_path}",
        )

    def restore_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Matrix Prime Hospital backup",
            "",
            "Matrix Prime Hospital backup (*.sqlite3 *.db)",
        )
        if not file_path:
            return

        confirmation = QMessageBox.warning(
            self,
            "Replace shared database?",
            "This replaces all data in the current Matrix Prime Hospital database with the selected "
            "backup. In shared mode, close other workstations before "
            "restoring. Create a backup of the current data first if you may "
            "need it. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            restored_path = restore_backup(file_path)
        except (OSError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Restore failed",
                f"The database was not replaced:\n\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Backup restored",
            "Backup restored successfully. Restart Matrix Prime Hospital to load the restored data.",
        )
