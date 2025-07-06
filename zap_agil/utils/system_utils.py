"""
Utilitários de sistema para o Zap Fácil.
"""

import os
import sys
from pathlib import Path

from zap_agil.utils.logging_config import logging


def resource_path(relative_path: str) -> str:
    """Obtém o caminho absoluto para um recurso."""
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Em modo de desenvolvimento, sobe dois níveis para chegar na raiz do pacote
        base_path = Path(__file__).resolve().parent.parent
    return str(base_path / relative_path)


def add_to_startup(enable: bool = True) -> bool:
    """
    Adiciona ou remove o app da inicialização do Windows usando um arquivo .bat na pasta
    Startup do usuário.

    Args:
        enable: True para adicionar/criar, False para remover.
    Returns:
        True se a operação foi bem-sucedida, False caso contrário.
    """
    if not enable:
        return remove_from_startup()

    try:
        # Caminho para a pasta Startup do usuário
        startup_dir = os.path.join(
            os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        # Caminho do executável/script atual
        app_path = Path(sys.executable)
        # Caminho do .bat
        bat_path = os.path.join(startup_dir, "zap_agil_startup.bat")

        # Gera o comando para iniciar o app
        # Se for um .exe, executa direto; se for .py, usa python
        if app_path.suffix.lower() == ".exe":
            cmd = f'start "" "{app_path}"\r\n'
        else:
            cmd = f'start "" "{sys.executable}" "{app_path}"\r\n'

        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(cmd)
        return True
    except Exception as e:
        logging.error(f"Erro ao criar .bat de inicialização: {e}")
        return False


def remove_from_startup() -> bool:
    """
    Remove o arquivo .bat de inicialização da pasta Startup do usuário.
    """
    try:
        startup_dir = os.path.join(
            os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        bat_path = os.path.join(startup_dir, "zap_agil_startup.bat")
        if os.path.exists(bat_path):
            os.remove(bat_path)
        return True
    except Exception as e:
        logging.error(f"Erro ao remover .bat de inicialização: {e}")
        return False


def is_in_startup() -> bool:
    """
    Verifica se o arquivo .bat de inicialização existe na pasta Startup do usuário.
    """
    try:
        startup_dir = os.path.join(
            os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        bat_path = os.path.join(startup_dir, "zap_agil_startup.bat")
        return os.path.exists(bat_path)
    except Exception:
        return False
