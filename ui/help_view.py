from PySide6.QtWidgets import (
    QLabel,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


APP_VERSION = "1.0.0"


class HelpView(QWidget):
    def __init__(self, role, parent=None):
        super().__init__(parent)
        if role not in {"ADMIN", "STAFF"}:
            raise ValueError("A valid application role is required.")
        self.role = role
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(14)

        description = QLabel(
            "Quick instructions for using Matrix Prime Hospital and resolving "
            "common problems."
        )
        description.setObjectName("help_description")
        description.setWordWrap(True)
        layout.addWidget(description)

        self.content = QTextBrowser()
        self.content.setObjectName("help_content")
        self.content.setOpenLinks(False)
        self.content.setHtml(self.help_html())
        layout.addWidget(self.content, 1)

        self.setStyleSheet("""
            QLabel#help_description {
                color: #667085;
                font-size: 13px;
            }
            QTextBrowser#help_content {
                background: #FFFFFF;
                border: 1px solid #E4E7EC;
                border-radius: 10px;
                padding: 16px;
                color: #182230;
                font-size: 13px;
            }
        """)

    def help_html(self):
        admin_topics = ""
        if self.role == "ADMIN":
            admin_topics = """
                <h2>Admin tasks</h2>
                <ul>
                    <li><b>Staff directory:</b> add and update staff records,
                    assign a unit and personnel type, and manage active status.</li>
                    <li><b>Data &amp; backups:</b> save a database backup to a
                    secure location or restore a previously saved backup.
                    Restoring replaces the current database.</li>
                    <li><b>Settings:</b> change the shared Admin or Staff
                    password. On a shared server, manage paired workstations,
                    their backup status, and workstation access.</li>
                    <li><b>Reports and exports:</b> use the available report
                    and export pages to review or save operational information.</li>
                </ul>
                <h2>Shared server administration</h2>
                <p>Keep the base-server computer running while workstations
                need shared data. Generate a pairing code from Settings for
                authorized PCs. Block a paired PC to disconnect it and prevent
                sign-in; unblock it to restore access. A workstation backup is
                complete only while it matches the current server database.</p>
                <p>To prepare a server handoff, save a current backup on the
                selected PC, start that PC in shared-server mode, restore its
                backup there, and pair the other PCs to its new pairing code.
                Keep the old server running until the new server has been
                checked.</p>
            """

        return f"""
            <html>
            <body>
                <h1>Matrix Prime Hospital Help</h1>
                <p><b>Version:</b> {APP_VERSION}</p>
                <h2>Getting started</h2>
                <ol>
                    <li>Sign in with the shared Admin or Staff password provided
                    by your hospital administrator.</li>
                    <li>Use the navigation on the left to open a workspace.
                    Your available pages depend on your role.</li>
                    <li>For attendance, enter the staff member's Staff ID and
                    follow the check-in or sign-out prompts.</li>
                </ol>
                <h2>Using the workspaces</h2>
                <ul>
                    <li><b>Dashboard:</b> view an overview of current operations.</li>
                    <li><b>Roster:</b> review scheduled shifts for a date.</li>
                    <li><b>Attendance:</b> record a staff member's arrival or
                    departure using their Staff ID.</li>
                    <li><b>Attendance history:</b> review recorded attendance
                    for the available dates.</li>
                </ul>
                {admin_topics}
                <h2>Troubleshooting</h2>
                <ul>
                    <li><b>Cannot sign in:</b> check the password and confirm
                    whether you should use Admin or Staff access. Ask an Admin
                    to reset a shared password if needed.</li>
                    <li><b>Cannot connect to shared data:</b> check that the
                    server computer is powered on, the app is running, and
                    both computers are connected to the hospital network.
                    Contact hospital IT if the connection or firewall may
                    have changed.</li>
                    <li><b>Pairing code rejected:</b> ask an Admin for a new
                    code. Pairing codes expire after five minutes.</li>
                    <li><b>Backup shows out of date:</b> create a new backup
                    from Data &amp; backups on that workstation. A server data
                    change makes previous workstation backups out of date.</li>
                    <li><b>Something still is not working:</b> note the exact
                    message and what you were doing, then contact your
                    hospital's Matrix Prime Hospital administrator or IT
                    support.</li>
                </ul>
                <h2>Support</h2>
                <p>For account access, workstation pairing, or application
                issues, contact your hospital's system administrator or IT
                support team. Do not send passwords or unprotected backup
                files in support requests.</p>
            </body>
            </html>
        """
