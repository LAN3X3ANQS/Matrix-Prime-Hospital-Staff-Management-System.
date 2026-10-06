from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox
)

from PySide6.QtCore import QDate

from database.database import get_attendance_by_date_range


class AttendanceHistoryView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "NurseRoster - Attendance History"
        )

        self.resize(900, 550)

        self.setup_ui()
        self.load_attendance()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Attendance History")

        title.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )

        filter_layout = QHBoxLayout()

        from_label = QLabel("From:")

        self.start_date_input = QDateEdit()

        self.start_date_input.setCalendarPopup(True)

        self.start_date_input.setDate(
            QDate.currentDate()
        )

        to_label = QLabel("To:")

        self.end_date_input = QDateEdit()

        self.end_date_input.setCalendarPopup(True)

        self.end_date_input.setDate(
            QDate.currentDate()
        )

        self.search_button = QPushButton("Search")

        self.search_button.clicked.connect(
            self.load_attendance
        )

        filter_layout.addWidget(from_label)

        filter_layout.addWidget(
            self.start_date_input
        )

        filter_layout.addWidget(to_label)

        filter_layout.addWidget(
            self.end_date_input
        )

        filter_layout.addWidget(
            self.search_button
        )

        filter_layout.addStretch()

        self.table = QTableWidget()

        self.table.setColumnCount(6)

        self.table.setHorizontalHeaderLabels([
            "Date",
            "Name",
            "Staff ID",
            "Time",
            "Status",
            "Record ID"
        ])

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.horizontalHeader().setStretchLastSection(
            True
        )

        self.summary_label = QLabel()

        self.summary_label.setStyleSheet(
            "font-size: 14px; margin-top: 5px;"
        )

        main_layout.addWidget(title)

        main_layout.addLayout(
            filter_layout
        )

        main_layout.addWidget(
            self.table
        )

        main_layout.addWidget(
            self.summary_label
        )

        self.setLayout(main_layout)

    def load_attendance(self):
        start_date = self.start_date_input.date().toString(
            "yyyy-MM-dd"
        )

        end_date = self.end_date_input.date().toString(
            "yyyy-MM-dd"
        )

        if start_date > end_date:
            QMessageBox.warning(
                self,
                "Invalid Date Range",
                "The start date cannot be after the end date."
            )
            return

        attendance = get_attendance_by_date_range(
            start_date,
            end_date
        )

        self.table.setRowCount(
            len(attendance)
        )

        for row, record in enumerate(attendance):

            values = [
                record[4],
                record[2],
                record[3],
                record[5] or "",
                record[6],
                str(record[0])
            ]

            for column, value in enumerate(values):

                item = QTableWidgetItem(
                    str(value)
                )

                self.table.setItem(
                    row,
                    column,
                    item
                )

        self.table.resizeColumnsToContents()

        self.summary_label.setText(
            f"{len(attendance)} attendance record(s) found."
        )