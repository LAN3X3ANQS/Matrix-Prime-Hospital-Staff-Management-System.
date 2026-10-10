from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QLabel,
    QFrame,
    QFileDialog,
    QScrollArea,
)


class NurseForm(QDialog):

    def __init__(self, nurse=None, parent=None):
        super().__init__(parent)

        self.nurse = nurse
        self.profile_photo = None
        self.remove_profile_photo = False

        self.setWindowTitle("Matrix Prime Hospital - Staff member")
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        width = min(520, available.width() - 40) if available else 520
        height = min(700, available.height() - 60) if available else 700
        width = max(1, width)
        height = max(1, height)
        self.setMinimumSize(min(480, width), min(480, height))
        self.resize(width, height)

        self.setup_ui()

        if nurse is not None:
            self.load_nurse()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #F7FAFC;
            }

            QLabel#title {
                color: #0B3B82;
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#description {
                color: #718096;
                font-size: 13px;
            }

            QFrame#form_card {
                background-color: white;
                border: 1px solid #E1E8EF;
                border-radius: 12px;
            }

            QLabel {
                color: #526779;
                font-size: 13px;
                font-weight: 600;
            }

            QLineEdit,
            QComboBox {
                background-color: white;
                border: 1px solid #CBD5E0;
                border-radius: 7px;
                padding: 9px 10px;
                min-height: 20px;
                color: #0B3B82;
                font-size: 13px;
            }

            QLineEdit:focus,
            QComboBox:focus {
                border: 1px solid #0B3B82;
            }

            QPushButton {
                border: none;
                border-radius: 7px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
                min-width: 90px;
            }

            QPushButton#cancel_button {
                background-color: #EDF2F7;
                color: #526779;
            }

            QPushButton#cancel_button:hover {
                background-color: #E2E8F0;
            }

            QPushButton#save_button {
                background-color: #00C853;
                color: white;
            }

            QPushButton#save_button:hover {
                background-color: #00B048;
            }

            QPushButton#save_button:pressed {
                background-color: #00963E;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(18)

        title = QLabel("Staff details")
        title.setObjectName("title")

        description = QLabel(
            "Register a staff member. Daily day staff have a fixed schedule; "
            "rotating staff are assigned a shift pattern."
        )
        description.setObjectName("description")

        main_layout.addWidget(title)
        main_layout.addWidget(description)

        form_card = QFrame()
        form_card.setObjectName("form_card")

        form_layout = QFormLayout()
        form_layout.setContentsMargins(22, 22, 22, 22)
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(16)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter full name")

        self.staff_id_input = QLineEdit()
        self.staff_id_input.setReadOnly(True)
        self.staff_id_input.setPlaceholderText(
            "Assigned automatically on registration"
        )
        self.staff_id_input.setText(
            self.nurse[2] if self.nurse is not None else "Assigned on save"
        )

        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText(
            "e.g. Emergency, Laboratory, Facilities"
        )

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number")

        self.status_input = QComboBox()
        self.status_input.addItems(["Active", "Inactive"])

        self.staff_type_input = QComboBox()
        self.staff_type_input.addItems(
            ["Admin", "Janitor", "Front Desk", "Nurse", "Lab Tech", "Doctor"]
        )
        self.staff_type_input.currentIndexChanged.connect(
            self.update_rotation_visibility
        )

        self.rotation_input = QComboBox()

        self.rotation_input.addItem(
            "Rotation 1 (M M N N O O)",
            0,
        )
        self.rotation_input.addItem(
            "Rotation 2 (N N O O M M)",
            1,
        )
        self.rotation_input.addItem(
            "Rotation 3 (O O M M N N)",
            2,
        )
        self.rotation_label = QLabel("Rotation")
        self.rotation_label.setStyleSheet("color: #526779;")
        self.rotation_input.currentIndexChanged.connect(
            self.update_rotation_visibility
        )

        self.photo_preview = QLabel("No profile picture")
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.setFixedSize(112, 112)
        self.photo_preview.setStyleSheet(
            "background: #F2F4F7; border: 1px solid #D0D5DD; "
            "border-radius: 56px; color: #667085;"
        )
        self.photo_button = QPushButton("Choose picture")
        self.photo_button.clicked.connect(self.choose_profile_photo)
        self.remove_photo_button = QPushButton("Remove picture")
        self.remove_photo_button.clicked.connect(self.clear_profile_photo)
        photo_actions = QVBoxLayout()
        photo_actions.addWidget(self.photo_button)
        photo_actions.addWidget(self.remove_photo_button)
        photo_row = QHBoxLayout()
        photo_row.addWidget(self.photo_preview)
        photo_row.addLayout(photo_actions)
        photo_row.addStretch()

        form_layout.addRow("Name", self.name_input)
        form_layout.addRow("Staff ID", self.staff_id_input)
        form_layout.addRow("Staff type", self.staff_type_input)
        form_layout.addRow("Unit", self.unit_input)
        form_layout.addRow("Phone", self.phone_input)
        form_layout.addRow("Status", self.status_input)
        form_layout.addRow(self.rotation_label, self.rotation_input)
        form_layout.addRow("Profile picture", photo_row)

        form_card.setLayout(form_layout)

        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_scroll.setWidget(form_card)
        main_layout.addWidget(form_scroll, 1)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancel_button")

        self.save_button = QPushButton("Save Staff Member")
        self.save_button.setObjectName("save_button")

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.update_rotation_visibility()

    def update_rotation_visibility(self):
        daily_day_staff = self.staff_type_input.currentText() in {
            "Janitor",
            "Admin",
            "Lab Tech",
            "Front Desk",
        }
        self.rotation_label.setVisible(not daily_day_staff)
        self.rotation_input.setVisible(not daily_day_staff)

    def load_nurse(self):
        self.name_input.setText(self.nurse[1])

        self.staff_id_input.setText(self.nurse[2])

        self.phone_input.setText(self.nurse[3] or "")

        status_index = self.status_input.findText(self.nurse[4])

        if status_index >= 0:
            self.status_input.setCurrentIndex(status_index)

        rotation_position = self.nurse[5]

        if rotation_position is not None:
            rotation_index = self.rotation_input.findData(rotation_position)

            if rotation_index >= 0:
                self.rotation_input.setCurrentIndex(rotation_index)

        staff_type = self.nurse[6] if len(self.nurse) > 6 else "Nurse"
        staff_type_index = self.staff_type_input.findText(staff_type)
        if staff_type_index >= 0:
            self.staff_type_input.setCurrentIndex(staff_type_index)
        self.unit_input.setText(self.nurse[7] if len(self.nurse) > 7 else "")
        if len(self.nurse) > 8 and self.nurse[8]:
            self.show_profile_photo(self.nurse[8])

    def choose_profile_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose staff profile picture",
            "",
            "Image files (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not file_path:
            return

        reader = QImageReader(file_path)
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            QMessageBox.warning(
                self,
                "Invalid picture",
                f"Could not read this image:\n{reader.errorString()}",
            )
            return

        image = image.scaled(
            512,
            512,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        encoded = QByteArray()
        buffer = QBuffer(encoded)
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            QMessageBox.critical(
                self,
                "Picture error",
                "Could not prepare the selected picture.",
            )
            return
        saved = image.save(buffer, "JPEG", 82)
        buffer.close()
        if not saved:
            QMessageBox.warning(
                self,
                "Picture error",
                "Could not convert the selected picture to JPEG.",
            )
            return

        self.profile_photo = bytes(encoded)
        self.remove_profile_photo = False
        self.show_profile_photo(self.profile_photo)

    def show_profile_photo(self, photo_bytes):
        pixmap = QPixmap()
        if not pixmap.loadFromData(photo_bytes):
            self.photo_preview.setText("Picture unavailable")
            return
        self.photo_preview.setPixmap(
            pixmap.scaled(
                self.photo_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.photo_preview.setStyleSheet(
            "background: #F2F4F7; border: 1px solid #D0D5DD; "
            "border-radius: 56px;"
        )

    def clear_profile_photo(self):
        self.profile_photo = None
        self.remove_profile_photo = self.nurse is not None
        self.photo_preview.setPixmap(QPixmap())
        self.photo_preview.setText("No profile picture")

    def save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "Invalid Staff Member",
                "Please enter the staff member's name.",
            )
            self.name_input.setFocus()
            return

        if not self.unit_input.text().strip():
            QMessageBox.warning(
                self,
                "Invalid Staff Member",
                "Please enter the staff member's unit.",
            )
            self.unit_input.setFocus()
            return

        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "staff_id": self.nurse[2] if self.nurse is not None else "",
            "phone": self.phone_input.text().strip(),
            "status": self.status_input.currentText(),
            "rotation_position": (
                None
                if self.staff_type_input.currentText() in {
                    "Janitor",
                    "Admin",
                    "Lab Tech",
                    "Front Desk",
                }
                else self.rotation_input.currentData()
            ),
            "staff_type": self.staff_type_input.currentText(),
            "unit": self.unit_input.text().strip(),
            "profile_photo": self.profile_photo,
            "remove_profile_photo": self.remove_profile_photo,
        }