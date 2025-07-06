\# 🤖 Zap Ágil



\*\*Zap Ágil\*\* is a powerful automation tool for sending personalized WhatsApp Web messages with attachments, scheduled campaigns, audio recordings, and detailed delivery reports. Its accessible GUI is built with wxPython, offering full control via mouse and keyboard shortcuts.



Developed by \*\*MHC Softwares\*\*.



---



\## ⚙️ Features



\- ✅ Automated sending of messages to contacts and groups  

\- 📁 Support for contact lists in `.txt` or `.xlsx`  

\- 🗑️ Campaign scheduling by day and time  

\- 📎 Attachments: documents, images, audio  

\- 🎙️ Record audio from within the interface  

\- 📊 Delivery reports in CSV format  

\- 🔄 Auto-reconnect on WhatsApp Web reload  

\- ♿ A fully accessible and keyboard-navigable interface (wxPython)  

\- 🧠 Invalid number detection and error feedback  

\- ⚖️ Built-in logging and visual notifications



---



\## 🔧 How It Works



\### 🪀 General Overview



Zap Ágil automates WhatsApp message sending through browser control using Selenium, while handling audio, file operations, and scheduling with robust Python libraries.



\### 📢 Message Engine (Core)



\- Controls WhatsApp Web in a real browser using Selenium and `webdriver-manager`  

\- Sends messages individually, typed or as media/audio attachments  

\- Detects invalid numbers and logs/report them accordingly



\### ⏰ Scheduler



\- Uses `APScheduler` for precise date and time control  

\- Supports both one-time and recurring tasks



\### 💾 Contact Import



\- Accepts `.txt` and `.xlsx` using `openpyxl`  

\- Contacts can be added/edited manually via the interface



\### 🎧 Audio Handling



\- Records audio using `sounddevice`, saves in OGG/Opus with `soundfile`  

\- Playback includes pause/resume using event control



\### 📈 Reports



\- All deliveries, statuses, and errors are logged  

\- Exportable to CSV with timestamp and campaign grouping



\### 📝 Configuration and Templates



\- Editable/savable message templates with variables like `@Name`, `@DueDate`  

\- Settings persist automatically across sessions



---



\## 🌐 Accessibility and UX



\- GUI built with `wxPython`  

\- Full keyboard navigation (Tab, Alt, arrow keys)  

\- Shortcuts for all functions (Ctrl+N, Ctrl+D, etc.)  

\- Tooltips on every button  

\- Compatible with screen readers



---



\## 📂 Project Structure



```

zap\_agil\_master/

├── zap\_agil/              # Main application code

├── tests/                 # Pytest test suite

├── assets/                # Icons, docs, static files

├── .vscode/               # Tasks and development settings

├── zap\_agil.pyw           # App launcher

├── zap\_agil.spec          # PyInstaller build config

├── requirements.txt

├── dev-requirements.txt

├── pyproject.toml

└── README.md

```



---



\## 🚀 Getting Started



1\. \*\*Clone the repository\*\*



```bash

git clone https://github.com/your-username/zap-agil.git

cd zap-agil/zap\_agil\_master

```



2\. \*\*Create a virtual environment\*\*



```bash

python -m venv .venv

```



\- \*\*Windows:\*\*  

&nbsp; `.venv\\Scripts\\activate`



\- \*\*macOS/Linux:\*\*  

&nbsp; `source .venv/bin/activate`



3\. \*\*Install dependencies\*\*



```bash

pip install -r requirements.txt

```



\- For development:



```bash

pip install -r dev-requirements.txt

```



4\. \*\*Run the application\*\*



```bash

python zap\_agil/zap\_agil.pyw

```



---



\## 🦞 Usage Tips (Keyboard \& Mouse)



\### Navigation



\- `Ctrl+Tab`: Switch between tabs  

\- `Alt`: Activate menu bar



\### Global Shortcuts



\- `Ctrl+Q`: Quit app  

\- `Ctrl+M`: Minimize to tray  

\- `Ctrl+T`: Open templates  

\- `Ctrl+A`: Schedule campaigns  

\- `Ctrl+R`: View reports  

\- `Ctrl+G`: Open settings  

\- `Ctrl+N`: Read news  

\- `Ctrl+D`: Read usage tips



\### Message Sending



\- Enter contact: type + press Enter  

\- Add manually: fill + `Ctrl+Enter`  

\- Remove: select + `Delete`  

\- Load list file: click or `Ctrl+B`



\### Message \& Attachments



\- Use variables like `@Name`, `@DueDate`  

\- Attach document: `Ctrl+D`  

\- Attach media: `Ctrl+I`  

\- Attach audio: `Ctrl+A`  

\- Record: ● Record → click to stop  

\- Play/Pause: ▶ / ❚❚



\### Templates



\- New: `Ctrl+N`  

\- Save: `Ctrl+S`  

\- Delete: `Ctrl+D`  

\- Attach: `Ctrl+B`  

\- Remove: `Ctrl+R`  

\- Close: `Esc`



\### Reports



\- Export CSV: `Ctrl+E`  

\- Delete: `Ctrl+D`  

\- Close: `Esc`



\### Scheduler



\- New: `Ctrl+N`  

\- Duplicate: `Ctrl+P`  

\- Delete: `Ctrl+D`  

\- Save: `Ctrl+S`  

\- Close: `Esc`



\### Mouse Users



\- Hover for tooltips  

\- Required fields are highlighted  

\- Use menus for all features



\### Keyboard Users



\- Navigate with Tab, Shift+Tab, arrow keys  

\- Alt to access menus  

\- Enter to confirm dialogs



---



\## ✅ Best Practices



\- Always review contact list before sending  

\- Use templates for recurring campaigns  

\- Analyze reports to monitor delivery  

\- Visit Help > Usage Tips for more



---



\## 📚 For Developers



\### Linting \& Formatting



```bash

ruff check .

ruff check . --fix

```



\- Or in VS Code:  

&nbsp; `Ctrl+Shift+P → Run Task → lint`



\### Testing



```bash

pytest

```



\### Building Executable



```bash

pyinstaller zap\_agil.spec

```



Output will be in `dist/zap\_agil/`



---



\*\*Enjoy!\*\*  

\_MHC Softwares\_

```



