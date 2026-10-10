import sqlite3

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QWidget,
)
from database.database import (
    get_active_nurses,
    get_attendance_by_date_range,
)
from records.leave_records import get_leave_records
from records.shift_records import get_shift_records
from roster.scheduler import generate_roster
from ui.export_dialog import ExportDialog


class ExportView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(18)

        description = QLabel(
            "Export roster, attendance, leave, or shift data for a selected date range."
        )
        description.setObjectName("export_description")
        description.setWordWrap(True)
        layout.addWidget(description)

        card = QFrame()
        card.setObjectName("export_card")
        form = QFormLayout(card)
        form.setContentsMargins(22, 20, 22, 20)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(14)

        self.dataset_input = QComboBox()
        self.dataset_input.addItem("Staff roster", "roster")
        self.dataset_input.addItem("Attendance", "attendance")
        self.dataset_input.addItem("Leave records", "leave")
        self.dataset_input.addItem("Shift changes", "shifts")
        form.addRow("Dataset", self.dataset_input)

        self.start_date_input = self.create_date_input()
        self.end_date_input = self.create_date_input()
        form.addRow("From", self.start_date_input)
        form.addRow("To", self.end_date_input)

        button_row = QHBoxLayout()
        button_row.addStretch()
        export_button = QPushButton("Choose format and export")
        export_button.setMinimumHeight(40)
        export_button.setCursor(Qt.CursorShape.PointingHandCursor)
        export_button.clicked.connect(self.export_data)
        button_row.addWidget(export_button)
        form.addRow("", button_row)

        layout.addWidget(card)
        layout.addStretch()
        self.setStyleSheet("""
            QLabel#export_description {
                color: #667085;
                font-size: 13px;
            }
            QFrame#export_card {
                background: #FFFFFF;
                border: 1px solid #E4E7EC;
                border-radius: 10px;
            }
        """)

    @staticmethod
    def create_date_input():
        widget = QDateEdit()
        widget.setCalendarPopup(True)
        widget.setDate(QDate.currentDate())
        widget.setDisplayFormat("dd MMM yyyy")
        return widget

    def export_data(self):
        start_date = self.start_date_input.date().toPython()
        end_date = self.end_date_input.date().toPython()
        if start_date > end_date:
            QMessageBox.warning(
                self,
                "Invalid date range",
                "The start date must not be after the end date.",
            )
            return

        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()
        dataset = self.dataset_input.currentData()
        try:
            title, headers, rows = self.get_dataset(
                dataset,
                start_date,
                end_date,
                start_iso,
                end_iso,
            )
        except (ValueError, OSError, sqlite3.Error) as error:
            QMessageBox.critical(
                self,
                "Could not prepare export",
                str(error),
            )
            return

        dialog = ExportDialog(title, headers, rows, self)
        dialog.exec()

    @staticmethod
    def get_dataset(dataset, start_date, end_date, start_iso, end_iso):
        if dataset == "roster":
            headers = ["Date", "Staff member", "Staff ID", "Staff type", "Shift"]
            rows = []
            roster = generate_roster(
                get_active_nurses(),
                start_date,
                (end_date - start_date).days + 1,
            )
            for day_roster in roster:
                for assignment in day_roster["nurses"]:
                    nurse = assignment["nurse"]
                    rows.append((
                        day_roster["date"].isoformat(),
                        nurse[1],
                        nurse[2],
                        nurse[6],
                        assignment["shift"],
                    ))
            return "Staff roster", headers, rows

        if dataset == "attendance":
            rows = get_attendance_by_date_range(start_iso, end_iso)
            return (
                "Attendance",
                [
                    "Record ID",
                    "Staff record ID",
                    "Staff member",
                    "Staff ID",
                    "Date",
                    "Sign-in",
                    "Attendance status",
                    "Staff type",
                    "Unit",
                    "Shift",
                    "Sign-out",
                    "Departure status",
                ],
                [
                    (
                        record[0],
                        record[1],
                        record[2],
                        record[3],
                        record[4],
                        record[5],
                        record[6],
                        record[7],
                        record[10],
                        record[8],
                        record[9],
                        record[11],
                    )
                    for record in rows
                ],
            )

        if dataset == "leave":
            rows = get_leave_records(start_iso, end_iso)
            return (
                "Leave records",
                ["Record ID", "Staff record ID", "Staff member", "Staff ID", "Start date", "End date", "Reason", "Status", "Staff type"],
                rows,
            )

        if dataset == "shifts":
            rows = get_shift_records(start_iso, end_iso)
            return (
                "Shift changes",
                ["Record ID", "Staff record ID", "Staff member", "Staff ID", "Date", "Original shift", "New shift", "Reason", "Created at", "Staff type"],
                rows,
            )

        raise ValueError(f"Unsupported export dataset: {dataset}")
