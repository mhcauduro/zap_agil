"""
Centraliza todas as constantes e enums do Zap Ágil para facilitar a manutenção.
"""

# Imports
import os
from enum import Enum, auto
from pathlib import Path

# --- Enums para Tipos e Estados ---


class SourceType(Enum):
    MANUAL_LIST = auto()
    LIST = auto()
    GROUP_LIST = auto()


class AudioState(Enum):
    IDLE = auto()
    RECORDING = auto()
    PLAYING = auto()
    PAUSED = auto()
    READY = auto()


class ConnectionState(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    NEEDS_QR_SCAN = auto()
    CONNECTED = auto()
    FAILED = auto()


class CampaignState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    FINISHED = auto()


# --- Informações do Aplicativo ---
APP_NAME = "Zap Ágil"
COMPANY_NAME = "MHC Softwares"
APP_VERSION = "1.0.0"


# --- Nomes de Arquivos e Diretórios ---
# Usados para construir os caminhos dinamicamente no bot_service.py
CONFIG_DIR_COMPANY = "MHC Softwares"
CONFIG_DIR_APP = "Zap Ágil"
CONFIG_FILENAME = "config.ini"
SCHEDULES_FILENAME = "schedules.json"
TEMPLATES_FILENAME = "templates.json"
REPORTS_SUBDIR_NAME = "Relatorios"  # Sem acento, para compatibilidade
TEMPLATES_SUBDIR_NAME = "Templates"
TEMP_AUDIO_FILENAME = "zapagil_temp_audio.ogg"

# --- Diretórios e arquivos de log ---

APPDATA_PATH = Path(os.getenv("APPDATA", Path.home()))
APPDATA_ZAPAGIL_DIR = APPDATA_PATH / CONFIG_DIR_COMPANY / CONFIG_DIR_APP
LOGS_DIRNAME = "Logs"
LOGS_PATH = APPDATA_ZAPAGIL_DIR / LOGS_DIRNAME
LOGS_PATH.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOGS_PATH / "zapAgil_debug.log"

# --- Assets da UI ---
APP_ICON_FILENAME = "assets/icons/app_icon.ico"
CLIENT_LOGO_FILENAME = "assets/logo.png"
MIC_ICON_FILENAME = "assets/icons/mic_icon.png"

# --- Configurações do Bot e WhatsApp ---
PHONE_COUNTRY_CODE = "55"
IMAGE_VIDEO_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webp"]
AUDIO_EXTENSIONS = [".ogg", ".opus", ".mp3", ".wav", ".m4a"]
DOCUMENT_EXTENSIONS = [
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".7z",
    ".zip",
    ".rar",
    ".txt",
    ".csv",
]

# --- Configurações de Áudio ---
AUDIO_SAMPLERATE = 48000
AUDIO_CHANNELS = 1
AUDIO_DTYPE = "float32"

# --- Delays Humanos (ms, convertido para segundos nos managers) ---
# Usando valores <50ms para digitação/busca natural e rápida:
HUMAN_TYPING_DELAY_MIN = 0.02
HUMAN_TYPING_DELAY_MAX = 0.05
AUDIO_THREAD_DELAY = 0.05  # 50 ms, gravação de áudio
AUDIO_STOP_DELAY = 0.08  # 80 ms, pausa para garantir fim da thread de áudio

# --- Textos Padrão ---
DEFAULT_CAMPAIGN_MSG = "Olá @Nome, tudo bem?\nEsta é uma mensagem de teste do Zap Ágil!"

# --- Configurações da Interface ---
THEME_COLORS = {
    "background": "#2C3E50",
    "panel": "#34495E",
    "text": "#ECF0F1",
    "text_light": "#888888",
    "primary": "#1ABC9C",
    "accent_red": "#E74C3C",
    "accent_yellow": "#F1C40F",
    "accent_purple": "#9B59B6",
    "log_info": "#3498DB",
    "log_success": "#2ECC71",
    "log_warning": "#F39C12",
    "log_error": "#E74C3C",
}

# --- Wildcards para Diálogos de Arquivo ---
WILDCARD_CONTACTS = "Lista de contatos (*.txt;*.xlsx)|*.txt;*.xlsx"
WILDCARD_MEDIA = (
    "Mídia (Imagem, Vídeo, Áudio)|"
    "*.jpg;*.jpeg;*.png;*.gif;*.mp4;*.webp;*.ogg;*.opus;*.mp3;*.wav;*.m4a"
)
WILDCARD_DOCUMENTS = (
    "Documentos (*.pdf;*.docx;*.xlsx;*.zip;*.rar)|"
    "*.pdf;*.doc;*.docx;*.xls;*.xlsx;*.ppt;*.pptx;*.zip;*.rar;*.txt;*.csv"
)
WILDCARD_ALL_ATTACHMENTS = f"{WILDCARD_MEDIA}|{WILDCARD_DOCUMENTS}"
WILDCARD_AUDIO = "Áudio (*.mp3;*.wav;*.ogg;*.m4a)|*.mp3;*.wav;*.ogg;*.m4a"
