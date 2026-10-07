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
from analytics.attendance_analytics import get_attendance_summary


class AnalyticsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Matrix Prime Hospital - Analytics")

        self.setup_ui()

        self.load_analytics()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(28, 24, 28, 28)

        main_layout.setSpacing(18)

        section_info = QVBoxLayout()

        section_info.setSpacing(3)

        title = QLabel("Attendance Analytics")

        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #0B3B82;
        """)

        description = QLabel(
            "Review attendance performance across a selected date range."
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

        self.generate_button = QPushButton("Generate Analytics")

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

        self.generate_button.clicked.connect(self.load_analytics)

        filter_layout.addWidget(from_label)

        filter_layout.addWidget(self.start_date_input)

        filter_layout.addSpacing(8)

        filter_layout.addWidget(to_label)

        filter_layout.addWidget(self.end_date_input)

        filter_layout.addSpacing(8)

        filter_layout.addWidget(self.generate_button)

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

        summary_layout = QVBoxLayout()

        summary_layout.setContentsMargins(18, 14, 18, 14)

        summary_title = QLabel("Period Summary")

        summary_title.setStyleSheet("""
            font-size: 13px;
            font-weight: 700;
            color: #526779;
        """)

        self.summary_label = QLabel()

        self.summary_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #0B3B82;
        """)

        self.summary_label.setWordWrap(True)

        summary_layout.addWidget(summary_title)

        summary_layout.addWidget(self.summary_label)

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

        self.table.setColumnCount(8)

        self.table.setHorizontalHeaderLabels([
            "Staff type",
            "Name",
            "Staff ID",
            "Scheduled Shifts",
            "Present",
            "Absent",
            "Approved Leave",
            "Attendance Rate",
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

        self.setLayout(main_layout)

    def load_analytics(self):
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

        try:
            summary = get_attendance_summary(start, end)

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Date Range",
                str(error),
            )

            return

        self.summary_label.setText(
            f"Scheduled: {summary['scheduled_shifts']}    |    "
            f"Present: {summary['present']}    |    "
            f"Absent: {summary['absent']}    |    "
            f"Approved Leave: {summary['approved_leave']}    |    "
            f"Attendance Rate: {summary['attendance_rate']:.1f}%"
        )

        nurses = summary["nurses"]

        self.table.setRowCount(len(nurses))

        for row, nurse in enumerate(nurses):
            values = [
                nurse["staff_type"],
                nurse["name"],
                nurse["staff_id"],
                nurse["scheduled_shifts"],
                nurse["present"],
                nurse["absent"],
                nurse["approved_leave"],
                f"{nurse['attendance_rate']:.1f}%",
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column >= 2:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                if column == 7:
                    item.setForeground(Qt.GlobalColor.darkGreen)

                self.table.setItem(row, column, item)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        for column in range(2, 7):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        self.table.resizeRowsToContents()