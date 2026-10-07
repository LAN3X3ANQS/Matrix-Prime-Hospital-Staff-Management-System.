from datetime import date
from PySide6.QtCore import Qt, QDate
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
    QMessageBox,
    QFrame,
    QHeaderView,
)
from database.database import get_active_nurses
from roster.scheduler import generate_roster


class RosterView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Matrix Prime Hospital - Roster")

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(28, 24, 28, 28)

        main_layout.setSpacing(18)

        section_info = QVBoxLayout()

        section_info.setSpacing(3)

        title = QLabel("Staff Roster")

        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #0B3B82;
        """)

        description = QLabel(
            "Generate and view the rotating duty schedule for all active staff."
        )

        description.setStyleSheet("""
            font-size: 13px;
            color: #718096;
        """)

        section_info.addWidget(title)

        section_info.addWidget(description)

        main_layout.addLayout(section_info)

        controls_frame = QFrame()

        controls_frame.setStyleSheet("""
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

        controls_layout = QHBoxLayout()

        controls_layout.setContentsMargins(14, 12, 14, 12)

        controls_layout.setSpacing(10)

        start_label = QLabel("Start Date")

        self.start_date_input = QDateEdit()

        self.start_date_input.setCalendarPopup(True)

        self.start_date_input.setDate(QDate.currentDate())

        self.start_date_input.setDisplayFormat("dd MMM yyyy")

        self.start_date_input.setMinimumWidth(130)

        days_label = QLabel("Days")

        self.days_input = QSpinBox()

        self.days_input.setMinimum(1)

        self.days_input.setMaximum(31)

        self.days_input.setValue(7)

        self.days_input.setMinimumWidth(80)

        self.generate_button = QPushButton("Generate Roster")

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

        self.generate_button.clicked.connect(self.generate_roster_view)

        controls_layout.addWidget(start_label)

        controls_layout.addWidget(self.start_date_input)

        controls_layout.addSpacing(8)

        controls_layout.addWidget(days_label)

        controls_layout.addWidget(self.days_input)

        controls_layout.addSpacing(8)

        controls_layout.addWidget(self.generate_button)

        controls_layout.addStretch()

        controls_frame.setLayout(controls_layout)

        main_layout.addWidget(controls_frame)

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
                color: #0B3B82;
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

    def generate_roster_view(self):
        nurses = get_active_nurses()

        start_qdate = self.start_date_input.date()

        start_date = date(
            start_qdate.year(),
            start_qdate.month(),
            start_qdate.day(),
        )

        number_of_days = self.days_input.value()

        roster = generate_roster(nurses, start_date, number_of_days)

        self.table.setColumnCount(1 + len(nurses))

        headers = ["Date"]

        for nurse in nurses:
            headers.append(
                f"{nurse[1]} · {nurse[6]} · {nurse[7]}"
            )

        self.table.setHorizontalHeaderLabels(headers)

        self.table.setRowCount(len(roster))

        for row, day_roster in enumerate(roster):
            date_item = QTableWidgetItem(
                day_roster["date"].strftime("%a, %d %b %Y")
            )

            self.table.setItem(row, 0, date_item)

            for column, nurse_entry in enumerate(
                day_roster["nurses"], start=1
            ):
                shift = nurse_entry["shift"]

                shift_item = QTableWidgetItem(shift)

                shift_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                if shift == "Morning":
                    shift_item.setForeground(Qt.GlobalColor.darkGreen)

                elif shift == "Night":
                    shift_item.setForeground(Qt.GlobalColor.darkBlue)

                elif shift == "Off":
                    shift_item.setForeground(Qt.GlobalColor.gray)

                self.table.setItem(row, column, shift_item)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        for column in range(1, self.table.columnCount()):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.Stretch,
            )

        self.table.resizeRowsToContents()