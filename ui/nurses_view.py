from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)
from database.database import (
    get_nurses,
    add_nurse,
    update_nurse,
    deactivate_nurse,
)
from database.models import Nurse
from ui.nurse_form import NurseForm


class NursesView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("NurseRoster - Nurses")
        self.resize(1000, 600)

        self.setup_ui()
        self.load_nurses()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Nurses")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Nurse")
        self.edit_button = QPushButton("Edit Nurse")
        self.deactivate_button = QPushButton("Deactivate Nurse")

        self.add_button.clicked.connect(self.add_nurse)
        self.edit_button.clicked.connect(self.edit_nurse)
        self.deactivate_button.clicked.connect(self.deactivate_nurse)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.deactivate_button)
        button_layout.addStretch()

        self.table = QTableWidget()
        self.table.setColumnCount(6)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Name",
            "Staff ID",
            "Phone",
            "Status",
            "Rotation",
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
        self.table.horizontalHeader().setStretchLastSection(True)

        main_layout.addWidget(title)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

    def load_nurses(self):
        nurses = get_nurses()

        self.table.setRowCount(len(nurses))

        for row, nurse in enumerate(nurses):
            rotation_position = nurse[5]

            if rotation_position == 0:
                rotation = "Rotation 1"
            elif rotation_position == 1:
                rotation = "Rotation 2"
            elif rotation_position == 2:
                rotation = "Rotation 3"
            else:
                rotation = "Unassigned"

            values = [
                nurse[0],
                nurse[1],
                nurse[2],
                nurse[3] or "",
                nurse[4],
                rotation,
            ]

            for column, value in enumerate(values):
                self.table.setItem(
                    row,
                    column,
                    QTableWidgetItem(str(value)),
                )

        self.table.resizeColumnsToContents()

    def add_nurse(self):
        dialog = NurseForm(parent=self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        nurse = Nurse(
            nurse_id=None,
            name=data["name"],
            staff_id=data["staff_id"],
            phone=data["phone"],
            status=data["status"],
        )

        try:
            add_nurse(
                nurse,
                rotation_position=data["rotation_position"],
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Could Not Add Nurse",
                str(error),
            )
            return

        self.load_nurses()

        QMessageBox.information(
            self,
            "Nurse Added",
            "The nurse has been added successfully.",
        )

    def edit_nurse(self):
        selected_row = self.table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Nurse Selected",
                "Please select a nurse to edit.",
            )
            return

        nurse_id = int(self.table.item(selected_row, 0).text())

        nurses = get_nurses()
        nurse = None

        for record in nurses:
            if record[0] == nurse_id:
                nurse = record
                break

        if nurse is None:
            QMessageBox.warning(
                self,
                "Nurse Not Found",
                "The selected nurse could not be found.",
            )
            return

        dialog = NurseForm(nurse=nurse, parent=self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        try:
            updated = update_nurse(
                nurse_id=nurse_id,
                name=data["name"],
                staff_id=data["staff_id"],
                phone=data["phone"],
                status=data["status"],
                rotation_position=data["rotation_position"],
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Could Not Update Nurse",
                str(error),
            )
            return

        if updated:
            self.load_nurses()

            QMessageBox.information(
                self,
                "Nurse Updated",
                "The nurse has been updated successfully.",
            )
        else:
            QMessageBox.warning(
                self,
                "Update Failed",
                "The nurse could not be updated.",
            )

    def deactivate_nurse(self):
        selected_row = self.table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Nurse Selected",
                "Please select a nurse to deactivate.",
            )
            return

        nurse_id = int(self.table.item(selected_row, 0).text())
        nurse_name = self.table.item(selected_row, 1).text()
        status = self.table.item(selected_row, 4).text()

        if status == "Inactive":
            QMessageBox.information(
                self,
                "Already Inactive",
                f"{nurse_name} is already inactive.",
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Deactivate Nurse",
            (
                f"Are you sure you want to deactivate {nurse_name}?\n\n"
                "The nurse's historical records will be preserved."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        updated = deactivate_nurse(nurse_id)

        if updated:
            self.load_nurses()

            QMessageBox.information(
                self,
                "Nurse Deactivated",
                f"{nurse_name} has been deactivated.",
            )
        else:
            QMessageBox.warning(
                self,
                "Deactivation Failed",
                "The nurse could not be deactivated.",
            )