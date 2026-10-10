from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFrame,
    QHeaderView,
)
from database.database import get_attendance_by_date_range


class AttendanceHistoryView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Matrix Prime Hospital - Attendance History")

        self.setup_ui()
        self.load_attendance()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(28, 24, 28, 28)

        main_layout.setSpacing(18)

        section_info = QVBoxLayout()

        section_info.setSpacing(3)

        title = QLabel("Attendance History")

        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #0B3B82;
        """)

        description = QLabel(
            "Search and review attendance records for all staff categories."
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

        self.search_button = QPushButton("Search")

        self.search_button.setCursor(Qt.PointingHandCursor)

        self.search_button.setStyleSheet("""
            QPushButton {
                background: #0B3B82;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 20px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #154D9E;
            }

            QPushButton:pressed {
                background: #072554;
            }
        """)

        self.search_button.clicked.connect(self.load_attendance)

        filter_layout.addWidget(from_label)

        filter_layout.addWidget(self.start_date_input)

        filter_layout.addSpacing(8)

        filter_layout.addWidget(to_label)

        filter_layout.addWidget(self.end_date_input)

        filter_layout.addSpacing(8)

        filter_layout.addWidget(self.search_button)

        filter_layout.addStretch()

        filter_frame.setLayout(filter_layout)

        main_layout.addWidget(filter_frame)

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

        self.table.setColumnCount(11)

        self.table.setHorizontalHeaderLabels([
            "Date",
            "Name",
            "Staff type",
            "Unit",
            "Staff ID",
            "Shift",
            "Sign-in",
            "Sign-out",
            "Status",
            "Departure",
            "Record ID",
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

        summary_frame = QFrame()

        summary_frame.setStyleSheet("""
            QFrame {
                background: #F5FAFD;
                border: 1px solid #DCEAF3;
                border-radius: 8px;
            }
        """)

        summary_layout = QHBoxLayout()

        summary_layout.setContentsMargins(14, 10, 14, 10)

        self.summary_label = QLabel()

        self.summary_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #526779;
        """)

        summary_layout.addWidget(self.summary_label)

        summary_layout.addStretch()

        summary_frame.setLayout(summary_layout)

        main_layout.addWidget(summary_frame)

        self.setLayout(main_layout)

    def load_attendance(self):
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")

        end_date = self.end_date_input.date().toString("yyyy-MM-dd")

        if start_date > end_date:
            QMessageBox.warning(
                self,
                "Invalid Date Range",
                "The start date cannot be after the end date.",
            )

            return

        attendance = get_attendance_by_date_range(start_date, end_date)

        self.table.setRowCount(len(attendance))

        for row, record in enumerate(attendance):
            values = [
                record[4],
                record[2],
                record[7],
                record[10],
                record[3],
                record[8],
                record[5] or "",
                record[9] or "Not signed out",
                record[6],
                record[11] or "",
                str(record[0]),
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column in (0, 2, 3, 4, 5, 6, 7, 8, 9, 10):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                if column == 8:
                    item.setForeground(
                        Qt.GlobalColor.darkGreen
                        if record[6] == "Present"
                        else Qt.GlobalColor.darkYellow
                    )
                if column == 9 and record[11] == "Early":
                    item.setForeground(Qt.GlobalColor.darkYellow)
                elif column == 9 and record[11] == "On time":
                    item.setForeground(Qt.GlobalColor.darkGreen)

                self.table.setItem(row, column, item)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in range(2, 11):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        self.table.resizeRowsToContents()

        self.summary_label.setText(
            f"{len(attendance)} attendance record(s) found."
        )