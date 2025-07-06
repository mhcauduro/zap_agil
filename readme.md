🤖 Zap Ágil

Zap Ágil is a powerful automation tool for sending personalized WhatsApp Web messages with attachments, scheduled campaigns, audio recordings, and detailed delivery reports. Its accessible GUI is built with wxPython, offering full control via mouse and keyboard shortcuts.

Developed by MHC Softwares.

⚙️ Features

✅ Automated sending of messages to contacts and groups

📁 Support for contact lists in .txt or .xlsx

🗑️ Campaign scheduling by day and time

📎 Attachments: documents, images, audio

🎙️ Record audio from within the interface

📊 Delivery reports in CSV format

🔄 Auto-reconnect on WhatsApp Web reload

♿ A fully accessible and keyboard-navigable interface (wxPython)

🧠 Invalid number detection and error feedback

⚖️ Built-in logging and visual notifications

🔧 How It Works

🪀 General Overview

Zap Ágil automates WhatsApp message sending through browser control using Selenium, while handling audio, file operations, and scheduling with robust Python libraries.

📢 Message Engine (Core)

Uses Selenium and webdriver-manager to control WhatsApp Web in a real browser window.

Sends messages individually, either typed or as audio/media attachments.

Detects if a number is invalid and logs/report it.

⏰ Scheduler

Campaigns can be scheduled using APScheduler, enabling precise control of sending date and time.

Supports one-time or recurring tasks.

💾 Contact Import

Accepts .txt and .xlsx files using openpyxl.

Users can also add/edit contacts manually in the interface.

🎧 Audio Handling

Records audio with sounddevice and saves with soundfile in OGG/Opus format.

Playback includes pause/resume using event control.

📈 Reports

All deliveries, statuses, and failures are logged and can be exported to CSV.

Timestamped, grouped by campaign.

📝 Configuration and Templates

Message templates are editable and savable with variables like @Name, @DueDate, etc.

Settings are stored and reloaded automatically.

🌐 Accessibility and UX

GUI built with wxPython

Fully usable by keyboard (Tab, Alt, arrows)

Shortcuts for all functions (Ctrl+N, Ctrl+D, etc.)

Tooltips on all buttons

Compatible with screen readers

📂 Project Structure

zap_agil_master/
├── zap_agil/              # Main application code
├── tests/                 # Pytest test suite
├── assets/                # Icons, docs, static files
├── .vscode/               # Tasks, settings for development
├── zap_agil.pyw           # App launcher
├── zap_agil.spec          # PyInstaller config
├── requirements.txt
├── dev-requirements.txt
├── pyproject.toml
└── README.md

🚀 Getting Started

1. Clone the repository

git clone https://github.com/your-username/zap-agil.git
cd zap-agil/zap_agil_master

2. Create virtual environment

python -m venv .venv

Windows:

.venv\Scripts\activate

macOS/Linux:

source .venv/bin/activate

3. Install dependencies

pip install -r requirements.txt

For development:

pip install -r dev-requirements.txt

4. Run the application

python zap_agil/zap_agil.pyw

🦞 Usage Tips (Keyboard & Mouse)

Navigation

Ctrl+Tab: Switch between tabs

Alt: Activate menu bar

Global Shortcuts

Ctrl+Q: Quit app

Ctrl+M: Minimize to tray

Ctrl+T: Open templates

Ctrl+A: Schedule campaigns

Ctrl+R: View reports

Ctrl+G: Open settings

Ctrl+N: Read news

Ctrl+D: Read usage tips

Message Sending

Enter contact: type + press Enter

Manual list add: fill + Ctrl+Enter

Remove contact: select + Delete

Load contact file: click or Ctrl+B

Message & Attachments

Write message using variables (@Name, @DueDate)

Attach document: Ctrl+D

Attach media: Ctrl+I

Attach audio: Ctrl+A

Record: ● Record → click to stop

Play/Pause: ▶ / ❚❚

Templates

New: Ctrl+N

Save: Ctrl+S

Delete: Ctrl+D

Attach: Ctrl+B

Remove: Ctrl+R

Close: Esc

Reports

Export CSV: Ctrl+E

Delete: Ctrl+D

Close: Esc

Scheduler

New: Ctrl+N

Duplicate: Ctrl+P

Delete: Ctrl+D

Save: Ctrl+S

Close: Esc

Mouse Users

Hover for tooltips

Required fields are highlighted

Use menus to access any feature

Keyboard Users

Navigate with Tab, Shift+Tab, arrows

Use Alt to access menus

Enter to confirm actions in dialogs

Recommendations

Always review contact list before sending

Use templates for recurring campaigns

Analyze reports to monitor delivery

Help > Usage Tips for more

📚 For Developers

Linting & Formatting

Run manually:

ruff check .
ruff check . --fix

Or use VS Code task: Ctrl+Shift+P → Run Task → lint

Testing

pytest

Building the .exe

pyinstaller zap_agil.spec

Creates output in dist/zap_agil/

Enjoy!

MHC Softwares

