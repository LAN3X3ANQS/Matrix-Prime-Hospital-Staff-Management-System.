from PySide6.QtCore import Qt, QDate
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
    QMessageBox,
    QFrame,
    QHeaderView,
)
from analytics.attendance_analytics import get_attendance_summary
from analytics.roster_analytics import get_roster_summary
from records.leave_records import get_leave_records
from records.shift_records import get_shift_records
from ui.export_dialog import ExportDialog


class ReportsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Matrix Prime Hospital - Reports")

        self.current_headers = []
        self.current_rows = []
        self.current_report_title = ""

        self.setup_ui()

        self.load_report()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(28, 24, 28, 28)

        main_layout.setSpacing(18)

        section_info = QVBoxLayout()

        section_info.setSpacing(3)

        title = QLabel("Reports")

        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #0B3B82;
        """)

        description = QLabel(
            "Generate, review, and export workforce reports."
        )

        description.setStyleSheet("""
            font-size: 13px;
            color: #718096;
        """)

        section_info.addWidget(title)

        section_info.addWidget(description)

        main_layout.addLayout(section_info)

        filter_frame = QFrame()

        filter_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E1E8EF;
                border-radius: 10px;
            }

            QLabel {
                color: #526779;
                font-weight: 600;
            }
        """)

        filter_layout = QHBoxLayout()

        filter_layout.setContentsMargins(14, 12, 14, 12)

        filter_layout.setSpacing(10)

        from_label = QLabel("From")

        self.start_date_input = QDateEdit()

        self.start_date_input.setCalendarPopup(True)

        self.start_date_input.setDate(QDate.currentDate())

        self.start_date_input.setDisplayFormat("dd MMM yyyy")

        self.start_date_input.setMinimumWidth(130)

        to_label = QLabel("To")

        self.end_date_input = QDateEdit()

        self.end_date_input.setCalendarPopup(True)

        self.end_date_input.setDate(QDate.currentDate())

        self.end_date_input.setDisplayFormat("dd MMM yyyy")

        self.end_date_input.setMinimumWidth(130)

        report_label = QLabel("Report")

        self.report_input = QComboBox()

        self.report_input.addItem("Attendance Report", "attendance")

        self.report_input.addItem("Roster Report", "roster")

        self.report_input.addItem("Leave Report", "leave")

        self.report_input.addItem("Shift Changes Report", "shift")

        self.report_input.setMinimumWidth(160)

        self.report_input.currentIndexChanged.connect(self.load_report)

        self.generate_button = QPushButton("Generate Report")

        self.generate_button.setCursor(Qt.PointingHandCursor)

        self.generate_button.setStyleSheet("""
            QPushButton {
                background: #0B3B82;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #154D9E;
            }

            QPushButton:pressed {
                background: #072554;
            }
        """)

        self.generate_button.clicked.connect(self.load_report)

        self.export_button = QPushButton("Export Report")

        self.export_button.setCursor(Qt.PointingHandCursor)

        self.export_button.setStyleSheet("""
            QPushButton {
                background: #00C853;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #00B048;
            }

            QPushButton:pressed {
                background: #00963E;
            }
        """)

        self.export_button.clicked.connect(self.export_report)

        filter_layout.addWidget(from_label)

        filter_layout.addWidget(self.start_date_input)

        filter_layout.addSpacing(6)

        filter_layout.addWidget(to_label)

        filter_layout.addWidget(self.end_date_input)

        filter_layout.addSpacing(6)

        filter_layout.addWidget(report_label)

        filter_layout.addWidget(self.report_input)

        filter_layout.addSpacing(6)

        filter_layout.addWidget(self.generate_button)

        filter_layout.addWidget(self.export_button)

        filter_layout.addStretch()

        filter_frame.setLayout(filter_layout)

        main_layout.addWidget(filter_frame)

        summary_frame = QFrame()

        summary_frame.setStyleSheet("""
            QFrame {
                background: #F5FAFD;
                border: 1px solid #DCEAF3;
                border-radius: 10px;
            }
        """)

        summary_layout = QHBoxLayout()

        summary_layout.setContentsMargins(16, 12, 16, 12)

        self.summary_label = QLabel()

        self.summary_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #526779;
        """)

        self.summary_label.setWordWrap(True)

        summary_layout.addWidget(self.summary_label)

        summary_layout.addStretch()

        summary_frame.setLayout(summary_layout)

        main_layout.addWidget(summary_frame)

        table_frame = QFrame()

        table_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E1E8EF;
                border-radius: 10px;
            }
        """)

        table_layout = QVBoxLayout()

        table_layout.setContentsMargins(1, 1, 1, 1)

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

        self.table.setAlternatingRowColors(True)

        self.table.verticalHeader().setVisible(False)

        self.table.setShowGrid(False)

        self.table.setStyleSheet("""
            QTableWidget {
                background: white;
                alternate-background-color: #F8FBFD;
                color: #0B3B82;
                border: none;
                border-radius: 9px;
                gridline-color: transparent;
                selection-background-color: #E8F5E9;
                selection-color: #0B3B82;
                outline: none;
            }

            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #EDF2F7;
            }

            QTableWidget::item:selected {
                background: #E8F5E9;
                color: #0B3B82;
            }

            QHeaderView::section {
                background: #F1F6FA;
                color: #526779;
                border: none;
                border-bottom: 1px solid #DCE5EC;
                padding: 11px 10px;
                font-weight: 600;
            }
        """)

        table_layout.addWidget(self.table)

        table_frame.setLayout(table_layout)

        main_layout.addWidget(table_frame)

        self.setLayout(main_layout)

    def load_report(self):
        start_date = self.start_date_input.date()

        end_date = self.end_date_input.date()

        if start_date > end_date:
            QMessageBox.warning(
                self,
                "Invalid Date Range",
                "The start date cannot be after the end date.",
            )

            return

        start = start_date.toPython()

        end = end_date.toPython()

        report_type = self.report_input.currentData()

        try:
            if report_type == "attendance":
                self.load_attendance_report(start, end)

            elif report_type == "roster":
                self.load_roster_report(start, end)

            elif report_type == "leave":
                self.load_leave_report(start, end)

            elif report_type == "shift":
                self.load_shift_report(start, end)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Report Error",
                str(error),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Report Error",
                f"Could not generate the report:\n\n{error}",
            )

    def load_attendance_report(self, start_date, end_date):
        report = get_attendance_summary(start_date, end_date)

        self.current_report_title = "Attendance Report"

        self.current_headers = [
            "Staff type",
            "Name",
            "Staff ID",
            "Scheduled Shifts",
            "Present",
            "Absent",
            "Approved Leave",
            "Attendance Rate",
        ]

        self.current_rows = []

        for nurse in report["nurses"]:
            self.current_rows.append([
                nurse["staff_type"],
                nurse["name"],
                nurse["staff_id"],
                nurse["scheduled_shifts"],
                nurse["present"],
                nurse["absent"],
                nurse["approved_leave"],
                f"{nurse['attendance_rate']:.1f}%",
            ])

        self.display_report(self.current_headers, self.current_rows)

        self.summary_label.setText(
            f"Attendance Report  |  "
            f"Scheduled: {report['scheduled_shifts']}  |  "
            f"Present: {report['present']}  |  "
            f"Absent: {report['absent']}  |  "
            f"Approved Leave: {report['approved_leave']}  |  "
            f"Rate: {report['attendance_rate']:.1f}%"
        )

    def load_roster_report(self, start_date, end_date):
        report = get_roster_summary(start_date, end_date)

        self.current_report_title = "Roster Report"

        self.current_headers = [
            "Staff type",
            "Name",
            "Staff ID",
            "Morning",
            "Night",
            "Off",
            "Total Scheduled",
        ]

        self.current_rows = []

        for nurse in report["nurses"]:
            total_scheduled = nurse["morning"] + nurse["night"]

            self.current_rows.append([
                nurse["staff_type"],
                nurse["name"],
                nurse["staff_id"],
                nurse["morning"],
                nurse["night"],
                nurse["off"],
                total_scheduled,
            ])

        self.display_report(self.current_headers, self.current_rows)

        self.summary_label.setText(
            f"Roster Report  |  "
            f"Days: {report['total_days']}  |  "
            f"Morning: {report['morning_shifts']}  |  "
            f"Night: {report['night_shifts']}  |  "
            f"Off: {report['off_days']}"
        )

    def load_leave_report(self, start_date, end_date):
        records = get_leave_records(
            start_date.isoformat(),
            end_date.isoformat(),
        )

        self.current_report_title = "Leave Report"

        self.current_headers = [
            "Staff member",
            "Staff type",
            "Staff ID",
            "Start Date",
            "End Date",
            "Reason",
            "Status",
        ]

        self.current_rows = []

        for record in records:
            self.current_rows.append([
                record[2],
                record[8],
                record[3],
                record[4],
                record[5],
                record[6] or "",
                record[7],
            ])

        self.display_report(self.current_headers, self.current_rows)

        self.summary_label.setText(
            f"Leave Report  |  {len(records)} record(s)"
        )

    def load_shift_report(self, start_date, end_date):
        records = get_shift_records(
            start_date.isoformat(),
            end_date.isoformat(),
        )

        self.current_report_title = "Shift Changes Report"

        self.current_headers = [
            "Staff member",
            "Staff type",
            "Staff ID",
            "Date",
            "Original Shift",
            "New Shift",
            "Reason",
            "Created At",
        ]

        self.current_rows = []

        for record in records:
            self.current_rows.append([
                record[2],
                record[9],
                record[3],
                record[4],
                record[5],
                record[6],
                record[7] or "",
                record[8],
            ])

        self.display_report(self.current_headers, self.current_rows)

        self.summary_label.setText(
            f"Shift Changes Report  |  {len(records)} record(s)"
        )

    def display_report(self, headers, rows):
        self.table.setColumnCount(len(headers))

        self.table.setHorizontalHeaderLabels(headers)

        self.table.setRowCount(len(rows))

        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column > 1:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.table.setItem(row, column, item)

        header = self.table.horizontalHeader()

        if len(headers) > 0:
            header.setSectionResizeMode(
                0,
                QHeaderView.ResizeMode.Stretch,
            )

        for column in range(1, len(headers)):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        self.table.resizeRowsToContents()

    def export_report(self):
        if not self.current_headers:
            QMessageBox.warning(
                self,
                "No Report",
                "Generate a report before exporting.",
            )

            return

        dialog = ExportDialog(
            title=self.current_report_title,
            headers=self.current_headers,
            rows=self.current_rows,
            parent=self,
        )

        dialog.exec()