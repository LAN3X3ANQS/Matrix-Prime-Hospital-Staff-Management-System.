from PySide6.QtCore import QDate
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

        self.setWindowTitle("NurseRoster - Shift Changes")
        self.resize(1000, 600)

        self.setup_ui()
        self.load_records()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Shift Changes")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Shift Change")
        self.edit_button = QPushButton("Edit Shift Change")
        self.delete_button = QPushButton("Delete Shift Change")

        self.add_button.clicked.connect(self.add_shift_change)
        self.edit_button.clicked.connect(self.edit_shift_change)
        self.delete_button.clicked.connect(self.delete_shift_change)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()

        filter_layout = QHBoxLayout()

        from_label = QLabel("From:")
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())

        to_label = QLabel("To:")
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.load_records)

        filter_layout.addWidget(from_label)
        filter_layout.addWidget(self.start_date_input)
        filter_layout.addWidget(to_label)
        filter_layout.addWidget(self.end_date_input)
        filter_layout.addWidget(self.search_button)
        filter_layout.addStretch()

        self.table = QTableWidget()
        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Nurse",
            "Staff ID",
            "Date",
            "Original Shift",
            "New Shift",
            "Reason",
            "Created At",
            "Nurse ID",
        ])

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        main_layout.addWidget(title)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(filter_layout)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

    def load_records(self):
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")

        if start_date > end_date:
            QMessageBox.warning(
                self,
                "Invalid Date Range",
                "The start date cannot be after the end date.",
            )
            return

        records = get_shift_records(start_date, end_date)
        self.table.setRowCount(len(records))

        for row, record in enumerate(records):
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
            ]

            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))

        self.table.resizeColumnsToContents()

    def add_shift_change(self):
        dialog = ShiftRecordDialog(parent=self)

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

        record_id = int(self.table.item(selected_row, 0).text())
        nurse_id = int(self.table.item(selected_row, 8).text())
        shift_date = self.table.item(selected_row, 3).text()
        original_shift = self.table.item(selected_row, 4).text()
        new_shift = self.table.item(selected_row, 5).text()
        reason = self.table.item(selected_row, 6).text()

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

        record_id = int(self.table.item(selected_row, 0).text())
        nurse_name = self.table.item(selected_row, 1).text()

        confirmation = QMessageBox.question(
            self,
            "Delete Shift Change",
            f"Are you sure you want to delete the shift change for {nurse_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        deleted = delete_shift_record(record_id)

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

        self.setWindowTitle("Shift Change")
        self.setFixedSize(450, 350)

        self.setup_ui()
        self.load_data(shift_date, original_shift, new_shift, reason)

    def setup_ui(self):
        layout = QFormLayout()

        self.nurse_input = QComboBox()
        nurses = get_nurses()

        for nurse in nurses:
            if nurse[4] == "Active":
                self.nurse_input.addItem(f"{nurse[1]} ({nurse[2]})", nurse[0])

        self.shift_date_input = QDateEdit()
        self.shift_date_input.setCalendarPopup(True)
        self.shift_date_input.setDate(QDate.currentDate())

        self.original_shift_input = QComboBox()
        self.original_shift_input.addItems(["Morning", "Night", "Off"])

        self.new_shift_input = QComboBox()
        self.new_shift_input.addItems(["Morning", "Night", "Off"])

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Reason for shift change")

        layout.addRow("Nurse:", self.nurse_input)
        layout.addRow("Shift Date:", self.shift_date_input)
        layout.addRow("Original Shift:", self.original_shift_input)
        layout.addRow("New Shift:", self.new_shift_input)
        layout.addRow("Reason:", self.reason_input)

        button_layout = QHBoxLayout()

        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

        save_button.clicked.connect(self.save)
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def load_data(
        self,
        shift_date,
        original_shift,
        new_shift,
        reason,
    ):
        if self.nurse_id is not None:
            index = self.nurse_input.findData(self.nurse_id)

            if index >= 0:
                self.nurse_input.setCurrentIndex(index)

        if shift_date:
            self.shift_date_input.setDate(
                QDate.fromString(shift_date, "yyyy-MM-dd")
            )

        if original_shift:
            index = self.original_shift_input.findText(original_shift)

            if index >= 0:
                self.original_shift_input.setCurrentIndex(index)

        if new_shift:
            index = self.new_shift_input.findText(new_shift)

            if index >= 0:
                self.new_shift_input.setCurrentIndex(index)

        self.reason_input.setText(reason)

    def get_shift_date(self):
        return self.shift_date_input.date().toString("yyyy-MM-dd")

    def save(self):
        if self.nurse_input.currentData() is None:
            QMessageBox.warning(self, "No Nurse", "Please select a nurse.")
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