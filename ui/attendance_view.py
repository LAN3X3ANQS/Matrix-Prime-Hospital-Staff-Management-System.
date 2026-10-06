from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox
)

from attendance.attendance import check_in_nurse


class AttendanceView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("NurseRoster - Attendance")
        self.resize(700, 500)

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        main_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        title = QLabel("Nurse Attendance")

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet("""
            font-size: 30px;
            font-weight: bold;
            margin-top: 30px;
            margin-bottom: 20px;
        """)

        instruction = QLabel(
            "Enter your Staff ID to record attendance."
        )

        instruction.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        instruction.setStyleSheet("""
            font-size: 16px;
            margin-bottom: 15px;
        """)

        input_layout = QHBoxLayout()

        self.staff_id_input = QLineEdit()

        self.staff_id_input.setPlaceholderText(
            "Enter Staff ID"
        )

        self.staff_id_input.setMinimumHeight(45)

        self.staff_id_input.setStyleSheet("""
            font-size: 18px;
            padding: 8px;
        """)

        self.check_in_button = QPushButton(
            "Check In"
        )

        self.check_in_button.setMinimumHeight(45)

        self.check_in_button.setMinimumWidth(120)

        self.check_in_button.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
        """)

        input_layout.addWidget(
            self.staff_id_input
        )

        input_layout.addWidget(
            self.check_in_button
        )

        self.result_label = QLabel("")

        self.result_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.result_label.setWordWrap(True)

        self.result_label.setStyleSheet("""
            font-size: 18px;
            margin-top: 30px;
        """)

        self.check_in_button.clicked.connect(
            self.check_in
        )

        self.staff_id_input.returnPressed.connect(
            self.check_in
        )

        main_layout.addWidget(title)
        main_layout.addWidget(instruction)
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.result_label)

        self.setLayout(main_layout)

    def check_in(self):
        staff_id = self.staff_id_input.text().strip()

        result = check_in_nurse(
            staff_id
        )

        if not result["success"]:
            self.result_label.setText(
                f"❌ {result['message']}"
            )

            self.result_label.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                margin-top: 30px;
            """)

            return

        nurse = result["nurse"]
        shift = result["shift"]
        attendance_time = result["time"]

        self.result_label.setText(
            f"✓ {result['message']}\n\n"
            f"Name: {nurse[1]}\n"
            f"Staff ID: {nurse[2]}\n"
            f"Shift: {shift}\n"
            f"Time: {attendance_time}"
        )

        self.result_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            margin-top: 30px;
        """)

        self.staff_id_input.clear()
        self.staff_id_input.setFocus()

