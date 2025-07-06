"""
Gerencia o arquivo de configuração principal (config.ini) do Zap Fácil.
"""

import os
from configparser import ConfigParser
from pathlib import Path
from typing import Optional

from zap_agil.core.constants import CONFIG_DIR_APP, CONFIG_DIR_COMPANY, CONFIG_FILENAME
from zap_agil.utils.logging_config import logging


class ConfigManager:
    """
    Classe dedicada a gerenciar as configurações do arquivo INI.
    """

    _instance: Optional["ConfigManager"] = None

    def __new__(cls):
        # Padrão Singleton para garantir uma única instância do ConfigManager
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Determina o diretório de configuração baseado no SO
        if os.name == "nt":  # Windows
            app_data_dir = os.getenv("APPDATA")
        else:  # Linux, macOS, etc.
            app_data_dir = os.path.join(os.path.expanduser("~"), ".config")

        if not app_data_dir:  # Fallback para o diretório home
            app_data_dir = os.path.expanduser("~")

        self._config_dir = Path(app_data_dir) / CONFIG_DIR_COMPANY / CONFIG_DIR_APP
        self._config_dir.mkdir(parents=True, exist_ok=True)

        self._config_path = self._config_dir / CONFIG_FILENAME
        self._config = ConfigParser()
        self._load_or_create_config()
        self._initialized = True

    def _load_or_create_config(self) -> None:
        """Carrega o arquivo de configuração ou cria um novo com valores padrão se não existir."""
        if not self._config_path.exists():
            self._create_default_config()
        else:
            self._config.read(self._config_path, encoding="utf-8")

    def _create_default_config(self) -> None:
        """Cria a estrutura e os valores padrão para o config.ini."""
        self._config["General"] = {
            "disclaimer_accepted": "false",
            "start_on_boot": "false",
        }
        self._config["Campaign"] = {"default_delay": "2"}
        self.save_config()

    def get_setting(self, section: str, key: str, fallback: str = "") -> str:
        """
        Obtém uma configuração do arquivo.

        Args:
            section (str): A seção do arquivo .ini.
            key (str): A chave da configuração.
            fallback (str): Valor padrão a ser retornado se a chave não for encontrada.

        Returns:
            str: O valor da configuração.
        """
        return self._config.get(section, key, fallback=fallback)

    def get_boolean_setting(self, section: str, key: str, fallback: bool = False) -> bool:
        """
        Obtém uma configuração e a converte para booleano.

        Args:
            section (str): A seção do arquivo .ini.
            key (str): A chave da configuração.
            fallback (bool): Valor padrão a ser retornado.

        Returns:
            bool: O valor booleano da configuração.
        """
        fallback_str = "true" if fallback else "false"
        value_str = self.get_setting(section, key, fallback=fallback_str)
        return value_str.lower() == "true"

    def save_setting(self, section: str, key: str, value: str) -> None:
        """
        Salva uma configuração no arquivo.

        Args:
            section (str): A seção do arquivo .ini.
            key (str): A chave da configuração.
            value (str): O valor a ser salvo.
        """
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, str(value))
        self.save_config()

    def save_config(self) -> None:
        """Salva o objeto de configuração atual no arquivo .ini."""
        try:
            with open(self._config_path, "w", encoding="utf-8") as configfile:
                self._config.write(configfile)
        except OSError as e:
            logging.error(f"Erro ao salvar config.ini: {e}")
