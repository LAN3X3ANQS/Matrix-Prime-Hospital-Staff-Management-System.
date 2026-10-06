from PySide6.QtCore import QDate
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

from analytics.attendance_analytics import (
    get_attendance_summary
)


class AnalyticsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "NurseRoster - Analytics"
        )

        self.resize(
            1000,
            650
        )

        self.setup_ui()

        self.load_analytics()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel(
            "Attendance Analytics"
        )

        title.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )

        filter_layout = QHBoxLayout()

        from_label = QLabel("From:")

        self.start_date_input = QDateEdit()

        self.start_date_input.setCalendarPopup(
            True
        )

        self.start_date_input.setDate(
            QDate.currentDate()
        )

        to_label = QLabel("To:")

        self.end_date_input = QDateEdit()

        self.end_date_input.setCalendarPopup(
            True
        )

        self.end_date_input.setDate(
            QDate.currentDate()
        )

        self.generate_button = QPushButton(
            "Generate Analytics"
        )

        self.generate_button.clicked.connect(
            self.load_analytics
        )

        filter_layout.addWidget(
            from_label
        )

        filter_layout.addWidget(
            self.start_date_input
        )

        filter_layout.addWidget(
            to_label
        )

        filter_layout.addWidget(
            self.end_date_input
        )

        filter_layout.addWidget(
            self.generate_button
        )

        filter_layout.addStretch()

        self.summary_label = QLabel()

        self.summary_label.setStyleSheet(
            "font-size: 16px; margin: 10px 0;"
        )

        self.table = QTableWidget()

        self.table.setColumnCount(
            7
        )

        self.table.setHorizontalHeaderLabels([
            "Name",
            "Staff ID",
            "Scheduled Shifts",
            "Present",
            "Absent",
            "Approved Leave",
            "Attendance Rate"
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

        main_layout.addWidget(
            title
        )

        main_layout.addLayout(
            filter_layout
        )

        main_layout.addWidget(
            self.summary_label
        )

        main_layout.addWidget(
            self.table
        )

        self.setLayout(
            main_layout
        )

    def load_analytics(self):
        start_date = self.start_date_input.date()

        end_date = self.end_date_input.date()

        if start_date > end_date:
            QMessageBox.warning(
                self,
                "Invalid Date Range",
                "The start date cannot be after the end date."
            )
            return

        start = start_date.toPython()

        end = end_date.toPython()

        try:
            summary = get_attendance_summary(
                start,
                end
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Date Range",
                str(error)
            )
            return

        self.summary_label.setText(
            f"Scheduled: {summary['scheduled_shifts']}  |  "
            f"Present: {summary['present']}  |  "
            f"Absent: {summary['absent']}  |  "
            f"Approved Leave: {summary['approved_leave']}  |  "
            f"Attendance Rate: "
            f"{summary['attendance_rate']:.1f}%"
        )

        nurses = summary["nurses"]

        self.table.setRowCount(
            len(nurses)
        )

        for row, nurse in enumerate(
            nurses
        ):
            values = [
                nurse["name"],
                nurse["staff_id"],
                nurse["scheduled_shifts"],
                nurse["present"],
                nurse["absent"],
                nurse["approved_leave"],
                f"{nurse['attendance_rate']:.1f}%"
            ]

            for column, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(value)
                )

                self.table.setItem(
                    row,
                    column,
                    item
                )

        self.table.resizeColumnsToContents()