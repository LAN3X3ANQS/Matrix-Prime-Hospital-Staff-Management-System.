from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from ui.analytics_view import AnalyticsView
from ui.attendance_history_view import AttendanceHistoryView
from ui.attendance_view import AttendanceView
from ui.dashboard_view import DashboardView
from ui.data_tools_view import DataToolsView
from ui.export_view import ExportView
from ui.leave_records_view import LeaveRecordsView
from ui.nurses_view import NursesView
from ui.reports_view import ReportsView
from ui.roster_view import RosterView
from ui.settings_view import SettingsView
from ui.shift_records_view import ShiftRecordsView
from networking.config import get_client_config


class MainWindow(QMainWindow):
    login_requested = Signal()

    ADMIN_PAGES = {
        "nurses",
        "analytics",
        "reports",
        "leave",
        "shifts",
        "exports",
        "settings",
        "data_tools",
    }

    PAGE_DETAILS = {
        "dashboard": ("Dashboard", "A clear view of today’s operations"),
        "nurses": ("Staff directory", "Manage janitors, nurses, and lab technicians"),
        "roster": ("Roster", "View the workforce duty schedule"),
        "attendance": ("Attendance", "Record a staff check-in using their Staff ID"),
        "history": ("Attendance history", "Review recorded attendance"),
        "analytics": ("Analytics", "Monitor attendance and leave trends"),
        "reports": ("Reports", "Generate and export operational reports"),
        "leave": ("Leave records", "Manage staff leave and absence records"),
        "shifts": ("Shift changes", "Track updates to scheduled shifts"),
        "exports": ("Exports", "Export operational data to a file"),
        "settings": ("Settings", "Manage shared application passwords"),
        "data_tools": ("Data & backups", "Back up or restore this computer's database"),
    }

    def __init__(self, role, lan_server=None):
        super().__init__()
        if role not in {"ADMIN", "STAFF"}:
            raise ValueError("A valid application role is required.")

        self.role = role
        self.lan_server = lan_server
        self.setWindowTitle("Matrix Prime Hospital | Staff Management")
        self.resize(1360, 850)
        self.setMinimumSize(1050, 680)
        self.pages_by_key = {}
        self.navigation_buttons = {}
        self.setup_ui()
        self.apply_styles()
        self.open_page("dashboard")

    def setup_ui(self):
        central = QWidget()
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(238)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 22, 16, 16)
        sidebar_layout.setSpacing(5)

        brand = QLabel("Matrix Prime Hospital")
        brand.setObjectName("brand")
        tagline = QLabel("HOSPITAL OPERATIONS")
        tagline.setObjectName("tagline")
        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(tagline)
        sidebar_layout.addSpacing(28)

        sidebar_layout.addWidget(self.create_section_label("WORKSPACE"))
        navigation = [
            ("dashboard", "Dashboard"),
            ("nurses", "Staff directory"),
            ("roster", "Roster"),
            ("attendance", "Attendance"),
            ("history", "Attendance history"),
            ("analytics", "Analytics"),
            ("reports", "Reports"),
            ("leave", "Leave records"),
            ("shifts", "Shift changes"),
            ("exports", "Exports"),
        ]
        if self.role == "ADMIN":
            for key, label in navigation:
                self.add_navigation_button(sidebar_layout, key, label)
        else:
            for key, label in navigation:
                if key in {"dashboard", "roster", "attendance", "history"}:
                    self.add_navigation_button(sidebar_layout, key, label)

        if self.role == "ADMIN":
            sidebar_layout.addSpacing(14)
            sidebar_layout.addWidget(self.create_section_label("SYSTEM"))
            self.add_navigation_button(sidebar_layout, "data_tools", "Data & backups")
            self.add_navigation_button(sidebar_layout, "settings", "Settings")
        sidebar_layout.addStretch()
        if self.lan_server is not None:
            status_text = "SHARED LAN SERVER\nThis computer hosts the database"
        elif get_client_config() is not None:
            status_text = "CONNECTED TO SERVER\nShared hospital database"
        else:
            status_text = "LOCAL DATABASE\nShared role-based access"
        app_status = QLabel(status_text)
        app_status.setObjectName("sidebar_footer")
        sidebar_layout.addWidget(app_status)

        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 17, 30, 17)

        title_group = QVBoxLayout()
        title_group.setSpacing(2)
        self.page_title = QLabel()
        self.page_title.setObjectName("page_title")
        self.page_description = QLabel()
        self.page_description.setObjectName("page_description")
        title_group.addWidget(self.page_title)
        title_group.addWidget(self.page_description)
        header_layout.addLayout(title_group)
        header_layout.addStretch()

        role_badge = QLabel(self.role)
        role_badge.setObjectName("role_badge")
        header_layout.addWidget(role_badge)
        sign_out = QPushButton("Sign out")
        sign_out.setObjectName("sign_out")
        sign_out.setCursor(Qt.CursorShape.PointingHandCursor)
        sign_out.clicked.connect(self.login_requested.emit)
        header_layout.addWidget(sign_out)

        self.pages = QStackedWidget()
        self.pages.setObjectName("pages")
        self.create_pages()
        content_layout.addWidget(header)
        content_layout.addWidget(self.pages, 1)
        outer.addWidget(self.sidebar)
        outer.addWidget(content, 1)
        self.setCentralWidget(central)

    def create_section_label(self, text):
        label = QLabel(text)
        label.setObjectName("section_label")
        return label

    def add_navigation_button(self, layout, key, text):
        button = QPushButton(text)
        button.setObjectName("nav_button")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(39)
        button.setProperty("active", False)
        button.clicked.connect(lambda checked=False, page=key: self.open_page(page))
        layout.addWidget(button)
        self.navigation_buttons[key] = button

    def create_pages(self):
        factories = {
            "dashboard": lambda: DashboardView(self.role),
            "roster": RosterView,
            "attendance": AttendanceView,
            "history": AttendanceHistoryView,
        }
        if self.role == "ADMIN":
            factories.update({
                "nurses": NursesView,
                "analytics": AnalyticsView,
                "reports": ReportsView,
                "leave": LeaveRecordsView,
                "shifts": ShiftRecordsView,
                "exports": ExportView,
                "settings": lambda: SettingsView(lan_server=self.lan_server),
                "data_tools": DataToolsView,
            })

        for key, factory in factories.items():
            page = factory()
            self.pages.addWidget(page)
            self.pages_by_key[key] = page
    def open_page(self, key):
        if key in self.ADMIN_PAGES and self.role != "ADMIN":
            return
        page = self.pages_by_key.get(key)
        if page is None:
            return

        self.pages.setCurrentWidget(page)
        title, description = self.PAGE_DETAILS[key]
        self.page_title.setText(title)
        self.page_description.setText(description)
        for button_key, button in self.navigation_buttons.items():
            active = button_key == key
            button.setProperty("active", active)
            button.style().unpolish(button)
            button.style().polish(button)
        self.refresh_page(key, page)

    @staticmethod
    def refresh_page(key, page):
        refresh_methods = {
            "dashboard": "load_dashboard",
            "nurses": "load_nurses",
            "roster": "generate_roster_view",
            "history": "load_attendance",
            "analytics": "load_analytics",
            "reports": "load_report",
            "leave": "load_records",
            "shifts": "load_records",
        }
        method_name = refresh_methods.get(key)
        if method_name:
            getattr(page, method_name)()
        if key == "attendance":
            page.staff_id_input.setFocus()

    def show_dashboard(self):
        self.open_page("dashboard")

    def show_nurses(self):
        self.open_page("nurses")

    def show_roster(self):
        self.open_page("roster")

    def show_attendance(self):
        self.open_page("attendance")

    def show_attendance_history(self):
        self.open_page("history")

    def show_analytics(self):
        self.open_page("analytics")

    def show_reports(self):
        self.open_page("reports")

    def show_leave_records(self):
        self.open_page("leave")

    def show_shift_records(self):
        self.open_page("shifts")

    def show_exports(self):
        self.open_page("exports")

    def show_settings(self):
        self.open_page("settings")

    def show_data_tools(self):
        self.open_page("data_tools")

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow, QWidget#content {
                background: #F5F7FA;
            }
            QWidget {
                font-family: "Segoe UI";
                font-size: 13px;
                color: #182230;
            }
            QFrame#sidebar {
                background: #182433;
                border: none;
            }
            QLabel#brand {
                color: #FFFFFF;
                font-size: 21px;
                font-weight: 700;
                padding-left: 8px;
            }
            QLabel#tagline {
                color: #9AA8B8;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 1px;
                padding-left: 9px;
            }
            QLabel#section_label {
                color: #8391A2;
                font-size: 9px;
                font-weight: 700;
                padding: 8px 9px 5px;
            }
            QPushButton#nav_button {
                background: transparent;
                color: #C5CFDA;
                border: none;
                border-radius: 6px;
                padding: 0 11px;
                text-align: left;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton#nav_button:hover {
                background: #253547;
                color: #FFFFFF;
            }
            QPushButton#nav_button[active="true"] {
                background: #2C4055;
                color: #FFFFFF;
                font-weight: 600;
                border-left: 3px solid #53B1A7;
                padding-left: 8px;
            }
            QLabel#sidebar_footer {
                color: #8391A2;
                font-size: 10px;
                line-height: 1.5;
                padding: 10px 8px;
                border-top: 1px solid #2D3A49;
            }
            QFrame#header {
                background: #FFFFFF;
                border: none;
                border-bottom: 1px solid #E4E7EC;
            }
            QLabel#page_title {
                color: #182230;
                font-size: 17px;
                font-weight: 650;
            }
            QLabel#page_description {
                color: #667085;
                font-size: 11px;
            }
            QLabel#role_badge {
                background: #E8F4F2;
                color: #25756C;
                border-radius: 10px;
                padding: 5px 10px;
                font-size: 9px;
                font-weight: 700;
            }
            QPushButton#sign_out {
                background: transparent;
                color: #475467;
                border: 1px solid #D0D5DD;
                border-radius: 6px;
                padding: 7px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#sign_out:hover {
                background: #F2F4F7;
            }
            QStackedWidget#pages {
                background: #F5F7FA;
            }
            QPushButton {
                background: #267D73;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #206C63;
            }
            QPushButton:disabled {
                background: #D0D5DD;
                color: #667085;
            }
            QLineEdit, QDateEdit, QComboBox, QTextEdit {
                background: #FFFFFF;
                color: #182230;
                border: 1px solid #D0D5DD;
                border-radius: 6px;
                padding: 8px 9px;
                selection-background-color: #D9EFEC;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #267D73;
            }
            QTableWidget {
                background: #FFFFFF;
                alternate-background-color: #F9FAFB;
                border: 1px solid #E4E7EC;
                border-radius: 7px;
                gridline-color: #EAECF0;
                selection-background-color: #D9EFEC;
                selection-color: #182230;
            }
            QHeaderView::section {
                background: #F2F4F7;
                color: #475467;
                border: none;
                border-bottom: 1px solid #E4E7EC;
                padding: 9px;
                font-size: 11px;
                font-weight: 600;
            }
        """)
