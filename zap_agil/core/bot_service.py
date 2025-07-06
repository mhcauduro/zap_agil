"""
Orquestrador principal do backend do Zap Ágil. Implementa um padrão Observer
para notificar a UI sobre eventos, mantendo o core desacoplado.
"""

import os
import threading
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from zap_agil.utils.logging_config import logging

from .audio_manager import AudioManager
from .campaign_manager import CampaignManager
from .constants import (
    CONFIG_DIR_APP,
    CONFIG_DIR_COMPANY,
    REPORTS_SUBDIR_NAME,
    SCHEDULES_FILENAME,
    TEMP_AUDIO_FILENAME,
    TEMPLATES_SUBDIR_NAME,
    THEME_COLORS,
    CampaignState,
    ConnectionState,
)
from .report_manager import ReportManager
from .schedule_manager import ScheduleManager
from .template_manager import TemplateManager
from .web_driver_manager import WebDriverManager
from .whatsapp_manager import WhatsAppManager


class BotService:
    def notify(self, event_type: str, *args: object, **kwargs: object) -> None:
        """
        Notificação pública para uso externo (UI, managers, etc).
        """
        return self._notify(event_type, *args, **kwargs)

    # Mantém apenas uma definição de __init__

    # Contatos manuais
    def add_manual_contact(self, identifier: str) -> bool:
        """
        Adiciona um contato manualmente à campanha atual.
        Args:
            identifier (str): Identificador do contato (ex: número de telefone).
        Returns:
            bool: True se o contato foi adicionado, False caso contrário.
        """
        try:
            result = self.campaign_manager.add_manual_contact(identifier)
            logging.debug(f"Contato manual '{identifier}' adicionado: {result}")
            return result
        except Exception as e:
            logging.error(f"Erro ao adicionar contato manual '{identifier}': {e}")
            return False

    def clear_manual_contacts(self) -> None:
        """
        Limpa todos os contatos manuais da campanha atual.
        """
        try:
            self.campaign_manager.clear_manual_contacts()
            logging.debug("Contatos manuais limpos com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao limpar contatos manuais: {e}")

    """
    Orquestrador do backend (Façade). Gerencia a comunicação com a UI
    através de um sistema de subscrição de eventos (Observer Pattern).
    """

    def __init__(self):
        # --- Estado da Aplicação ---
        self.connection_state = ConnectionState.DISCONNECTED
        self.campaign_state = CampaignState.IDLE
        self.campaign_thread: threading.Thread | None = None

        # --- Controle de Threads ---
        self.pause_event = threading.Event()
        self.pause_event.set()  # Inicia "setado" (não pausado)

        # --- Sistema de Notificação (Observer Pattern) ---

        self.subscribers: defaultdict[str, list[Callable[..., Any]]] = defaultdict(list)

        # --- Inicialização de Paths ---
        self._initialize_data_dirs()

        # --- Inicialização dos Módulos (Managers) ---
        self.webdriver_manager = WebDriverManager(self)
        self.whatsapp_manager = WhatsAppManager(self)
        self.campaign_manager = CampaignManager(self)
        self.template_manager = TemplateManager(self)
        self.report_manager = ReportManager(self)
        self.schedule_manager = ScheduleManager(self)
        self.audio_manager = AudioManager(self)

    # --- Métodos do Sistema de Notificação ---

    def subscribe(self, event_type: str, callback: Callable[..., object]) -> None:
        """
        Permite que um componente (ex: a UI) se inscreva para ouvir um evento.
        Evita duplicidade de callbacks.
        """
        if callback not in self.subscribers[event_type]:
            self.subscribers[event_type].append(callback)
            logging.debug(f"Callback inscrito para evento '{event_type}'.")

    def _notify(self, event_type: str, *args: object, **kwargs: object) -> None:
        """
        Notifica todos os inscritos de um determinado evento,
        removendo callbacks inválidos automaticamente.
        """
        subscribers = self.subscribers.get(event_type, [])
        to_remove = []
        for callback in subscribers:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logging.exception(f"Erro ao executar callback para o evento '{event_type}': {e}")
                self.notify(
                    "log",
                    f"ERRO: Falha ao executar callback para o evento '{event_type}': {e}",
                    "#ff5555",  # vermelho para erro
                )
                to_remove.append(callback)
        # Remove callbacks que deram erro (ex: objetos destruídos)
        for cb in to_remove:
            try:
                subscribers.remove(cb)
            except Exception as e:
                logging.exception(f"Erro ao remover callback inválido: {e}")
                self.notify(
                    "log",
                    f"ERRO ao remover callback inválido: {e}",
                    "#ff5555",
                )

    # --- Lógica de Negócio Principal ---
    def _initialize_data_dirs(self) -> None:
        """
        Garante que todos os diretórios de dados necessários existam.
        """
        if os.name == "nt":  # Windows
            base_dir = Path(os.getenv("APPDATA", Path.home()))
        else:  # Linux, macOS
            base_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))

        self.app_data_dir = base_dir / CONFIG_DIR_COMPANY / CONFIG_DIR_APP
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Diretório de dados da aplicação: {self.app_data_dir}")

        self.templates_attachments_dir = self.app_data_dir / TEMPLATES_SUBDIR_NAME
        self.templates_attachments_dir.mkdir(exist_ok=True)
        logging.debug(f"Diretório de anexos de modelos: {self.templates_attachments_dir}")

        self.reports_dir = self.app_data_dir / REPORTS_SUBDIR_NAME
        self.reports_dir.mkdir(exist_ok=True)
        logging.debug(f"Diretório de relatórios: {self.reports_dir}")

        self.schedules_filepath = self.app_data_dir / SCHEDULES_FILENAME

        cache_dir = self.app_data_dir / "Cache"
        cache_dir.mkdir(exist_ok=True)
        self.temp_audio_path = cache_dir / TEMP_AUDIO_FILENAME
        logging.debug(f"Diretório de cache: {cache_dir}")

    def start_connection(self) -> None:
        """
        Inicia a conexão com o WhatsApp em uma thread separada para não bloquear a UI.
        """
        if self.connection_state not in [
            ConnectionState.DISCONNECTED,
            ConnectionState.FAILED,
        ]:
            logging.info("Conexão já está ativa ou em andamento.")
            return
        logging.info("Iniciando conexão com o WhatsApp.")
        threading.Thread(target=self.webdriver_manager.initialize_driver, daemon=True).start()

    def shutdown(self) -> None:
        """
        Encerra todos os serviços de forma segura.
        """
        logging.info("Encerrando todos os serviços do BotService.")
        self._notify("log", "Encerrando serviços...", THEME_COLORS["log_warning"])
        if self.campaign_thread and self.campaign_thread.is_alive():
            self.campaign_state = CampaignState.STOPPED
            self.pause_event.set()  # Libera a pausa para que a thread possa terminar

        self.schedule_manager.shutdown()
        self.webdriver_manager.shutdown()
        self.audio_manager.discard_recorded_audio()

    def start_campaign(self, campaign_config: dict[str, Any]) -> None:
        """
        Inicia uma campanha em uma thread separada.
        """
        if self.campaign_thread and self.campaign_thread.is_alive():
            logging.warning("Tentativa de iniciar campanha enquanto já existe uma em andamento.")
            self._notify(
                "log",
                "Já existe uma campanha em andamento.",
                THEME_COLORS["log_warning"],
            )
            return

        self.pause_event.set()  # Garante que a campanha não comece pausada

        self.campaign_thread = threading.Thread(
            target=self.campaign_manager.run_campaign,
            args=(campaign_config,),
            daemon=True,
        )
        self.campaign_thread.start()

    def stop_campaign(self) -> None:
        """
        Para a campanha atual.
        """
        if self.campaign_state in [CampaignState.RUNNING, CampaignState.PAUSED]:
            logging.info("Campanha interrompida pelo usuário.")
            self.campaign_state = CampaignState.STOPPED
            self.pause_event.set()  # Libera a pausa para que a thread possa parar
            self._notify(
                "log",
                "Campanha interrompida pelo usuário.",
                THEME_COLORS["log_warning"],
            )

    def toggle_pause_campaign(self) -> None:
        """
        Pausa ou retoma a campanha usando um threading.Event.
        """
        if self.campaign_state == CampaignState.RUNNING:
            logging.info("Campanha pausada pelo usuário.")
            self.pause_event.clear()  # Pausa a thread da campanha
            self.campaign_state = CampaignState.PAUSED
            self._notify("log", "Campanha pausada.", THEME_COLORS["log_warning"])
        elif self.campaign_state == CampaignState.PAUSED:
            logging.info("Campanha retomada pelo usuário.")
            self.pause_event.set()  # Libera a thread da campanha
            self.campaign_state = CampaignState.RUNNING
            self._notify("log", "Campanha retomada.", THEME_COLORS["log_info"])

        self._notify("campaign_status", self.campaign_state)

    # --- Métodos "Pass-Through" para os Managers ---
    # A UI chama estes métodos, e o BotService delega para o manager correto.

    # Audio Manager
    def start_recording(self):
        self.audio_manager.start_recording()

    def stop_recording(self):
        self.audio_manager.stop_recording()

    def play_recorded_audio(self):
        self.audio_manager.play_recorded_audio()

    def pause_playback(self):
        self.audio_manager.pause_playback()

    def resume_playback(self):
        self.audio_manager.resume_playback()

    def discard_recorded_audio(self):
        self.audio_manager.discard_recorded_audio()

    def get_audio_duration(self, file_path: str) -> float | None:
        return self.audio_manager.get_audio_duration(file_path)

    # Template Manager
    def get_templates(self) -> list[dict[str, Any]]:
        return self.template_manager.get_templates()

    def save_template(self, data: dict[str, Any]) -> str | None:
        return self.template_manager.save_template(data)

    def delete_template(self, tpl_id: str) -> bool:
        return self.template_manager.delete_template(tpl_id)

    # Report Manager
    def get_reports(self) -> list[str]:
        return self.report_manager.get_reports()

    def get_report_content(self, fname: str) -> str:
        return self.report_manager.get_report_content(fname)

    def delete_report(self, fname: str) -> bool:
        return self.report_manager.delete_report(fname)

    def export_report_to_csv(self, r_fname: str, c_path: str) -> bool:
        return self.report_manager.export_report_to_csv(r_fname, c_path)

    # Schedule Manager
    def get_schedules(self) -> list[dict[str, Any]]:
        return self.schedule_manager.get_schedules()

    def save_schedule(self, data: dict[str, Any]) -> str | None:
        return self.schedule_manager.save_schedule(data)

    def delete_schedule(self, sch_id: str) -> bool:
        return self.schedule_manager.delete_schedule(sch_id)

    def get_next_run_time(self, sch_id: str) -> datetime | None:
        return self.schedule_manager.get_next_run_time(sch_id)
