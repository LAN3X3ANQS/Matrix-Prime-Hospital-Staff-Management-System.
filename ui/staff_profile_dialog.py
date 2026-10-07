from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class StaffProfileDialog(QDialog):
    def __init__(self, staff, score, parent=None):
        super().__init__(parent)
        self.staff = staff
        self.score = score
        self.setWindowTitle("Matrix Prime Hospital - Staff profile")
        self.setMinimumWidth(490)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(16)

        identity = QHBoxLayout()
        self.photo = QLabel()
        self.photo.setFixedSize(104, 104)
        self.photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo.setStyleSheet(
            "background: #F2F4F7; border: 1px solid #D0D5DD; "
            "border-radius: 52px; color: #667085;"
        )
        photo_bytes = self.staff[8] if len(self.staff) > 8 else None
        pixmap = QPixmap()
        if photo_bytes and pixmap.loadFromData(photo_bytes):
            self.photo.setPixmap(
                pixmap.scaled(
                    self.photo.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.photo.setText("No picture")
        identity.addWidget(self.photo)

        name = QLabel(self.staff[1])
        name.setStyleSheet(
            "font-size: 21px; font-weight: 700; color: #182230;"
        )
        details = QLabel(
            f"{self.staff[6]} · {self.staff[7] or 'Unit not specified'}"
        )
        details.setStyleSheet("font-size: 13px; color: #667085;")
        identity_text = QVBoxLayout()
        identity_text.addStretch()
        identity_text.addWidget(name)
        identity_text.addWidget(details)
        identity_text.addStretch()
        identity.addLayout(identity_text, 1)
        layout.addLayout(identity)

        fields = QFormLayout()
        fields.setVerticalSpacing(10)
        fields.addRow("Staff ID", QLabel(self.staff[2]))
        fields.addRow("Staff type", QLabel(self.staff[6]))
        fields.addRow("Unit", QLabel(self.staff[7] or "Not specified"))
        fields.addRow("Phone", QLabel(self.staff[3] or "Not specified"))
        fields.addRow("Employment status", QLabel(self.staff[4]))
        rotation = self.staff[5]
        rotation_text = (
            f"Rotation {rotation + 1}"
            if rotation is not None
            else "Not assigned"
        )
        fields.addRow("Duty rotation", QLabel(rotation_text))
        layout.addLayout(fields)

        if self.score["score"] is None:
            score_text = "Not enough scheduled shifts yet"
            score_color = "#667085"
        else:
            score_text = (
                f"{self.score['score']}% "
                f"({'Consistent' if self.score['is_consistent'] else 'Needs review'})"
            )
            score_color = (
                "#16803C"
                if self.score["is_consistent"]
                else "#A15C07"
            )
        score_label = QLabel(score_text)
        score_label.setStyleSheet(
            f"font-size: 19px; font-weight: 700; color: {score_color};"
        )
        score_explanation = QLabel(
            "Attendance reliability · last 30 days. On-time check-ins ÷ "
            "scheduled shifts, excluding approved leave. This is not a "
            "measure of job performance."
        )
        score_explanation.setWordWrap(True)
        score_explanation.setStyleSheet("font-size: 11px; color: #667085;")
        layout.addWidget(score_label)
        layout.addWidget(score_explanation)

        counts = QLabel(
            f"Scheduled: {self.score['scheduled_shifts']}   "
            f"On time: {self.score['on_time_check_ins']}   "
            f"Late: {self.score['late_check_ins']}   "
            f"Not recorded: {self.score['absent_shifts']}\n"
            f"Shifts signed out: {self.score['completed_sign_outs']}   "
            f"Approved leave shifts: {self.score['approved_leave_shifts']}"
        )
        counts.setWordWrap(True)
        counts.setStyleSheet("font-size: 11px; color: #475467;")
        layout.addWidget(counts)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)
