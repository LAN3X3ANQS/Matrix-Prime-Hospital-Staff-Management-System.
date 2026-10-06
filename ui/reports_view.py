from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox
)

from analytics.attendance_analytics import (
    get_attendance_summary
)

from analytics.roster_analytics import (
    get_roster_summary
)

from records.leave_records import (
    get_leave_records
)

from records.shift_records import (
    get_shift_records
)

from ui.export_dialog import ExportDialog


class ReportsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "NurseRoster - Reports"
        )

        self.resize(
            1100,
            650
        )

        self.current_headers = []
        self.current_rows = []
        self.current_report_title = ""

        self.setup_ui()

        self.load_report()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel(
            "Reports"
        )

        title.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )

        filter_layout = QHBoxLayout()

        from_label = QLabel(
            "From:"
        )

        self.start_date_input = QDateEdit()

        self.start_date_input.setCalendarPopup(
            True
        )

        self.start_date_input.setDate(
            QDate.currentDate()
        )

        to_label = QLabel(
            "To:"
        )

        self.end_date_input = QDateEdit()

        self.end_date_input.setCalendarPopup(
            True
        )

        self.end_date_input.setDate(
            QDate.currentDate()
        )

        report_label = QLabel(
            "Report:"
        )

        self.report_input = QComboBox()

        self.report_input.addItem(
            "Attendance Report",
            "attendance"
        )

        self.report_input.addItem(
            "Roster Report",
            "roster"
        )

        self.report_input.addItem(
            "Leave Report",
            "leave"
        )

        self.report_input.addItem(
            "Shift Changes Report",
            "shift"
        )

        self.report_input.currentIndexChanged.connect(
            self.load_report
        )

        self.generate_button = QPushButton(
            "Generate Report"
        )

        self.generate_button.clicked.connect(
            self.load_report
        )

        self.export_button = QPushButton(
            "Export Report"
        )

        self.export_button.clicked.connect(
            self.export_report
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
            report_label
        )

        filter_layout.addWidget(
            self.report_input
        )

        filter_layout.addWidget(
            self.generate_button
        )

        filter_layout.addWidget(
            self.export_button
        )

        filter_layout.addStretch()

        self.summary_label = QLabel()

        self.summary_label.setStyleSheet(
            "font-size: 16px; margin: 10px 0;"
        )

        self.table = QTableWidget()

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

    def load_report(self):
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

        report_type = self.report_input.currentData()

        try:
            if report_type == "attendance":
                self.load_attendance_report(
                    start,
                    end
                )

            elif report_type == "roster":
                self.load_roster_report(
                    start,
                    end
                )

            elif report_type == "leave":
                self.load_leave_report(
                    start,
                    end
                )

            elif report_type == "shift":
                self.load_shift_report(
                    start,
                    end
                )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Report Error",
                str(error)
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Report Error",
                f"Could not generate the report:\n\n{error}"
            )

    def load_attendance_report(
        self,
        start_date,
        end_date
    ):
        report = get_attendance_summary(
            start_date,
            end_date
        )

        self.current_report_title = (
            "Attendance Report"
        )

        self.current_headers = [
            "Name",
            "Staff ID",
            "Scheduled Shifts",
            "Present",
            "Absent",
            "Approved Leave",
            "Attendance Rate"
        ]

        self.current_rows = []

        for nurse in report["nurses"]:
            self.current_rows.append([
                nurse["name"],
                nurse["staff_id"],
                nurse["scheduled_shifts"],
                nurse["present"],
                nurse["absent"],
                nurse["approved_leave"],
                f"{nurse['attendance_rate']:.1f}%"
            ])

        self.display_report(
            self.current_headers,
            self.current_rows
        )

        self.summary_label.setText(
            f"Attendance Report  |  "
            f"Scheduled: {report['scheduled_shifts']}  |  "
            f"Present: {report['present']}  |  "
            f"Absent: {report['absent']}  |  "
            f"Approved Leave: {report['approved_leave']}  |  "
            f"Rate: {report['attendance_rate']:.1f}%"
        )

    def load_roster_report(
        self,
        start_date,
        end_date
    ):
        report = get_roster_summary(
            start_date,
            end_date
        )

        self.current_report_title = (
            "Roster Report"
        )

        self.current_headers = [
            "Name",
            "Staff ID",
            "Morning",
            "Night",
            "Off",
            "Total Scheduled"
        ]

        self.current_rows = []

        for nurse in report["nurses"]:
            total_scheduled = (
                nurse["morning"]
                + nurse["night"]
            )

            self.current_rows.append([
                nurse["name"],
                nurse["staff_id"],
                nurse["morning"],
                nurse["night"],
                nurse["off"],
                total_scheduled
            ])

        self.display_report(
            self.current_headers,
            self.current_rows
        )

        self.summary_label.setText(
            f"Roster Report  |  "
            f"Days: {report['total_days']}  |  "
            f"Morning: {report['morning_shifts']}  |  "
            f"Night: {report['night_shifts']}  |  "
            f"Off: {report['off_days']}"
        )

    def load_leave_report(
        self,
        start_date,
        end_date
    ):
        records = get_leave_records(
            start_date.isoformat(),
            end_date.isoformat()
        )

        self.current_report_title = (
            "Leave Report"
        )

        self.current_headers = [
            "Nurse",
            "Staff ID",
            "Start Date",
            "End Date",
            "Reason",
            "Status"
        ]

        self.current_rows = []

        for record in records:
            self.current_rows.append([
                record[2],
                record[3],
                record[4],
                record[5],
                record[6] or "",
                record[7]
            ])

        self.display_report(
            self.current_headers,
            self.current_rows
        )

        self.summary_label.setText(
            f"Leave Report  |  "
            f"{len(records)} record(s)"
        )

    def load_shift_report(
        self,
        start_date,
        end_date
    ):
        records = get_shift_records(
            start_date.isoformat(),
            end_date.isoformat()
        )

        self.current_report_title = (
            "Shift Changes Report"
        )

        self.current_headers = [
            "Nurse",
            "Staff ID",
            "Date",
            "Original Shift",
            "New Shift",
            "Reason",
            "Created At"
        ]

        self.current_rows = []

        for record in records:
            self.current_rows.append([
                record[2],
                record[3],
                record[4],
                record[5],
                record[6],
                record[7] or "",
                record[8]
            ])

        self.display_report(
            self.current_headers,
            self.current_rows
        )

        self.summary_label.setText(
            f"Shift Changes Report  |  "
            f"{len(records)} record(s)"
        )

    def display_report(
        self,
        headers,
        rows
    ):
        self.table.setColumnCount(
            len(headers)
        )

        self.table.setHorizontalHeaderLabels(
            headers
        )

        self.table.setRowCount(
            len(rows)
        )

        for row, values in enumerate(
            rows
        ):
            for column, value in enumerate(
                values
            ):
                self.table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        str(value)
                    )
                )

        self.table.resizeColumnsToContents()

    def export_report(self):
        if not self.current_headers:
            QMessageBox.warning(
                self,
                "No Report",
                "Generate a report before exporting."
            )
            return

        dialog = ExportDialog(
            title=self.current_report_title,
            headers=self.current_headers,
            rows=self.current_rows,
            parent=self
        )

        dialog.exec()