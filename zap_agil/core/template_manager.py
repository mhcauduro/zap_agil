"""
Gerencia templates de mensagens, incluindo anexos, para o Zap Fácil.
Garante robustez no acesso e limpeza dos arquivos.
"""

import shutil
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from zap_agil.utils.logging_config import logging

if TYPE_CHECKING:
    from zap_agil.core.bot_service import BotService

from zap_agil.utils.json_utils import load_json_file, save_json_file

from .constants import THEME_COLORS


class TemplateManager:
    """Gerencia a lógica de templates e anexos."""

    def __init__(self, bot_service: "BotService"):
        self.bot_service = bot_service
        self.templates_dir: Path = bot_service.templates_attachments_dir
        self.templates_json: Path = (
            bot_service.app_data_dir / "templates.json"
        )  # Arquivo com os dados dos templates

        self.templates_dir.mkdir(exist_ok=True)
        logging.debug("TemplateManager inicializado.")

    def get_templates(self) -> list[dict[str, Any]]:
        """Retorna a lista de templates salvos."""
        result = load_json_file(self.templates_json, default=[])
        if isinstance(result, list):
            logging.debug(f"{len(result)} templates carregados.")
            return result
        logging.warning("Arquivo de templates corrompido ou inválido.")
        return []

    def save_template(self, data: dict[str, Any]) -> str | None:
        """
        Salva um novo template ou atualiza existente.
        Se houver anexo, faz cópia física para pasta dedicada.
        """
        templates = self.get_templates()
        tpl_id = data.get("id") or str(uuid.uuid4())
        data["id"] = tpl_id

        # CORREÇÃO: Usa a chave "attachment" que vem da UI
        attachment_path = data.get("attachment")

        # Se houver anexo novo, faz a cópia e atualiza o caminho.
        if attachment_path and attachment_path != data.get("stored_attachment"):
            src = Path(attachment_path)
            if src.is_file():
                dest = self.templates_dir / f"{tpl_id}{src.suffix.lower()}"
                try:
                    shutil.copyfile(src, dest)
                    data["stored_attachment"] = str(dest)
                    self.bot_service._notify(
                        "log",
                        f"Anexo copiado para template: {dest.name}",
                        THEME_COLORS["log_success"],
                    )
                    logging.info(f"Anexo copiado para template: {dest.name}")
                except Exception as e:
                    self.bot_service._notify(
                        "log",
                        f"Falha ao copiar anexo: {e}",
                        THEME_COLORS["log_error"],
                    )
                    logging.error(f"Falha ao copiar anexo: {e}")
            else:
                self.bot_service._notify(
                    "log",
                    f"Arquivo de anexo não encontrado: {src}",
                    THEME_COLORS["log_warning"],
                )
                logging.warning(f"Arquivo de anexo não encontrado: {src}")

        # Atualiza ou insere template
        idx = next((i for i, tpl in enumerate(templates) if tpl.get("id") == tpl_id), None)
        if idx is not None:
            templates[idx] = data
        else:
            templates.append(data)

        if save_json_file(self.templates_json, templates):
            self.bot_service._notify(
                "log",
                f"Template salvo com sucesso (ID: {tpl_id})",
                THEME_COLORS["log_success"],
            )
            logging.info(f"Template salvo com sucesso (ID: {tpl_id})")
            return tpl_id

        self.bot_service._notify(
            "log",
            f"Falha ao salvar template (ID: {tpl_id})",
            THEME_COLORS["log_error"],
        )
        logging.error(f"Falha ao salvar template (ID: {tpl_id})")
        return None

    def delete_template(self, tpl_id: str) -> bool:
        """Remove o template e o anexo associado (se existir)."""
        templates = self.get_templates()
        tpl = next((tpl for tpl in templates if tpl.get("id") == tpl_id), None)
        if not tpl:
            self.bot_service._notify(
                "log",
                f"Template com ID '{tpl_id}' não encontrado.",
                THEME_COLORS["log_warning"],
            )
            logging.warning(f"Template com ID '{tpl_id}' não encontrado para exclusão.")
            return False

        # Deleta anexo físico se existir
        if tpl.get("stored_attachment"):
            try:
                attachment_path = Path(tpl["stored_attachment"])
                if attachment_path.exists() and self.templates_dir in attachment_path.parents:
                    attachment_path.unlink()
                    self.bot_service._notify(
                        "log",
                        f"Anexo do template excluído: {attachment_path.name}",
                        THEME_COLORS["log_warning"],
                    )
                    logging.info(f"Anexo do template excluído: {attachment_path.name}")
            except Exception as e:
                self.bot_service._notify(
                    "log",
                    f"Falha ao excluir anexo: {e}",
                    THEME_COLORS["log_error"],
                )
                logging.error(f"Falha ao excluir anexo: {e}")

        new_templates = [t for t in templates if t.get("id") != tpl_id]
        if save_json_file(self.templates_json, new_templates):
            self.bot_service._notify(
                "log",
                f"Template excluído (ID: {tpl_id})",
                THEME_COLORS["log_warning"],
            )
            logging.info(f"Template excluído (ID: {tpl_id})")
            return True

        self.bot_service._notify(
            "log",
            f"Falha ao excluir template (ID: {tpl_id})",
            THEME_COLORS["log_error"],
        )
        logging.error(f"Falha ao excluir template (ID: {tpl_id})")
        return False

    def cleanup_orphaned_attachments(self) -> None:
        """Remove arquivos de anexo não referenciados por nenhum template."""
        templates = self.get_templates()
        referenced = {
            Path(tpl["stored_attachment"]).name for tpl in templates if tpl.get("stored_attachment")
        }
        for file in self.templates_dir.iterdir():
            if file.is_file() and file.name not in referenced:
                try:
                    file.unlink()
                    self.bot_service._notify(
                        "log",
                        f"Anexo órfão removido: {file.name}",
                        THEME_COLORS["log_warning"],
                    )
                    logging.info(f"Anexo órfão removido: {file.name}")
                except Exception as e:
                    self.bot_service._notify(
                        "log",
                        f"Erro ao remover anexo órfão: {e}",
                        THEME_COLORS["log_error"],
                    )
                    logging.error(f"Erro ao remover anexo órfão: {e}")
