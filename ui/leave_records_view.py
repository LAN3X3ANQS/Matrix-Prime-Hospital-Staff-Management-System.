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
    QDialog,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QFrame,
    QHeaderView,
)
from database.database import get_nurses
from records.leave_records import (
    create_leave_record,
    get_leave_records,
    update_leave_record,
    delete_leave_record,
)


class LeaveRecordsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Matrix Prime Hospital - Leave Records"
        )

        self.setup_ui()
        self.load_records()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            28,
            24,
            28,
            28
        )

        main_layout.setSpacing(
            18
        )

        section_info = QVBoxLayout()

        section_info.setSpacing(
            3
        )

        title = QLabel(
            "Leave Records"
        )

        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #0B3B82;
        """)

        description = QLabel(
            "Manage leave applications for all staff categories."
        )

        description.setStyleSheet("""
            font-size: 13px;
            color: #718096;
        """)

        section_info.addWidget(
            title
        )

        section_info.addWidget(
            description
        )

        main_layout.addLayout(
            section_info
        )

        action_frame = QFrame()

        action_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E1E8EF;
                border-radius: 10px;
            }
        """)

        button_layout = QHBoxLayout()

        button_layout.setContentsMargins(
            14,
            12,
            14,
            12
        )

        button_layout.setSpacing(
            10
        )

        self.add_button = QPushButton(
            "Add Leave"
        )

        self.edit_button = QPushButton(
            "Edit Leave"
        )

        self.delete_button = QPushButton(
            "Delete Leave"
        )

        self.add_button.setCursor(
            Qt.PointingHandCursor
        )

        self.edit_button.setCursor(
            Qt.PointingHandCursor
        )

        self.delete_button.setCursor(
            Qt.PointingHandCursor
        )

        self.add_button.setStyleSheet("""
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

        self.edit_button.setStyleSheet("""
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

        self.delete_button.setStyleSheet("""
            QPushButton {
                background: #EEF3F7;
                color: #526779;
                border: 1px solid #D6E0E8;
                border-radius: 7px;
                padding: 9px 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #E3EBF1;
            }
        """)

        self.add_button.clicked.connect(
            self.add_leave
        )

        self.edit_button.clicked.connect(
            self.edit_leave
        )

        self.delete_button.clicked.connect(
            self.delete_leave
        )

        button_layout.addWidget(
            self.add_button
        )

        button_layout.addWidget(
            self.edit_button
        )

        button_layout.addWidget(
            self.delete_button
        )

        button_layout.addStretch()

        action_frame.setLayout(
            button_layout
        )

        main_layout.addWidget(
            action_frame
        )

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

        filter_layout.setContentsMargins(
            14,
            12,
            14,
            12
        )

        filter_layout.setSpacing(
            10
        )

        from_label = QLabel(
            "From"
        )

        self.start_date_input = QDateEdit()

        self.start_date_input.setCalendarPopup(
            True
        )

        self.start_date_input.setDate(
            QDate.currentDate()
        )

        self.start_date_input.setDisplayFormat(
            "dd MMM yyyy"
        )

        self.start_date_input.setMinimumWidth(
            130
        )

        to_label = QLabel(
            "To"
        )

        self.end_date_input = QDateEdit()

        self.end_date_input.setCalendarPopup(
            True
        )

        self.end_date_input.setDate(
            QDate.currentDate()
        )

        self.end_date_input.setDisplayFormat(
            "dd MMM yyyy"
        )

        self.end_date_input.setMinimumWidth(
            130
        )

        self.search_button = QPushButton(
            "Search"
        )

        self.search_button.setCursor(
            Qt.PointingHandCursor
        )

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

        self.search_button.clicked.connect(
            self.load_records
        )

        filter_layout.addWidget(
            from_label
        )

        filter_layout.addWidget(
            self.start_date_input
        )

        filter_layout.addSpacing(
            8
        )

        filter_layout.addWidget(
            to_label
        )

        filter_layout.addWidget(
            self.end_date_input
        )

        filter_layout.addSpacing(
            8
        )

        filter_layout.addWidget(
            self.search_button
        )

        filter_layout.addStretch()

        filter_frame.setLayout(
            filter_layout
        )

        main_layout.addWidget(
            filter_frame
        )

        table_frame = QFrame()

        table_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E1E8EF;
                border-radius: 10px;
            }
        """)

        table_layout = QVBoxLayout()

        table_layout.setContentsMargins(
            1,
            1,
            1,
            1
        )

        self.table = QTableWidget()

        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Staff member",
            "Staff type",
            "Staff ID",
            "Start Date",
            "End Date",
            "Reason",
            "Status",
            "Staff record ID",
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

        self.table.setAlternatingRowColors(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setShowGrid(
            False
        )

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

        table_layout.addWidget(
            self.table
        )

        table_frame.setLayout(
            table_layout
        )

        main_layout.addWidget(
            table_frame
        )

        self.setLayout(
            main_layout
        )

    def load_records(self):
        start_date = (
            self.start_date_input.date().toString(
                "yyyy-MM-dd"
            )
        )

        end_date = (
            self.end_date_input.date().toString(
                "yyyy-MM-dd"
            )
        )

        if start_date > end_date:
            QMessageBox.warning(
                self,
                "Invalid Date Range",
                "The start date cannot be after the end date.",
            )

            return

        records = get_leave_records(
            start_date,
            end_date
        )

        self.table.setRowCount(
            len(records)
        )

        for row, record in enumerate(
            records
        ):
            values = [
                record[0],
                record[2],
                record[8],
                record[3],
                record[4],
                record[5],
                record[6] or "",
                record[7],
                record[1],
            ]

            for column, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(value)
                )

                if column in (
                    0,
                    2,
                    3,
                    4,
                    6,
                    7
                ):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                if column == 7:
                    if record[7] == "Approved":
                        item.setForeground(
                            Qt.GlobalColor.darkGreen
                        )

                    elif record[7] == "Rejected":
                        item.setForeground(
                            Qt.GlobalColor.darkRed
                        )

                    else:
                        item.setForeground(
                            Qt.GlobalColor.darkYellow
                        )

                self.table.setItem(
                    row,
                    column,
                    item
                )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.ResizeToContents
        )

        self.table.resizeRowsToContents()

    def add_leave(self):
        dialog = LeaveRecordDialog(
            parent=self
        )

        if dialog.exec():
            create_leave_record(
                nurse_id=dialog.nurse_input.currentData(),
                start_date=dialog.get_start_date(),
                end_date=dialog.get_end_date(),
                reason=dialog.reason_input.text().strip(),
                status=dialog.status_input.currentText(),
            )

            self.load_records()

    def edit_leave(self):
        selected_row = self.table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Record Selected",
                "Please select a leave record to edit.",
            )

            return

        record_id = int(
            self.table.item(
                selected_row,
                0
            ).text()
        )

        nurse_id = int(
            self.table.item(
                selected_row,
                7
            ).text()
        )

        start_date = self.table.item(
            selected_row,
            3
        ).text()

        end_date = self.table.item(
            selected_row,
            4
        ).text()

        reason = self.table.item(
            selected_row,
            5
        ).text()

        status = self.table.item(
            selected_row,
            6
        ).text()

        dialog = LeaveRecordDialog(
            nurse_id=nurse_id,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status=status,
            parent=self,
        )

        if dialog.exec():
            try:
                update_leave_record(
                    record_id=record_id,
                    start_date=dialog.get_start_date(),
                    end_date=dialog.get_end_date(),
                    reason=dialog.reason_input.text().strip(),
                    status=dialog.status_input.currentText(),
                )

            except ValueError as error:
                QMessageBox.warning(
                    self,
                    "Invalid Leave",
                    str(error)
                )

                return

            self.load_records()

    def delete_leave(self):
        selected_row = self.table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Record Selected",
                "Please select a leave record to delete.",
            )

            return

        record_id = int(
            self.table.item(
                selected_row,
                0
            ).text()
        )

        nurse_name = self.table.item(
            selected_row,
            1
        ).text()

        confirmation = QMessageBox.question(
            self,
            "Delete Leave",
            (
                f"Are you sure you want to delete the "
                f"leave record for {nurse_name}?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if confirmation != (
            QMessageBox.StandardButton.Yes
        ):
            return

        deleted = delete_leave_record(
            record_id
        )

        if deleted:
            self.load_records()

            QMessageBox.information(
                self,
                "Leave Deleted",
                "The leave record has been deleted."
            )

        else:
            QMessageBox.warning(
                self,
                "Delete Failed",
                "The leave record could not be deleted."
            )


class LeaveRecordDialog(QDialog):

    def __init__(
        self,
        nurse_id=None,
        start_date=None,
        end_date=None,
        reason="",
        status="Approved",
        parent=None,
    ):
        super().__init__(parent)

        self.nurse_id = nurse_id

        self.setWindowTitle(
            "Matrix Prime Hospital - Leave Record"
        )

        self.setFixedSize(
            450,
            350
        )

        self.setup_ui()

        self.load_data(
            start_date,
            end_date,
            reason,
            status
        )

    def setup_ui(self):
        layout = QFormLayout()

        layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        layout.setSpacing(
            14
        )

        self.nurse_input = QComboBox()

        nurses = get_nurses()

        for nurse in nurses:
            if nurse[4] == "Active":
                self.nurse_input.addItem(
                    f"{nurse[1]} - {nurse[6]} ({nurse[2]})",
                    nurse[0]
                )

        self.start_date_input = QDateEdit()

        self.start_date_input.setCalendarPopup(
            True
        )

        self.start_date_input.setDate(
            QDate.currentDate()
        )

        self.end_date_input = QDateEdit()

        self.end_date_input.setCalendarPopup(
            True
        )

        self.end_date_input.setDate(
            QDate.currentDate()
        )

        self.reason_input = QLineEdit()

        self.reason_input.setPlaceholderText(
            "Reason for leave"
        )

        self.status_input = QComboBox()

        self.status_input.addItems([
            "Approved",
            "Pending",
            "Rejected"
        ])

        layout.addRow(
            "Staff member:",
            self.nurse_input
        )

        layout.addRow(
            "Start Date:",
            self.start_date_input
        )

        layout.addRow(
            "End Date:",
            self.end_date_input
        )

        layout.addRow(
            "Reason:",
            self.reason_input
        )

        layout.addRow(
            "Status:",
            self.status_input
        )

        button_layout = QHBoxLayout()

        cancel_button = QPushButton(
            "Cancel"
        )

        save_button = QPushButton(
            "Save"
        )

        cancel_button.setCursor(
            Qt.PointingHandCursor
        )

        save_button.setCursor(
            Qt.PointingHandCursor
        )

        cancel_button.setStyleSheet("""
            QPushButton {
                background: #EEF3F7;
                color: #526779;
                border: 1px solid #D6E0E8;
                border-radius: 7px;
                padding: 9px 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #E3EBF1;
            }
        """)

        save_button.setStyleSheet("""
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

        save_button.clicked.connect(
            self.save
        )

        cancel_button.clicked.connect(
            self.reject
        )

        button_layout.addStretch()

        button_layout.addWidget(
            cancel_button
        )

        button_layout.addWidget(
            save_button
        )

        layout.addRow(
            button_layout
        )

        self.setLayout(
            layout
        )

    def load_data(
        self,
        start_date,
        end_date,
        reason,
        status
    ):
        if self.nurse_id is not None:
            index = self.nurse_input.findData(
                self.nurse_id
            )

            if index >= 0:
                self.nurse_input.setCurrentIndex(
                    index
                )

        if start_date:
            self.start_date_input.setDate(
                QDate.fromString(
                    start_date,
                    "yyyy-MM-dd"
                )
            )

        if end_date:
            self.end_date_input.setDate(
                QDate.fromString(
                    end_date,
                    "yyyy-MM-dd"
                )
            )

        self.reason_input.setText(
            reason
        )

        status_index = (
            self.status_input.findText(
                status
            )
        )

        if status_index >= 0:
            self.status_input.setCurrentIndex(
                status_index
            )

    def get_start_date(self):
        return (
            self.start_date_input.date().toString(
                "yyyy-MM-dd"
            )
        )

    def get_end_date(self):
        return (
            self.end_date_input.date().toString(
                "yyyy-MM-dd"
            )
        )

    def save(self):
        if self.nurse_input.currentData() is None:
            QMessageBox.warning(
                self,
                "No Staff Member",
                "Please select a staff member."
            )

            return

        if (
            self.start_date_input.date()
            > self.end_date_input.date()
        ):
            QMessageBox.warning(
                self,
                "Invalid Leave",
                "The start date cannot be after the end date.",
            )

            return

        self.accept()