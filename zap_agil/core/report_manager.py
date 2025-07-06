"""
Gerencia a lógica de negócio para relatórios de campanhas no Zap Ágil,
incluindo listagem, leitura, exclusão e exportação para CSV.
"""

import csv
import re
from pathlib import Path
from typing import TYPE_CHECKING

from zap_agil.core.constants import THEME_COLORS
from zap_agil.utils.logging_config import logging

if TYPE_CHECKING:
    from zap_agil.core.bot_service import BotService


class ReportManager:
    """Gerencia a lógica de negócio de relatórios de campanhas."""

    def __init__(self, bot_service: "BotService"):
        """
        Inicializa o gerenciador de relatórios.

        Args:
            bot_service ('BotService'): A instância principal do serviço do bot.
        """
        self.bot_service = bot_service
        self.reports_dir: Path = bot_service.reports_dir
        logging.debug("ReportManager inicializado.")

    def get_reports(self) -> list[str]:
        """
        Retorna uma lista ordenada dos nomes dos arquivos de relatório,
        do mais recente para o mais antigo.
        """
        if not self.reports_dir.is_dir():
            logging.warning("Diretório de relatórios não existe.")
            return []

        reports = sorted([f.name for f in self.reports_dir.glob("Relatorio_*.txt")], reverse=True)
        logging.debug(f"{len(reports)} relatórios encontrados.")
        return reports

    def get_report_content(self, filename: str) -> str:
        """
        Lê e retorna o conteúdo de texto de um arquivo de relatório.
        """
        if not filename:
            logging.warning("Nenhum relatório selecionado para leitura.")
            return "Nenhum relatório selecionado."

        report_path = self.reports_dir / filename
        try:
            content = report_path.read_text(encoding="utf-8")
            logging.debug(f"Conteúdo do relatório '{filename}' lido com sucesso.")
            return content
        except FileNotFoundError:
            logging.error(f"Relatório '{filename}' não foi encontrado.")
            return f"Erro: Relatório '{filename}' não foi encontrado."
        except Exception as e:
            logging.error(f"Erro ao ler o relatório '{filename}': {e}")
            return f"Erro ao ler o relatório '{filename}': {e}"

    def delete_report(self, filename: str) -> bool:
        """Exclui um arquivo de relatório de forma segura."""
        if not filename:
            logging.warning("Nenhum nome de relatório fornecido para exclusão.")
            return False

        try:
            report_path = self.reports_dir / filename
            report_path.unlink(missing_ok=True)
            self.bot_service._notify(
                "log", f"Relatório '{filename}' excluído.", THEME_COLORS["log_warning"]
            )
            logging.info(f"Relatório '{filename}' excluído.")
            return True
        except OSError as e:
            log_msg = f"Falha ao excluir o relatório '{filename}'. Motivo: {e}"
            self.bot_service._notify("log", log_msg, THEME_COLORS["log_error"])
            logging.error(log_msg)
            return False

    def export_report_to_csv(self, report_filename: str, csv_path: str) -> bool:
        """
        Exporta os detalhes de um relatório de campanha para um arquivo CSV,
        utilizando Regex para uma extração de dados robusta.
        """
        report_content = self.get_report_content(report_filename)
        if not report_content or "Erro:" in report_content:
            self.bot_service._notify(
                "log",
                f"Não foi possível exportar o relatório: {report_content}",
                THEME_COLORS["log_error"],
            )
            logging.error(f"Não foi possível exportar o relatório: {report_content}")
            return False

        # Regex para extrair os dados de cada linha de detalhe do relatório.
        line_pattern = re.compile(
            r"Destinatário:\s*(?P<destinatario>.*?)\s*"
            r"Status:\s*(?P<status>.*?)\s*"
            r"(?:Detalhes:\s*(?P<detalhes>.*?)\s*)?"
            r"(?:Motivo:\s*(?P<motivo>.*?)\s*)?$"
        )

        header = ["Destinatario", "Status", "Detalhes", "Motivo"]
        rows = []

        for line in report_content.splitlines():
            match = line_pattern.match(line.strip())
            if match:
                row_data = match.groupdict(default="")
                rows.append([
                    row_data.get("destinatario", ""),
                    row_data.get("status", ""),
                    row_data.get("detalhes", ""),
                    row_data.get("motivo", ""),
                ])

        if not rows:
            log_msg = "Nenhum dado de detalhe de envio encontrado no relatório para exportar."
            self.bot_service._notify("log", log_msg, THEME_COLORS["log_warning"])
            logging.warning(log_msg)
            return False

        try:
            # Usa utf-8-sig para garantir compatibilidade com Excel
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                writer = csv.writer(csvfile, delimiter=";")
                writer.writerow(header)
                writer.writerows(rows)

            log_msg = f"Relatório exportado com sucesso para CSV: {Path(csv_path).name}"
            self.bot_service._notify("log", log_msg, THEME_COLORS["log_success"])
            logging.info(log_msg)
            return True
        except OSError as e:
            log_msg = f"Erro de permissão ou de disco ao exportar para CSV: {e}"
            self.bot_service._notify("log", log_msg, THEME_COLORS["log_error"])
            logging.error(log_msg)
            return False
