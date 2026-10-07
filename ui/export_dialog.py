from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QHBoxLayout,
    QLabel,
    QFrame,
)
from exports.csv_export import export_to_csv
from exports.excel_export import export_to_excel
from exports.pdf_export import export_to_pdf


class ExportDialog(QDialog):

    def __init__(
        self,
        title,
        headers,
        rows,
        parent=None
    ):
        super().__init__(parent)

        self.report_title = title
        self.headers = headers
        self.rows = rows

        self.setWindowTitle(
            "Matrix Prime Hospital - Export Report"
        )

        self.setFixedSize(
            480,
            300
        )

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        main_layout.setSpacing(
            18
        )

        title = QLabel(
            "Export Report"
        )

        title.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #0B3B82;
        """)

        description = QLabel(
            "Choose a format and save a copy of this report."
        )

        description.setStyleSheet("""
            font-size: 13px;
            color: #718096;
        """)

        main_layout.addWidget(
            title
        )

        main_layout.addWidget(
            description
        )

        format_frame = QFrame()

        format_frame.setStyleSheet("""
            QFrame {
                background: #F8FBFD;
                border: 1px solid #E1E8EF;
                border-radius: 10px;
            }

            QLabel {
                color: #526779;
                font-weight: 600;
            }
        """)

        form_layout = QFormLayout()

        form_layout.setContentsMargins(
            16,
            16,
            16,
            16
        )

        form_layout.setSpacing(
            14
        )

        self.format_input = QComboBox()

        self.format_input.addItem(
            "CSV",
            "csv"
        )

        self.format_input.addItem(
            "Excel",
            "excel"
        )

        self.format_input.addItem(
            "PDF",
            "pdf"
        )

        form_layout.addRow(
            "Format:",
            self.format_input
        )

        format_frame.setLayout(
            form_layout
        )

        main_layout.addWidget(
            format_frame
        )

        button_layout = QHBoxLayout()

        button_layout.setSpacing(
            10
        )

        button_layout.addStretch()

        self.cancel_button = QPushButton(
            "Cancel"
        )

        self.export_button = QPushButton(
            "Export"
        )

        self.cancel_button.setCursor(
            Qt.PointingHandCursor
        )

        self.export_button.setCursor(
            Qt.PointingHandCursor
        )

        self.cancel_button.setStyleSheet("""
            QPushButton {
                background: #EEF3F7;
                color: #526779;
                border: 1px solid #D6E0E8;
                border-radius: 7px;
                padding: 9px 20px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #E3EBF1;
            }
        """)

        self.export_button.setStyleSheet("""
            QPushButton {
                background: #00C853;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 9px 22px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #00B048;
            }

            QPushButton:pressed {
                background: #00963E;
            }
        """)

        self.export_button.clicked.connect(
            self.export_report
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        button_layout.addWidget(
            self.cancel_button
        )

        button_layout.addWidget(
            self.export_button
        )

        main_layout.addLayout(
            button_layout
        )

        self.setLayout(
            main_layout
        )

    def export_report(self):
        export_format = (
            self.format_input.currentData()
        )

        if export_format == "csv":
            file_filter = (
                "CSV Files (*.csv)"
            )

            default_extension = ".csv"

        elif export_format == "excel":
            file_filter = (
                "Excel Files (*.xlsx)"
            )

            default_extension = ".xlsx"

        else:
            file_filter = (
                "PDF Files (*.pdf)"
            )

            default_extension = ".pdf"

        default_file_name = (
            self.report_title
            .replace("/", "-")
            .replace("\\", "-")
            + default_extension
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            str(
                Path.home()
                / default_file_name
            ),
            file_filter
        )

        if not file_path:
            return

        try:
            if export_format == "csv":
                export_to_csv(
                    file_path=file_path,
                    headers=self.headers,
                    rows=self.rows
                )

            elif export_format == "excel":
                export_to_excel(
                    file_path=file_path,
                    sheet_name=self.report_title[:31],
                    headers=self.headers,
                    rows=self.rows
                )

            elif export_format == "pdf":
                export_to_pdf(
                    file_path=file_path,
                    title=self.report_title,
                    headers=self.headers,
                    rows=self.rows
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export the report:\n\n{error}"
            )

            return

        QMessageBox.information(
            self,
            "Export Complete",
            f"Report exported successfully to:\n\n{file_path}"
        )

        self.accept()