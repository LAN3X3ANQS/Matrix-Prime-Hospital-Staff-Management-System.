from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget
)

from ui.nurses_view import NursesView
from ui.roster_view import RosterView
from ui.attendance_view import AttendanceView
from ui.attendance_history_view import AttendanceHistoryView
from ui.analytics_view import AnalyticsView
from ui.reports_view import ReportsView
from ui.leave_records_view import LeaveRecordsView
from ui.shift_records_view import ShiftRecordsView


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "NurseRoster"
        )

        self.resize(
            1100,
            650
        )

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()

        main_layout = QVBoxLayout()

        navigation_layout = QHBoxLayout()

        self.nurses_button = QPushButton(
            "Nurses"
        )

        self.roster_button = QPushButton(
            "Roster"
        )

        self.attendance_button = QPushButton(
            "Attendance"
        )

        self.history_button = QPushButton(
            "Attendance History"
        )

        self.analytics_button = QPushButton(
            "Analytics"
        )

        self.reports_button = QPushButton(
            "Reports"
        )

        self.leave_button = QPushButton(
            "Leave Records"
        )

        self.shift_button = QPushButton(
            "Shift Changes"
        )

        self.nurses_button.clicked.connect(
            self.show_nurses
        )

        self.roster_button.clicked.connect(
            self.show_roster
        )

        self.attendance_button.clicked.connect(
            self.show_attendance
        )

        self.history_button.clicked.connect(
            self.show_attendance_history
        )

        self.analytics_button.clicked.connect(
            self.show_analytics
        )

        self.reports_button.clicked.connect(
            self.show_reports
        )

        self.leave_button.clicked.connect(
            self.show_leave_records
        )

        self.shift_button.clicked.connect(
            self.show_shift_records
        )

        navigation_layout.addWidget(
            self.nurses_button
        )

        navigation_layout.addWidget(
            self.roster_button
        )

        navigation_layout.addWidget(
            self.attendance_button
        )

        navigation_layout.addWidget(
            self.history_button
        )

        navigation_layout.addWidget(
            self.analytics_button
        )

        navigation_layout.addWidget(
            self.reports_button
        )

        navigation_layout.addWidget(
            self.leave_button
        )

        navigation_layout.addWidget(
            self.shift_button
        )

        navigation_layout.addStretch()

        self.pages = QStackedWidget()

        self.nurses_view = NursesView()

        self.roster_view = RosterView()

        self.attendance_view = AttendanceView()

        self.attendance_history_view = (
            AttendanceHistoryView()
        )

        self.analytics_view = AnalyticsView()

        self.reports_view = ReportsView()

        self.leave_records_view = (
            LeaveRecordsView()
        )

        self.shift_records_view = (
            ShiftRecordsView()
        )

        self.pages.addWidget(
            self.nurses_view
        )

        self.pages.addWidget(
            self.roster_view
        )

        self.pages.addWidget(
            self.attendance_view
        )

        self.pages.addWidget(
            self.attendance_history_view
        )

        self.pages.addWidget(
            self.analytics_view
        )

        self.pages.addWidget(
            self.reports_view
        )

        self.pages.addWidget(
            self.leave_records_view
        )

        self.pages.addWidget(
            self.shift_records_view
        )

        main_layout.addLayout(
            navigation_layout
        )

        main_layout.addWidget(
            self.pages
        )

        central_widget.setLayout(
            main_layout
        )

        self.setCentralWidget(
            central_widget
        )

    def show_nurses(self):
        self.pages.setCurrentWidget(
            self.nurses_view
        )

        self.nurses_view.load_nurses()

    def show_roster(self):
        self.pages.setCurrentWidget(
            self.roster_view
        )

        self.roster_view.generate_roster_view()

    def show_attendance(self):
        self.pages.setCurrentWidget(
            self.attendance_view
        )

        self.attendance_view.staff_id_input.setFocus()

    def show_attendance_history(self):
        self.pages.setCurrentWidget(
            self.attendance_history_view
        )

        self.attendance_history_view.load_attendance()

    def show_analytics(self):
        self.pages.setCurrentWidget(
            self.analytics_view
        )

        self.analytics_view.load_analytics()

    def show_reports(self):
        self.pages.setCurrentWidget(
            self.reports_view
        )

        self.reports_view.load_report()

    def show_leave_records(self):
        self.pages.setCurrentWidget(
            self.leave_records_view
        )

        self.leave_records_view.load_records()

    def show_shift_records(self):
        self.pages.setCurrentWidget(
            self.shift_records_view
        )

        self.shift_records_view.load_records()