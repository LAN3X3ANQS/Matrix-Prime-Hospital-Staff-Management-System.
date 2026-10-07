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
from records.shift_records import (
    create_shift_record,
    get_shift_records,
    update_shift_record,
    delete_shift_record,
)


class ShiftRecordsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Matrix Prime Hospital - Shift Changes"
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
            "Shift Changes"
        )

        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #0B3B82;
        """)

        description = QLabel(
            "Manage approved changes to nurses' scheduled shifts."
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
            "Add Shift Change"
        )

        self.edit_button = QPushButton(
            "Edit Shift Change"
        )

        self.delete_button = QPushButton(
            "Delete Shift Change"
        )

        for button in (
            self.add_button,
            self.edit_button,
            self.delete_button,
        ):
            button.setCursor(
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
            self.add_shift_change
        )

        self.edit_button.clicked.connect(
            self.edit_shift_change
        )

        self.delete_button.clicked.connect(
            self.delete_shift_change
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

        self.table.setColumnCount(10)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Staff member",
            "Staff ID",
            "Date",
            "Original Shift",
            "New Shift",
            "Reason",
            "Created At",
            "Staff record ID",
            "Staff type",
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

        records = get_shift_records(
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
                record[3],
                record[4],
                record[5],
                record[6],
                record[7] or "",
                record[8],
                record[1],
                record[9],
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
                    5,
                    7,
                    8
                ):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                if column == 4:
                    if record[5] == "Morning":
                        item.setForeground(
                            Qt.GlobalColor.darkGreen
                        )

                    elif record[5] == "Night":
                        item.setForeground(
                            Qt.GlobalColor.darkBlue
                        )

                if column == 5:
                    if record[6] == "Morning":
                        item.setForeground(
                            Qt.GlobalColor.darkGreen
                        )

                    elif record[6] == "Night":
                        item.setForeground(
                            Qt.GlobalColor.darkBlue
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
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            8,
            QHeaderView.ResizeMode.ResizeToContents
        )

        self.table.resizeRowsToContents()

    def add_shift_change(self):
        dialog = ShiftRecordDialog(
            parent=self
        )

        if dialog.exec():
            try:
                create_shift_record(
                    nurse_id=dialog.nurse_input.currentData(),
                    shift_date=dialog.get_shift_date(),
                    original_shift=dialog.original_shift_input.currentText(),
                    new_shift=dialog.new_shift_input.currentText(),
                    reason=dialog.reason_input.text().strip(),
                )

            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not create the shift change:\n\n{error}",
                )

                return

            self.load_records()

    def edit_shift_change(self):
        selected_row = self.table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Record Selected",
                "Please select a shift change to edit.",
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
                8
            ).text()
        )

        shift_date = self.table.item(
            selected_row,
            3
        ).text()

        original_shift = self.table.item(
            selected_row,
            4
        ).text()

        new_shift = self.table.item(
            selected_row,
            5
        ).text()

        reason = self.table.item(
            selected_row,
            6
        ).text()

        dialog = ShiftRecordDialog(
            nurse_id=nurse_id,
            shift_date=shift_date,
            original_shift=original_shift,
            new_shift=new_shift,
            reason=reason,
            parent=self,
        )

        if dialog.exec():
            try:
                update_shift_record(
                    record_id=record_id,
                    shift_date=dialog.get_shift_date(),
                    original_shift=dialog.original_shift_input.currentText(),
                    new_shift=dialog.new_shift_input.currentText(),
                    reason=dialog.reason_input.text().strip(),
                )

            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not update the shift change:\n\n{error}",
                )

                return

            self.load_records()

    def delete_shift_change(self):
        selected_row = self.table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Record Selected",
                "Please select a shift change to delete.",
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
            "Delete Shift Change",
            (
                f"Are you sure you want to delete the "
                f"shift change for {nurse_name}?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if confirmation != (
            QMessageBox.StandardButton.Yes
        ):
            return

        deleted = delete_shift_record(
            record_id
        )

        if deleted:
            self.load_records()

            QMessageBox.information(
                self,
                "Shift Change Deleted",
                "The shift change has been deleted.",
            )

        else:
            QMessageBox.warning(
                self,
                "Delete Failed",
                "The shift change could not be deleted.",
            )


class ShiftRecordDialog(QDialog):

    def __init__(
        self,
        nurse_id=None,
        shift_date=None,
        original_shift=None,
        new_shift=None,
        reason="",
        parent=None,
    ):
        super().__init__(parent)

        self.nurse_id = nurse_id

        self.setWindowTitle(
            "Matrix Prime Hospital - Shift Change"
        )

        self.setFixedSize(
            450,
            350
        )

        self.setup_ui()

        self.load_data(
            shift_date,
            original_shift,
            new_shift,
            reason
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

        self.shift_date_input = QDateEdit()

        self.shift_date_input.setCalendarPopup(
            True
        )

        self.shift_date_input.setDate(
            QDate.currentDate()
        )

        self.original_shift_input = QComboBox()

        self.original_shift_input.addItems([
            "Morning",
            "Night",
            "Off"
        ])

        self.new_shift_input = QComboBox()

        self.new_shift_input.addItems([
            "Morning",
            "Night",
            "Off"
        ])

        self.reason_input = QLineEdit()

        self.reason_input.setPlaceholderText(
            "Reason for shift change"
        )

        layout.addRow(
            "Nurse:",
            self.nurse_input
        )

        layout.addRow(
            "Shift Date:",
            self.shift_date_input
        )

        layout.addRow(
            "Original Shift:",
            self.original_shift_input
        )

        layout.addRow(
            "New Shift:",
            self.new_shift_input
        )

        layout.addRow(
            "Reason:",
            self.reason_input
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
        shift_date,
        original_shift,
        new_shift,
        reason,
    ):
        if self.nurse_id is not None:
            index = self.nurse_input.findData(
                self.nurse_id
            )

            if index >= 0:
                self.nurse_input.setCurrentIndex(
                    index
                )

        if shift_date:
            self.shift_date_input.setDate(
                QDate.fromString(
                    shift_date,
                    "yyyy-MM-dd"
                )
            )

        if original_shift:
            index = self.original_shift_input.findText(
                original_shift
            )

            if index >= 0:
                self.original_shift_input.setCurrentIndex(
                    index
                )

        if new_shift:
            index = self.new_shift_input.findText(
                new_shift
            )

            if index >= 0:
                self.new_shift_input.setCurrentIndex(
                    index
                )

        self.reason_input.setText(
            reason
        )

    def get_shift_date(self):
        return (
            self.shift_date_input.date().toString(
                "yyyy-MM-dd"
            )
        )

    def save(self):
        if self.nurse_input.currentData() is None:
            QMessageBox.warning(
                self,
                "No Nurse",
                "Please select a nurse."
            )

            return

        if (
            self.original_shift_input.currentText()
            == self.new_shift_input.currentText()
        ):
            QMessageBox.warning(
                self,
                "Invalid Shift Change",
                "The original and new shifts cannot be the same.",
            )

            return

        self.accept()