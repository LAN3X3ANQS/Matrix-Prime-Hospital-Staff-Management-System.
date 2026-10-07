from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from database.database import get_active_staff
from roster.scheduler import generate_roster


class DashboardView(QWidget):

    def __init__(self, role):
        super().__init__()

        self.role = role

        self.setup_ui()
        self.load_dashboard()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 26, 28, 28)
        main_layout.setSpacing(22)

        welcome_label = QLabel()
        welcome_label.setObjectName("dashboard_welcome")

        if self.role == "ADMIN":
            welcome_label.setText("Welcome back, Admin")
        else:
            welcome_label.setText("Welcome back, Staff")

        main_layout.addWidget(welcome_label)

        description = QLabel(
            "Here is an overview of today's workforce operations."
        )
        description.setObjectName("dashboard_description")

        main_layout.addWidget(description)
        main_layout.addSpacing(6)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)

        self.on_duty_card = self.create_stat_card(
            "Scheduled today",
            "0",
            "Staff assigned to a shift",
        )

        self.active_nurses_card = self.create_stat_card(
            "Active Staff",
            "0",
            "Admins, janitors, nurses, and lab technicians",
        )

        self.night_shift_card = self.create_stat_card(
            "Night shift",
            "0",
            "Staff assigned tonight",
        )

        self.off_duty_card = self.create_stat_card(
            "Off today",
            "0",
            "Staff not scheduled today",
        )

        cards_layout.addWidget(self.on_duty_card, 0, 0)
        cards_layout.addWidget(self.active_nurses_card, 0, 1)
        cards_layout.addWidget(self.night_shift_card, 1, 0)
        cards_layout.addWidget(self.off_duty_card, 1, 1)

        main_layout.addLayout(cards_layout)

        if self.role == "ADMIN":
            information_card = QFrame()
            information_card.setObjectName("dashboard_card")

            information_layout = QVBoxLayout(information_card)
            information_layout.setContentsMargins(22, 20, 22, 20)
            information_layout.setSpacing(8)

            information_title = QLabel("Administration")
            information_title.setObjectName("card_title")

            information_text = QLabel(
                "Use the navigation menu to register and manage staff, "
                "rosters, attendance, leave records, shift changes, "
                "analytics, reports, exports, and backups."
            )
            information_text.setObjectName("card_description")
            information_text.setWordWrap(True)

            information_layout.addWidget(information_title)
            information_layout.addWidget(information_text)

            main_layout.addWidget(information_card)

        else:
            information_card = QFrame()
            information_card.setObjectName("dashboard_card")

            information_layout = QVBoxLayout(information_card)
            information_layout.setContentsMargins(22, 20, 22, 20)
            information_layout.setSpacing(8)

            information_title = QLabel("Staff Operations")
            information_title.setObjectName("card_title")

            information_text = QLabel(
                "Use Attendance to record a staff check-in, "
                "Attendance History to review records for all staff, "
                "and Roster to view the duty schedule."
            )
            information_text.setObjectName("card_description")
            information_text.setWordWrap(True)

            information_layout.addWidget(information_title)
            information_layout.addWidget(information_text)

            main_layout.addWidget(information_card)

        main_layout.addStretch()

        self.setStyleSheet("""
            QWidget {
                font-family: "Segoe UI";
            }

            QLabel#dashboard_welcome {
                color: #0B3B82;
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#dashboard_description {
                color: #718096;
                font-size: 14px;
            }

            QFrame#dashboard_card {
                background: white;
                border: 1px solid #E1E8EF;
                border-radius: 12px;
            }

            QLabel#card_title {
                color: #0B3B82;
                font-size: 16px;
                font-weight: 700;
            }

            QLabel#card_description {
                color: #718096;
                font-size: 13px;
                line-height: 1.4;
            }

            QFrame#stat_card {
                background: white;
                border: 1px solid #E1E8EF;
                border-radius: 12px;
            }

            QLabel#stat_title {
                color: #64748B;
                font-size: 13px;
                font-weight: 600;
            }

            QLabel#stat_value {
                color: #0B3B82;
                font-size: 30px;
                font-weight: 700;
            }

            QLabel#stat_description {
                color: #94A3B8;
                font-size: 11px;
            }
        """)

    def create_stat_card(self, title, value, description):
        card = QFrame()
        card.setObjectName("stat_card")
        card.setMinimumHeight(145)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setObjectName("stat_title")

        value_label = QLabel(value)
        value_label.setObjectName("stat_value")

        description_label = QLabel(description)
        description_label.setObjectName("stat_description")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(description_label)
        layout.addStretch()

        card.value_label = value_label

        return card

    def load_dashboard(self):
        active_staff = get_active_staff()

        active_count = len(active_staff)

        self.active_nurses_card.value_label.setText(
            str(active_count)
        )

        roster = generate_roster(active_staff, date.today(), 1)
        shifts = [
            assignment["shift"]
            for assignment in roster[0]["nurses"]
        ] if roster else []
        self.on_duty_card.value_label.setText(
            str(sum(shift != "Off" for shift in shifts))
        )
        self.night_shift_card.value_label.setText(
            str(shifts.count("Night"))
        )
        self.off_duty_card.value_label.setText(
            str(shifts.count("Off"))
        )