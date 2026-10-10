from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
)
from attendance.attendance import check_in_nurse, check_out_nurse


class AttendanceView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Matrix Prime Hospital - Attendance")

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(28, 24, 28, 28)

        main_layout.setSpacing(18)

        header_layout = QVBoxLayout()

        header_layout.setSpacing(3)

        title = QLabel("Staff Attendance")

        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #0B3B82;
        """)

        description = QLabel(
            "Record attendance for any registered staff member using their Staff ID."
        )

        description.setStyleSheet("""
            font-size: 13px;
            color: #718096;
        """)

        header_layout.addWidget(title)

        header_layout.addWidget(description)

        main_layout.addLayout(header_layout)

        attendance_card = QFrame()

        attendance_card.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E1E8EF;
                border-radius: 12px;
            }
        """)

        card_layout = QVBoxLayout()

        card_layout.setContentsMargins(32, 32, 32, 32)

        card_layout.setSpacing(16)

        card_title = QLabel("Shift attendance")

        card_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_title.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #0B3B82;
        """)

        card_instruction = QLabel(
            "Enter the Staff ID of the staff member reporting for duty."
        )

        card_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_instruction.setWordWrap(True)

        card_instruction.setStyleSheet("""
            font-size: 13px;
            color: #718096;
        """)

        input_layout = QHBoxLayout()

        input_layout.setSpacing(10)

        self.staff_id_input = QLineEdit()

        self.staff_id_input.setPlaceholderText("Enter Staff ID")

        self.staff_id_input.setMinimumHeight(44)

        self.staff_id_input.setStyleSheet("""
            QLineEdit {
                background: #F8FBFD;
                color: #0B3B82;
                border: 1px solid #D6E0E8;
                border-radius: 7px;
                padding: 8px 12px;
                font-size: 15px;
            }

            QLineEdit:focus {
                border: 1px solid #00C853;
                background: white;
            }
        """)

        self.check_in_button = QPushButton("Sign In")
        self.check_out_button = QPushButton("Sign Out")

        for button in (self.check_in_button, self.check_out_button):
            button.setMinimumHeight(44)
            button.setMinimumWidth(125)
            button.setCursor(Qt.PointingHandCursor)

        self.check_in_button.setStyleSheet("""
            QPushButton {
                background: #00C853;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 20px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #00B048;
            }

            QPushButton:pressed {
                background: #00963E;
            }
        """)
        self.check_out_button.setStyleSheet("""
            QPushButton {
                background: #1769AA;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 20px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #2380C5;
            }

            QPushButton:pressed {
                background: #125486;
            }
        """)

        input_layout.addWidget(self.staff_id_input)

        input_layout.addWidget(self.check_in_button)
        input_layout.addWidget(self.check_out_button)

        result_frame = QFrame()

        result_frame.setStyleSheet("""
            QFrame {
                background: #F8FBFD;
                border: 1px solid #E1E8EF;
                border-radius: 9px;
            }
        """)

        result_layout = QVBoxLayout()

        result_layout.setContentsMargins(20, 18, 20, 18)

        self.result_label = QLabel(
            "Attendance result will appear here."
        )

        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.result_label.setWordWrap(True)

        self.result_label.setStyleSheet("""
            font-size: 14px;
            color: #718096;
        """)

        result_layout.addWidget(self.result_label)

        result_frame.setLayout(result_layout)

        card_layout.addWidget(card_title)

        card_layout.addWidget(card_instruction)

        card_layout.addSpacing(8)

        card_layout.addLayout(input_layout)

        card_layout.addSpacing(8)

        card_layout.addWidget(result_frame)

        attendance_card.setLayout(card_layout)

        main_layout.addWidget(attendance_card)

        main_layout.addStretch()

        self.check_in_button.clicked.connect(self.check_in)
        self.check_out_button.clicked.connect(self.check_out)

        self.staff_id_input.returnPressed.connect(self.check_in)

        self.setLayout(main_layout)

    def check_in(self):
        staff_id = self.staff_id_input.text().strip()

        result = check_in_nurse(staff_id)

        if not result["success"]:
            self.result_label.setText(f"❌ {result['message']}")

            self.result_label.setStyleSheet("""
                font-size: 15px;
                font-weight: 600;
                color: #B42318;
            """)

            return

        nurse = result["staff"]
        shift = result["shift"]
        attendance_time = result["time"]

        self.result_label.setText(
            f"✓ {result['message']}\n\n"
            f"Name: {nurse[1]}\n"
            f"Staff type: {nurse[6]}\n"
            f"Unit: {nurse[7]}\n"
            f"Staff ID: {nurse[2]}\n"
            f"Shift: {shift}\n"
            f"Time: {attendance_time}"
        )

        self.result_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #00C853;
        """)

        self.staff_id_input.clear()

        self.staff_id_input.setFocus()

    def check_out(self):
        result = check_out_nurse(self.staff_id_input.text().strip())
        if not result["success"]:
            self.result_label.setText(f"Sign-out not recorded\n\n{result['message']}")
            self.result_label.setStyleSheet(
                "font-size: 15px; font-weight: 600; color: #B42318;"
            )
            return

        staff = result["staff"]
        self.result_label.setText(
            f"✓ {result['message']}\n\n"
            f"Name: {staff[1]}\n"
            f"Staff type: {staff[6]}\n"
            f"Unit: {staff[7]}\n"
            f"Staff ID: {staff[2]}\n"
            f"Shift: {result['shift']}\n"
            f"Sign-in: {result['sign_in_time']}\n"
            f"Sign-out: {result['time']} ({result['status']})\n"
            f"Scheduled end: {result['scheduled_end']}"
        )
        result_color = "#A15C07" if result["status"] == "Early" else "#16803C"
        self.result_label.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {result_color};"
        )
        self.staff_id_input.clear()
        self.staff_id_input.setFocus()