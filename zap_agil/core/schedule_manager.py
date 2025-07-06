"""
Gerencia a lógica de agendamento de campanhas, utilizando apscheduler
para executar tarefas em horários programados de forma robusta.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from zap_agil.utils.json_utils import load_json_file, save_json_file
from zap_agil.utils.logging_config import logging

from .constants import THEME_COLORS

# --- CORREÇÃO: Bloco para resolver a referência circular de tipo ---
if TYPE_CHECKING:
    from zap_agil.core.bot_service import BotService


class ScheduleManager:
    """Gerencia o agendamento de campanhas."""

    def __init__(self, bot_service: "BotService"):
        self.bot_service = bot_service
        self.schedules_filepath = bot_service.schedules_filepath
        self.scheduler: BackgroundScheduler | None = None
        self._initialize_scheduler()
        logging.debug("ScheduleManager inicializado.")

    def _initialize_scheduler(self) -> None:
        """Inicializa o agendador e carrega os jobs existentes."""
        try:
            self.scheduler = BackgroundScheduler(daemon=True, timezone="America/Sao_Paulo")
            self.scheduler.start()
            self.reschedule_all_jobs()
            logging.info("Agendador inicializado e jobs recarregados.")
        except Exception as e:
            self.bot_service._notify(
                "log",
                f"ERRO CRÍTICO ao iniciar o agendador: {e}",
                THEME_COLORS["log_error"],
            )
            logging.error(f"ERRO CRÍTICO ao iniciar o agendador: {e}")

    def shutdown(self) -> None:
        """Encerra o agendador de forma segura."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.bot_service._notify(
                "log", "[AGENDADOR] Scheduler encerrado.", THEME_COLORS["log_warning"]
            )
            logging.info("Scheduler encerrado.")

    def get_schedules(self) -> list[dict[str, Any]]:
        """Carrega e retorna a lista de agendamentos do arquivo JSON."""
        schedules = load_json_file(self.schedules_filepath, default=[])
        logging.debug(f"{len(schedules)} agendamentos carregados.")
        return schedules

    def save_schedule(self, schedule_data: dict[str, Any]) -> str | None:
        """Salva um novo agendamento ou atualiza um existente."""
        schedules = self.get_schedules()
        schedule_id = schedule_data.get("id")

        if schedule_id and any(s.get("id") == schedule_id for s in schedules):
            index = next((i for i, s in enumerate(schedules) if s.get("id") == schedule_id), -1)
            if index != -1:
                schedules[index] = schedule_data
        else:
            schedule_id = schedule_id or str(uuid.uuid4())
            schedule_data["id"] = schedule_id
            schedules.append(schedule_data)

        if save_json_file(self.schedules_filepath, schedules):
            self.reschedule_all_jobs()  # Sempre reagenda para refletir as mudanças
            self.bot_service._notify(
                "log",
                f"[AGENDADOR] Agendamento salvo/atualizado (ID: {schedule_id})",
                THEME_COLORS["log_success"],
            )
            logging.info(f"Agendamento salvo/atualizado (ID: {schedule_id})")
            return schedule_id
        self.bot_service._notify(
            "log",
            f"[AGENDADOR] Falha ao salvar o agendamento (ID: {schedule_id})",
            THEME_COLORS["log_error"],
        )
        logging.error(f"Falha ao salvar o agendamento (ID: {schedule_id})")
        return None

    def delete_schedule(self, schedule_id: str) -> bool:
        """Exclui um agendamento do arquivo e do scheduler."""
        schedules = self.get_schedules()
        schedules_to_keep = [s for s in schedules if s.get("id") != schedule_id]
        if len(schedules) == len(schedules_to_keep):
            self.bot_service._notify(
                "log",
                f"[AGENDADOR] Nenhum agendamento com o ID '{schedule_id}' encontrado.",
                THEME_COLORS["log_warning"],
            )
            logging.warning(
                f"Nenhum agendamento com o ID '{schedule_id}' encontrado para exclusão."
            )
            return False

        if save_json_file(self.schedules_filepath, schedules_to_keep):
            self.reschedule_all_jobs()
            self.bot_service._notify(
                "log",
                f"[AGENDADOR] Agendamento excluído (ID: {schedule_id})",
                THEME_COLORS["log_warning"],
            )
            logging.info(f"Agendamento excluído (ID: {schedule_id})")
            return True
        self.bot_service._notify(
            "log",
            f"[AGENDADOR] Falha ao excluir agendamento (ID: {schedule_id})",
            THEME_COLORS["log_error"],
        )
        logging.error(f"Falha ao excluir agendamento (ID: {schedule_id})")
        return False

    def get_next_run_time(self, schedule_id: str) -> datetime | None:
        """Retorna o próximo horário de execução de um job específico."""
        if self.scheduler and self.scheduler.running:
            job = self.scheduler.get_job(schedule_id)
            return job.next_run_time if job else None
        return None

    def reschedule_all_jobs(self) -> None:
        """Limpa e recarrega todos os jobs do scheduler a partir do arquivo JSON."""
        if not self.scheduler:
            return

        self.scheduler.remove_all_jobs()
        schedules = self.get_schedules()
        active_jobs_count = 0

        for schedule in schedules:
            if schedule.get("enabled", False):
                try:
                    trigger_info = schedule["trigger"]
                    # Novo: agendamento absoluto por data real
                    month = int(trigger_info["month"])
                    day = int(trigger_info["day"])
                    hour = int(trigger_info["hours"])
                    minute = int(trigger_info["minutes"])
                    year = datetime.now().year
                    run_date = datetime(year, month, day, hour, minute)
                    self.scheduler.add_job(
                        func=self._execute_scheduled_campaign,
                        trigger=DateTrigger(run_date=run_date, timezone="America/Sao_Paulo"),
                        id=schedule["id"],
                        args=[schedule["id"]],
                        name=schedule.get("name", "Campanha Agendada"),
                        replace_existing=True,
                    )
                    active_jobs_count += 1
                    msg = (
                        f"[AGENDADOR] Campanha programada para "
                        f"{run_date.strftime('%d/%m/%Y %H:%M')}: "
                        f"{schedule.get('name', schedule['id'])}"
                    )
                    self.bot_service._notify(
                        "log",
                        msg,
                        "gray",
                    )
                    logging.info(
                        f"Campanha programada para {run_date.strftime('%d/%m/%Y %H:%M')}: "
                        f"{schedule.get('name', schedule['id'])}"
                    )
                except Exception as e:
                    log_msg = f"[AGENDADOR] Erro ao programar '{schedule.get('name')}': {e}"
                    self.bot_service._notify("log", log_msg, THEME_COLORS["log_error"])
                    logging.error(log_msg)

        log_msg = (
            f"[AGENDADOR] {active_jobs_count} campanha(s) ativa(s)."
            if active_jobs_count > 0
            else "[AGENDADOR] Nenhum agendamento ativo."
        )
        log_color = THEME_COLORS["accent_purple"] if active_jobs_count > 0 else "gray"
        self.bot_service._notify("log", log_msg, log_color)
        logging.info(log_msg)

    def _execute_scheduled_campaign(self, schedule_id: str) -> None:
        """Função que é chamada pelo scheduler para executar uma campanha."""
        self.bot_service._notify(
            "log",
            f"[AGENDADOR] Disparando campanha (ID: {schedule_id})...",
            THEME_COLORS["accent_purple"],
        )
        logging.info(f"Disparando campanha agendada (ID: {schedule_id})...")

        schedule_to_run = next(
            (s for s in self.get_schedules() if s.get("id") == schedule_id), None
        )
        if not schedule_to_run:
            self.bot_service._notify(
                "log",
                f"[AGENDADOR] ERRO: Campanha {schedule_id} não encontrada.",
                THEME_COLORS["log_error"],
            )
            logging.error(f"Campanha agendada {schedule_id} não encontrada.")
            return

        if not self.bot_service.webdriver_manager.is_whatsapp_ready():
            self.bot_service._notify(
                "log",
                "[AGENDADOR] WhatsApp não conectado. A campanha será tentada no próximo horário.",
                THEME_COLORS["log_warning"],
            )
            logging.warning("WhatsApp não conectado para disparo de campanha agendada.")
            return

        self.bot_service.start_campaign(schedule_to_run.get("campaign_config", {}))
        logging.info(f"Campanha agendada (ID: {schedule_id}) disparada.")
