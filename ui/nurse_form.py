from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)


class NurseForm(QDialog):

    def __init__(self, nurse=None, parent=None):
        super().__init__(parent)

        self.nurse = nurse

        self.setWindowTitle("Nurse")
        self.setFixedSize(400, 300)

        self.setup_ui()

        if nurse is not None:
            self.load_nurse()

    def setup_ui(self):
        layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter nurse name")

        self.staff_id_input = QLineEdit()
        self.staff_id_input.setPlaceholderText("Enter Staff ID")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number")

        self.status_input = QComboBox()
        self.status_input.addItems(["Active", "Inactive"])

        self.rotation_input = QComboBox()

        self.rotation_input.addItem("Rotation 1 (M M N N O O)", 0)
        self.rotation_input.addItem("Rotation 2 (N N O O M M)", 1)
        self.rotation_input.addItem("Rotation 3 (O O M M N N)", 2)

        layout.addRow("Name:", self.name_input)
        layout.addRow("Staff ID:", self.staff_id_input)
        layout.addRow("Phone:", self.phone_input)
        layout.addRow("Status:", self.status_input)
        layout.addRow("Rotation:", self.rotation_input)

        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.save_button = QPushButton("Save")

        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.save)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        layout.addRow(button_layout)

        self.setLayout(layout)

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

    def save(self):
        name = self.name_input.text().strip()
        staff_id = self.staff_id_input.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Invalid Nurse",
                "Please enter the nurse's name.",
            )
            self.name_input.setFocus()
            return

        if not staff_id:
            QMessageBox.warning(
                self,
                "Invalid Nurse",
                "Please enter a Staff ID.",
            )
            self.staff_id_input.setFocus()
            return

        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "staff_id": self.staff_id_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "status": self.status_input.currentText(),
            "rotation_position": self.rotation_input.currentData(),
        }