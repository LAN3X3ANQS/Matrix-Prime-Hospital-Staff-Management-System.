from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDateEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox
)

from database.database import get_active_nurses
from roster.scheduler import generate_roster


class RosterView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("NurseRoster - Roster")
        self.resize(900, 500)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Nurse Roster")

        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
        """)

        controls_layout = QHBoxLayout()

        start_label = QLabel("Start Date:")

        self.start_date_input = QDateEdit()

        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())

        days_label = QLabel("Days:")

        self.days_input = QSpinBox()

        self.days_input.setMinimum(1)
        self.days_input.setMaximum(31)
        self.days_input.setValue(7)

        self.generate_button = QPushButton("Generate Roster")

        self.generate_button.clicked.connect(
            self.generate_roster_view
        )

        controls_layout.addWidget(start_label)
        controls_layout.addWidget(self.start_date_input)
        controls_layout.addWidget(days_label)
        controls_layout.addWidget(self.days_input)
        controls_layout.addWidget(self.generate_button)
        controls_layout.addStretch()

        self.table = QTableWidget()

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(title)
        layout.addLayout(controls_layout)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def generate_roster_view(self):
        nurses = get_active_nurses()

        if len(nurses) != 3:
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)

            QMessageBox.warning(
                self,
                "Roster Requires 3 Active Nurses",
                f"The current rotation is designed for exactly 3 active nurses.\n\n"
                f"Currently active: {len(nurses)}"
            )

            return

        start_qdate = self.start_date_input.date()

        start_date = date(
            start_qdate.year(),
            start_qdate.month(),
            start_qdate.day()
        )

        number_of_days = self.days_input.value()

        roster = generate_roster(
            nurses,
            start_date,
            number_of_days
        )

        self.table.setColumnCount(1 + len(nurses))

        headers = ["Date"]

        for nurse in nurses:
            headers.append(nurse[1])

        self.table.setHorizontalHeaderLabels(headers)

        self.table.setRowCount(len(roster))

        for row, day_roster in enumerate(roster):
            date_item = QTableWidgetItem(
                day_roster["date"].strftime("%a, %d %b %Y")
            )

            self.table.setItem(row, 0, date_item)

            for column, nurse_entry in enumerate(
                day_roster["nurses"],
                start=1
            ):
                shift_item = QTableWidgetItem(
                    nurse_entry["shift"]
                )

                self.table.setItem(
                    row,
                    column,
                    shift_item
                )

        self.table.resizeColumnsToContents()