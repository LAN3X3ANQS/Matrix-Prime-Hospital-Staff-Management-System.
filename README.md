# Matrix Prime Hospital

Matrix Prime Hospital is a local desktop application for workforce rosters,
attendance, leave records, shift changes, reports, and exports.

## Run

Install the packages listed in `requirements.txt`, then launch the application
from the project directory:

```powershell
python -m pip install -r requirements.txt
python main.py
```

To build a Windows executable, install PyInstaller and package the cryptography
runtime with the app:

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile `
  --name MatrixPrimeHospital `
  --icon assets\matrix-prime-hospital.ico `
  --add-data "assets\matrix-prime-hospital.ico;assets" `
  --collect-all cryptography `
  main.py
```

The executable and app windows use the Matrix Prime Hospital blue-and-white
“M” icon with a green medical-cross tile.

Test the executable on the intended server and workstation computers before
distribution. The server computer's Windows firewall must permit the app's
private-network TCP listener (port 48731); ask hospital IT to apply a
private-network-only rule rather than exposing it publicly.

On a fresh database, the application creates separate, random Admin and Staff
passwords and displays them once in the setup dialog and launching terminal.
Set `NURSEROSTER_ADMIN_PASSWORD` and/or `NURSEROSTER_STAFF_PASSWORD` before the
first launch to provision chosen passwords instead. Seeded passwords must be
at least 6 characters; Admin and Staff passwords must differ. The database
stores password hashes and salts, not plaintext passwords. Generated passwords
are shown only at creation time, so record them securely. There is no first-run
password setup screen; Admin can change the shared passwords from **Settings**.

The authentication table is initialized alongside the existing application
tables. Existing nurse, roster, attendance, leave, and shift data is preserved.

## Staff directory

Admin can register and manage staff records in the Staff Directory. Current
categories are **Admin**, **Janitor**, **Front Desk**, **Nurse**, **Lab Tech**,
and **Doctor**. Each record has a unique generated Staff ID, unit, status,
optional profile picture, and roster rotation. The shared Admin and Staff
passwords remain shared application roles and are not individual personnel
accounts. An **Admin** staff type in the directory is an employee record, not
an individual application account. Attendance uses each worker's Staff ID and
records their directory category.

New Staff IDs use `MPH-{type abbreviation}-{YY}{sequence}` and the sequence
starts at `0001` for each staff type in each calendar year (for example,
`MPH-ADM-260001`). IDs already assigned to existing staff remain unchanged.

The roster follows a stable six-day rotation, so looking at the same date in
different roster date ranges gives the same shift. Attendance records separately
capture sign-in and sign-out for each Morning or Night shift. The 30-day profile
reliability score is on-time check-ins divided by scheduled shifts, excluding
approved leave; it is not a measure of job performance.

Janitors, Admin staff, Lab Techs, and Front Desk staff are scheduled every day
on a 8:00 AM–6:00 PM day shift and do not receive a rotating roster assignment.
Nurses and Doctors continue to use the six-day rotating shift patterns.
Sign-outs before the scheduled shift end are recorded as **Early**. Sign-out
is accepted until 30 minutes after the scheduled shift end; after that cutoff,
the open sign-in can no longer be closed.

## Data sharing and backups

The app supports a **hospital LAN server**. On the computer designated as the
server, launch the app and choose **Make this computer the shared server**.
Keep that computer and app running. Copy the server address, port, six-digit
PIN, and TLS fingerprint shown in the server window to each workstation. On
the workstation, choose **Connect to a shared server** and enter those
details. Compare the TLS fingerprint shown on both computers before
connecting; do not continue if they differ. The client saves its server
connection; staff still sign in with the shared Admin or Staff password. The
Admin Settings page on the server computer can generate another PIN or revoke
all paired computers.

The server uses an encrypted TLS connection with a certificate fingerprint
verified against the server's displayed fingerprint during pairing. PINs
expire after five minutes and can pair multiple hospital workstations during
that window. Share them only with authorized computers on the hospital
network. Before deployment, hospital IT should assign the server computer a
stable private-network address and allow inbound TCP port **48731** only on
the hospital's private network.
Do not expose this port to the public internet. The server rejects connections
from public IP addresses, but firewall configuration is still required.

The server computer is the single source of truth and should be a dedicated,
reliable machine with restricted Windows access and regular backups. If it is
shut down or the app is closed, connected workstations cannot use shared data.
This provides LAN sharing only; it does not connect remote US and Nigeria
locations over the internet. A VPN or centrally hosted service would be needed
for that and requires separate hospital approval.

Admins can use **Settings** on the server or a paired workstation to review
paired PCs, block or unblock a workstation, and check whether its locally
saved backup matches the current server database. Each workstation must create
a backup from **Data & backups**; any server data changes make that backup
out of date. A PC with a complete backup can be selected to prepare a base
server change. The handoff is coordinated: start that PC in shared-server
mode, restore its saved backup, then pair the remaining PCs to the new server
with its new connection details and PIN. Settings does not remotely start
another PC's server.

Data & backups can create and restore full database backup files. In shared
mode, backups are created from and restored to the server database. Backup
files contain staff data, profile pictures, attendance, and password hashes;
they are not encrypted by the app. Store and transfer them only through
hospital-approved protected storage. When moving existing local data to a
new server, create a backup from the old installation and restore it on the
server computer before pairing workstations. Close connected workstations
before restoring a shared backup.

## Access

- The **Help** page is available to Admin and Staff and includes quick-start
  guidance, workspace instructions, common troubleshooting steps, version
  information, and where to request hospital support.
- **Admin** has access to every workspace, including staff management,
  analytics, reports, leave and shift records, exports, and password settings.
- **Staff** has access to the dashboard, roster, attendance sign-in/sign-out, and
  attendance history only. Staff cannot open Admin-only pages; those pages are
  not created in a Staff session.

Both roles use a shared password rather than individual accounts. The entered
Staff ID identifies the worker being checked in; it does not identify the
operator using the application.