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
from records.leave_records import (
    create_leave_record,
    get_leave_records,
    update_leave_record,
    delete_leave_record,
)


class LeaveRecordsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("NurseRoster - Leave Records")
        self.resize(1000, 600)

        self.setup_ui()
        self.load_records()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Leave Records")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Leave")
        self.edit_button = QPushButton("Edit Leave")
        self.delete_button = QPushButton("Delete Leave")

        self.add_button.clicked.connect(self.add_leave)
        self.edit_button.clicked.connect(self.edit_leave)
        self.delete_button.clicked.connect(self.delete_leave)

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
        self.table.setColumnCount(8)

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Nurse",
                "Staff ID",
                "Start Date",
                "End Date",
                "Reason",
                "Status",
                "Nurse ID",
            ]
        )

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

        records = get_leave_records(start_date, end_date)
        self.table.setRowCount(len(records))

        for row, record in enumerate(records):
            values = [
                record[0],
                record[2],
                record[3],
                record[4],
                record[5],
                record[6] or "",
                record[7],
                record[1],
            ]

            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))

        self.table.resizeColumnsToContents()

    def add_leave(self):
        dialog = LeaveRecordDialog(parent=self)

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

        record_id = int(self.table.item(selected_row, 0).text())
        nurse_id = int(self.table.item(selected_row, 7).text())
        start_date = self.table.item(selected_row, 3).text()
        end_date = self.table.item(selected_row, 4).text()
        reason = self.table.item(selected_row, 5).text()
        status = self.table.item(selected_row, 6).text()

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
                QMessageBox.warning(self, "Invalid Leave", str(error))
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

        record_id = int(self.table.item(selected_row, 0).text())
        nurse_name = self.table.item(selected_row, 1).text()

        confirmation = QMessageBox.question(
            self,
            "Delete Leave",
            f"Are you sure you want to delete the leave record for {nurse_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        deleted = delete_leave_record(record_id)

        if deleted:
            self.load_records()
            QMessageBox.information(
                self, "Leave Deleted", "The leave record has been deleted."
            )
        else:
            QMessageBox.warning(
                self, "Delete Failed", "The leave record could not be deleted."
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

        self.setWindowTitle("Leave Record")
        self.setFixedSize(450, 350)

        self.setup_ui()
        self.load_data(start_date, end_date, reason, status)

    def setup_ui(self):
        layout = QFormLayout()

        self.nurse_input = QComboBox()
        nurses = get_nurses()

        for nurse in nurses:
            if nurse[4] == "Active":
                self.nurse_input.addItem(f"{nurse[1]} ({nurse[2]})", nurse[0])

        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())

        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())

        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Reason for leave")

        self.status_input = QComboBox()
        self.status_input.addItems(["Approved", "Pending", "Rejected"])

        layout.addRow("Nurse:", self.nurse_input)
        layout.addRow("Start Date:", self.start_date_input)
        layout.addRow("End Date:", self.end_date_input)
        layout.addRow("Reason:", self.reason_input)
        layout.addRow("Status:", self.status_input)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

        save_button.clicked.connect(self.save)
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def load_data(self, start_date, end_date, reason, status):
        if self.nurse_id is not None:
            index = self.nurse_input.findData(self.nurse_id)
            if index >= 0:
                self.nurse_input.setCurrentIndex(index)

        if start_date:
            self.start_date_input.setDate(
                QDate.fromString(start_date, "yyyy-MM-dd")
            )

        if end_date:
            self.end_date_input.setDate(
                QDate.fromString(end_date, "yyyy-MM-dd")
            )

        self.reason_input.setText(reason)

        status_index = self.status_input.findText(status)
        if status_index >= 0:
            self.status_input.setCurrentIndex(status_index)

    def get_start_date(self):
        return self.start_date_input.date().toString("yyyy-MM-dd")

    def get_end_date(self):
        return self.end_date_input.date().toString("yyyy-MM-dd")

    def save(self):
        if self.nurse_input.currentData() is None:
            QMessageBox.warning(self, "No Nurse", "Please select a nurse.")
            return

        if self.start_date_input.date() > self.end_date_input.date():
            QMessageBox.warning(
                self,
                "Invalid Leave",
                "The start date cannot be after the end date.",
            )
            return

        self.accept()