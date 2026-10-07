from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFrame,
    QHeaderView,
)
from database.database import (
    add_staff,
    deactivate_staff,
    get_staff,
    update_staff,
)
from database.models import Staff
from analytics.attendance_analytics import get_staff_attendance_score
from ui.nurse_form import NurseForm
from ui.staff_profile_dialog import StaffProfileDialog


class NursesView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Matrix Prime Hospital - Staff directory")

        self.setup_ui()
        self.load_staff()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(28, 24, 28, 28)

        main_layout.setSpacing(18)

        section_header = QHBoxLayout()

        section_info = QVBoxLayout()
        section_info.setSpacing(3)

        title = QLabel("Staff Directory")

        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #17324D;
        """)

        description = QLabel(
            "Register and manage admins, janitors, front desk staff, nurses, lab techs, and doctors."
        )

        description.setStyleSheet("""
            font-size: 13px;
            color: #718096;
        """)

        section_info.addWidget(title)

        section_info.addWidget(description)

        section_header.addLayout(section_info)

        section_header.addStretch()

        main_layout.addLayout(section_header)

        action_frame = QFrame()

        action_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E1E8EF;
                border-radius: 10px;
            }
        """)

        button_layout = QHBoxLayout()

        button_layout.setContentsMargins(14, 12, 14, 12)

        button_layout.setSpacing(10)

        self.add_button = QPushButton("Register Staff")

        self.profile_button = QPushButton("View Profile")
        self.edit_button = QPushButton("Edit Staff")

        self.deactivate_button = QPushButton("Deactivate Staff")

        self.add_button.setCursor(Qt.PointingHandCursor)

        self.edit_button.setCursor(Qt.PointingHandCursor)

        self.deactivate_button.setCursor(Qt.PointingHandCursor)

        self.add_button.setStyleSheet("""
            QPushButton {
                background: #66B032;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #57982B;
            }

            QPushButton:pressed {
                background: #477E24;
            }
        """)

        self.edit_button.setStyleSheet("""
            QPushButton {
                background: #1769AA;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #2380C5;
            }

            QPushButton:pressed {
                background: #125486;
            }
        """)

        self.deactivate_button.setStyleSheet("""
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

        self.add_button.clicked.connect(self.add_staff)

        self.profile_button.clicked.connect(self.view_profile)
        self.edit_button.clicked.connect(self.edit_staff)

        self.deactivate_button.clicked.connect(self.deactivate_staff)

        button_layout.addWidget(self.add_button)

        button_layout.addWidget(self.profile_button)
        button_layout.addWidget(self.edit_button)

        button_layout.addWidget(self.deactivate_button)

        button_layout.addStretch()

        action_frame.setLayout(button_layout)

        main_layout.addWidget(action_frame)

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

        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Name",
            "Staff ID",
            "Staff type",
            "Unit",
            "Phone",
            "Status",
            "Rotation",
            "Attendance reliability · 30d",
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

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            8,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.table.setStyleSheet("""
            QTableWidget {
                background: white;
                alternate-background-color: #F8FBFD;
                color: #17324D;
                border: none;
                border-radius: 9px;
                gridline-color: transparent;
                selection-background-color: #DFF0D0;
                selection-color: #17324D;
                outline: none;
            }

            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #EDF2F7;
            }

            QTableWidget::item:selected {
                background: #DFF0D0;
                color: #17324D;
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
        self.table.cellDoubleClicked.connect(
            lambda row, column: self.view_profile()
        )

    def load_staff(self):
        nurses = get_staff()

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
                nurse[6],
                nurse[7],
                nurse[3] or "",
                nurse[4],
                rotation,
            ]
            try:
                score = get_staff_attendance_score(nurse[0])
            except ValueError:
                score = {"score": None, "is_consistent": False}
            values.append(
                "N/A" if score["score"] is None else f"{score['score']}%"
            )

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                if column == 6:
                    if nurse[4] == "Active":
                        item.setForeground(Qt.GlobalColor.darkGreen)

                    else:
                        item.setForeground(Qt.GlobalColor.gray)
                if column == 8 and score["is_consistent"]:
                    item.setForeground(Qt.GlobalColor.darkGreen)

                self.table.setItem(row, column, item)

        self.table.resizeRowsToContents()

    def add_staff(self):
        dialog = NurseForm(parent=self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        staff = Staff(
            nurse_id=None,
            name=data["name"],
            staff_id=data["staff_id"],
            phone=data["phone"],
            status=data["status"],
        )

        try:
            add_staff(
                staff,
                rotation_position=data["rotation_position"],
                staff_type=data["staff_type"],
                unit=data["unit"],
                profile_photo=data["profile_photo"],
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Could Not Add Staff Member",
                str(error),
            )

            return

        self.load_staff()

        QMessageBox.information(
            self,
            "Staff Member Registered",
            f"{staff.staff_id} has been assigned to "
            f"{staff.name} and registered successfully.",
        )

    def view_profile(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.information(
                self,
                "Select a staff member",
                "Select a staff member to view their profile.",
            )
            return
        staff_record_id = int(self.table.item(selected_row, 0).text())
        staff = next(
            (
                record
                for record in get_staff()
                if record[0] == staff_record_id
            ),
            None,
        )
        if staff is None:
            QMessageBox.warning(
                self,
                "Staff member not found",
                "The selected staff profile is no longer available.",
            )
            return
        try:
            score = get_staff_attendance_score(staff_record_id)
        except ValueError:
            score = {
                "score": None,
                "scheduled_shifts": 0,
                "on_time_check_ins": 0,
                "late_check_ins": 0,
                "absent_shifts": 0,
                "completed_sign_outs": 0,
                "approved_leave_shifts": 0,
                "is_consistent": False,
            }
        StaffProfileDialog(staff, score, self).exec()

    def edit_staff(self):
        selected_row = self.table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Staff Member Selected",
                "Please select a staff member to edit.",
            )

            return

        nurse_id = int(self.table.item(selected_row, 0).text())

        nurses = get_staff()

        nurse = None

        for record in nurses:
            if record[0] == nurse_id:
                nurse = record
                break

        if nurse is None:
            QMessageBox.warning(
                self,
                "Staff Member Not Found",
                "The selected staff member could not be found.",
            )

            return

        dialog = NurseForm(nurse=nurse, parent=self)

        if not dialog.exec():
            return

        data = dialog.get_data()

        try:
            updated = update_staff(
                staff_record_id=nurse_id,
                name=data["name"],
                staff_id=data["staff_id"],
                phone=data["phone"],
                status=data["status"],
                rotation_position=data["rotation_position"],
                staff_type=data["staff_type"],
                unit=data["unit"],
                profile_photo=data["profile_photo"],
                clear_profile_photo=data["remove_profile_photo"],
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Could Not Update Staff Member",
                str(error),
            )

            return

        if updated:
            self.load_staff()

            QMessageBox.information(
                self,
                "Staff Member Updated",
                "The staff member has been updated successfully.",
            )

        else:
            QMessageBox.warning(
                self,
                "Update Failed",
                "The staff member could not be updated.",
            )

    def deactivate_staff(self):
        selected_row = self.table.currentRow()

        if selected_row < 0:
            QMessageBox.warning(
                self,
                "No Staff Member Selected",
                "Please select a staff member to deactivate.",
            )

            return

        nurse_id = int(self.table.item(selected_row, 0).text())

        nurse_name = self.table.item(selected_row, 1).text()

        status = self.table.item(selected_row, 6).text()

        if status == "Inactive":
            QMessageBox.information(
                self,
                "Already Inactive",
                f"{nurse_name} is already inactive.",
            )

            return

        confirmation = QMessageBox.question(
            self,
            "Deactivate Staff Member",
            (
                f"Are you sure you want to deactivate {nurse_name}?\n\n"
                "Their historical records will be preserved."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        updated = deactivate_staff(nurse_id)

        if updated:
            self.load_staff()
            QMessageBox.information(
                self,
                "Staff Member Deactivated",
                f"{nurse_name} has been deactivated.",
            )

        else:
            QMessageBox.warning(
                self,
                "Deactivation Failed",
                "The staff member could not be deactivated.",
            )

    def load_nurses(self):
        self.load_staff()