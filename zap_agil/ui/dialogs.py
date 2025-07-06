"""
Define diálogos modernos, responsivos e intuitivos para o gerenciamento de
modelos, relatórios e agendamentos do Zap Fácil.
"""

import calendar
import copy
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import wx
import wx.adv

from zap_agil.core.bot_service import BotService
from zap_agil.core.constants import (
    APP_NAME,
    THEME_COLORS,
    WILDCARD_ALL_ATTACHMENTS,
    WILDCARD_CONTACTS,
    SourceType,
)
from zap_agil.ui.panels import ContentPanel
from zap_agil.ui.ui_utils import show_file_dialog
from zap_agil.utils.logging_config import logging


def _get_resource_txt(filename: str) -> str:
    """
    Lê um arquivo de texto da raiz do app (compatível com PyInstaller).
    Se não existir, retorna string vazia.
    """
    try:
        if hasattr(sys, "_MEIPASS"):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent.parent  # zap_agil/
        path = base / filename
        if path.exists():
            content = path.read_text(encoding="utf-8")
            if content.strip():
                return content
    except Exception:
        # Ignora erro de leitura de arquivo de recurso
        return ""
    # Mensagem padrão se não encontrar o arquivo
    if "dica" in filename.lower():
        return "Arquivo de dicas não encontrado. Verifique a instalação."
    if "novidade" in filename.lower():
        return "Arquivo de novidades não encontrado. Verifique a instalação."
    return "Arquivo de texto não encontrado."


class LargeTextDialog(wx.Dialog):
    """
    Diálogo responsivo para exibir textos grandes (novidades, dicas etc).
    Possui rolagem suave, seleção de texto, botão fechar, atalhos e adapta a qualquer tela.
    """

    def __init__(self, parent, title: str, filename: str):
        logging.debug(f"Abrindo LargeTextDialog: {title} ({filename})")
        super().__init__(
            parent,
            title=title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MINIMIZE_BOX,
            size=(700, 500),
        )
        logging.debug(f"Abrindo LargeTextDialog: {title} ({filename})")
        self.SetBackgroundColour(wx.Colour(THEME_COLORS["panel"]))
        self.SetForegroundColour(wx.Colour(THEME_COLORS["text"]))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Caixa de texto grande, read-only, fonte aumentada e rolagem
        self.txt_ctrl = wx.TextCtrl(
            self,
            value=_get_resource_txt(filename),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.HSCROLL | wx.VSCROLL,
        )
        font = self.txt_ctrl.GetFont()
        font.SetPointSize(max(font.GetPointSize(), 11))
        self.txt_ctrl.SetFont(font)
        self.txt_ctrl.SetBackgroundColour(wx.Colour(THEME_COLORS["background"]))
        self.txt_ctrl.SetForegroundColour(wx.Colour(THEME_COLORS["text"]))
        self.txt_ctrl.SetToolTip(
            "Campo somente leitura. Use Ctrl+F para buscar no texto. "
            "Selecione e copie livremente. A navegação é acessível por teclado."
        )
        main_sizer.Add(self.txt_ctrl, 1, wx.EXPAND | wx.ALL, 12)

        # Botões: Copiar Tudo e Fechar
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        copy_btn = wx.Button(self, id=wx.ID_ANY, label="Copiar Tudo")
        copy_btn.SetToolTip(
            "Copiar todo o texto exibido para a área de transferência. "
            "Atenção: o conteúdo pode ser extenso."
        )
        close_btn = wx.Button(self, id=wx.ID_CLOSE, label="Fechar")
        close_btn.SetToolTip(
            "Fechar esta janela de diálogo. Atalho: Esc. A navegação é acessível por teclado."
        )
        close_btn.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_QUIT, wx.ART_BUTTON))
        btn_sizer.Add(copy_btn, 0, wx.ALL, 5)
        btn_sizer.AddStretchSpacer()
        btn_sizer.Add(close_btn, 0, wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        self.SetSizer(main_sizer)
        self.CentreOnParent()
        self.txt_ctrl.SetFocus()
        self.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CLOSE), id=wx.ID_CLOSE)
        self.Bind(wx.EVT_BUTTON, self._on_copy_all, copy_btn)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_down)

    def _on_copy_all(self, event):
        if self.txt_ctrl.GetValue() and wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.txt_ctrl.GetValue()))
            wx.TheClipboard.Close()
            wx.Bell()
            wx.MessageBox(
                "Texto copiado para a área de transferência!",
                "Copiado",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )

    def _on_key_down(self, event: wx.KeyEvent):
        # Ctrl+F: buscar texto
        if event.ControlDown() and event.GetKeyCode() == ord("F"):
            self._show_find_dialog()
            return
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _show_find_dialog(self):
        # Diálogo simples de busca textual
        dlg = wx.TextEntryDialog(self, "Buscar por:", "Procurar no texto")
        if dlg.ShowModal() == wx.ID_OK:
            keyword = dlg.GetValue().strip()
            if keyword:
                value = self.txt_ctrl.GetValue()
                idx = value.lower().find(keyword.lower())
                if idx >= 0:
                    self.txt_ctrl.SetFocus()
                    self.txt_ctrl.SetSelection(idx, idx + len(keyword))
                else:
                    wx.MessageBox(
                        f"'{keyword}' não encontrado no texto.",
                        "Busca",
                        wx.OK | wx.ICON_INFORMATION,
                    )
        dlg.Destroy()


class NewsDialog(LargeTextDialog):
    def __init__(self, parent):
        super().__init__(parent, "Novidades do Programa", "novidades.txt")


class TipsDialog(LargeTextDialog):
    def __init__(self, parent):
        super().__init__(parent, "Tutorial & Dicas de Uso", "dicas.txt")


# --- DIÁLOGO DE GERENCIAMENTO DE MODELOS ---
class TemplatesDialog(wx.Dialog):
    """Diálogo para criar, editar e excluir modelos de campanhas."""

    def __init__(self, parent: wx.Window, bot_service: BotService):
        logging.debug("Abrindo TemplatesDialog.")
        super().__init__(
            parent,
            title=f"Gerenciar Modelos - {APP_NAME}",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MINIMIZE_BOX,
        )
        logging.debug("Abrindo TemplatesDialog.")
        self.bot = bot_service
        self.current_template_id: str | None = None
        self.templates_data: list[dict[str, Any]] = []

        self.SetBackgroundColour(wx.Colour(THEME_COLORS["panel"]))
        self.SetForegroundColour(wx.Colour(THEME_COLORS["text"]))
        self.SetMinSize((850, 600))

        self._init_ui()
        self._bind_events()
        self._load_templates()
        self.CentreOnParent()

    def _init_ui(self) -> None:
        """Inicializa a interface com layout responsivo."""
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # --- Painel Esquerdo (Lista de Modelos) ---
        left_panel = self._create_list_panel()

        # --- Painel Direito (Formulário de Edição) ---
        right_panel = self._create_form_panel()

        main_sizer.Add(left_panel, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(right_panel, 3, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(main_sizer)

    def _create_list_panel(self) -> wx.Panel:
        """Cria o painel com a lista de modelos e botões de ação."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(panel, label="Modelos Salvos:")
        label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        sizer.Add(label, 0, wx.ALL | wx.EXPAND, 5)

        self.template_list_box = wx.ListBox(panel, style=wx.LB_SINGLE)
        self.template_list_box.SetToolTip(
            "Lista de modelos salvos. Selecione um modelo para editar, visualizar detalhes ou "
            "carregar. Use as setas do teclado para navegar."
        )
        sizer.Add(self.template_list_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.new_btn = wx.Button(panel, label="&Novo")
        self.new_btn.SetToolTip(
            "Criar um novo modelo de campanha. Atalho: Ctrl+N. Botão acessível por teclado."
        )
        self.delete_btn = wx.Button(panel, label="&Excluir")
        self.delete_btn.SetToolTip(
            "Excluir o modelo selecionado da lista. Atalho: Ctrl+D. Confirmação será solicitada."
        )

        btn_sizer.Add(self.new_btn, 1, wx.EXPAND | wx.RIGHT, 5)
        btn_sizer.Add(self.delete_btn, 1, wx.EXPAND)
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_form_panel(self) -> wx.Panel:
        """Cria o painel de formulário com layout de grade para alinhamento."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        form_box = wx.StaticBox(panel, label="Detalhes do Modelo")
        form_sizer = wx.StaticBoxSizer(form_box, wx.VERTICAL)

        gbs = wx.GridBagSizer(5, 10)

        # Nome do Modelo
        gbs.Add(
            wx.StaticText(panel, label="Nome do Modelo:"),
            pos=(0, 0),
            flag=wx.ALIGN_CENTER_VERTICAL,
        )
        self.template_name = wx.TextCtrl(panel)
        self.template_name.SetToolTip(
            "Campo obrigatório. Digite um nome único e descritivo para o modelo de campanha. "
            "Exemplo: Promoção de Verão."
        )
        self.template_name.SetHint("Ex.: Promoção de Verão")
        gbs.Add(self.template_name, pos=(0, 1), flag=wx.EXPAND)

        # Mensagem
        gbs.Add(
            wx.StaticText(panel, label="Texto da Mensagem:"),
            pos=(1, 0),
            flag=wx.ALIGN_TOP,
        )
        self.template_msg = wx.TextCtrl(
            panel, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER, size=(-1, 150)
        )
        self.template_msg.SetToolTip(
            "Digite o texto da mensagem que será enviada. "
            "Use @Coluna para personalizar com dados do seu arquivo. "
            "Campo multilinha, acessível por teclado."
        )
        gbs.Add(self.template_msg, pos=(1, 1), flag=wx.EXPAND)

        # Anexo
        gbs.Add(
            wx.StaticText(panel, label="Anexo (Opcional):"),
            pos=(2, 0),
            flag=wx.ALIGN_CENTER_VERTICAL,
        )
        attach_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.template_attachment_path = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.template_attachment_path.SetToolTip(
            "Campo somente leitura. Exibe o caminho do arquivo de mídia ou documento anexado ao "
            "modelo. Clique em 'Selecionar anexo' para escolher um arquivo."
        )
        self.browse_attachment_btn = wx.Button(panel, id=wx.ID_FIND, label="Selecionaranexo...")
        self.browse_attachment_btn.SetToolTip(
            "Procurar e anexar um arquivo ao modelo. Atalho: Ctrl+B. Botão acessível por teclado."
        )
        self.clear_attachment_btn = wx.Button(panel, id=wx.ID_CLEAR, label="Remover")
        self.clear_attachment_btn.SetToolTip(
            "Remover o anexo do modelo. O campo ficará vazio. Atalho: Ctrl+R."
        )
        attach_sizer.Add(self.template_attachment_path, 1, wx.EXPAND | wx.RIGHT, 5)
        attach_sizer.Add(self.browse_attachment_btn, 0, wx.RIGHT, 5)
        attach_sizer.Add(self.clear_attachment_btn, 0)
        gbs.Add(attach_sizer, pos=(2, 1), flag=wx.EXPAND)

        gbs.AddGrowableCol(1)
        gbs.AddGrowableRow(1)
        form_sizer.Add(gbs, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(form_sizer, 1, wx.EXPAND)

        # Botões de Ação
        btn_sizer = wx.StdDialogButtonSizer()
        self.save_btn = wx.Button(panel, wx.ID_SAVE, label="&Salvar Modelo")
        self.save_btn.SetToolTip(
            "Salvar as alterações realizadas no modelo. Atalho: Ctrl+S. "
            "Botão acessível por teclado."
        )
        close_btn = wx.Button(panel, wx.ID_CANCEL, label="&Fechar")
        close_btn.SetToolTip(
            "Fechar esta janela de diálogo. Atalho: Esc. A navegação é acessível por teclado."
        )
        btn_sizer.AddButton(self.save_btn)
        btn_sizer.AddButton(close_btn)
        btn_sizer.Realize()

        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        panel.SetSizer(sizer)
        return panel

    def _bind_events(self) -> None:
        """Associa eventos aos componentes da interface."""
        self.new_btn.Bind(wx.EVT_BUTTON, self._on_new)
        self.delete_btn.Bind(wx.EVT_BUTTON, self._on_delete)
        self.Bind(wx.EVT_BUTTON, self._on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CANCEL), id=wx.ID_CANCEL)
        self.template_list_box.Bind(wx.EVT_LISTBOX, self._on_select_template)
        self.browse_attachment_btn.Bind(wx.EVT_BUTTON, self._on_browse_attachment)
        self.clear_attachment_btn.Bind(wx.EVT_BUTTON, self._on_clear_attachment)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_down)

    def _on_key_down(self, event: wx.KeyEvent) -> None:
        """Gerencia atalhos de teclado."""
        keycode = event.GetKeyCode()
        if event.ControlDown():
            if keycode == ord("N"):
                self._on_new(event)
                return
            elif keycode == ord("D"):
                self._on_delete(event)
                return
            elif keycode == ord("S"):
                self._on_save(event)
                return
            elif keycode == ord("B"):
                self._on_browse_attachment(event)
                return
            elif keycode == ord("R"):
                self._on_clear_attachment(event)
                return
        if keycode == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _update_ui_state(self) -> None:
        """Atualiza o estado dos botões de ação com base na seleção e nos dados."""
        has_selection = self.template_list_box.GetSelection() != wx.NOT_FOUND
        self.delete_btn.Enable(has_selection)

        has_attachment = bool(self.template_attachment_path.GetValue())
        self.clear_attachment_btn.Enable(has_attachment)

        is_new = self.current_template_id is None
        self.save_btn.SetLabel("&Salvar Novo" if is_new else "&Atualizar Modelo")

    def _load_templates(self) -> None:
        """Carrega os modelos salvos e atualiza a lista."""
        try:
            self.templates_data = self.bot.get_templates()
            self.template_list_box.Clear()
            for tpl in self.templates_data:
                name = tpl.get("name", "Modelo sem nome")
                attachment_str = " | 📎 Anexo" if tpl.get("attachment") else ""
                self.template_list_box.Append(f"{name}{attachment_str}")
            self._clear_form()
            logging.debug(f"{len(self.templates_data)} modelos carregados no TemplatesDialog.")
        except Exception as exc:
            logging.error(f"Erro ao carregar modelos no TemplatesDialog: {exc}")

    def _clear_form(self) -> None:
        """Limpa o formulário, preparando para um novo modelo ou deseleção."""
        self.current_template_id = None
        self.template_name.Clear()
        self.template_msg.Clear()
        self.template_attachment_path.Clear()
        self.template_list_box.SetSelection(wx.NOT_FOUND)
        self.template_name.SetFocus()
        self._update_ui_state()

    def _populate_form(self, template_data: dict[str, Any]) -> None:
        """Preenche o formulário com os dados de um modelo."""
        self.current_template_id = template_data.get("id")
        self.template_name.SetValue(template_data.get("name", ""))
        self.template_msg.SetValue(template_data.get("message", ""))

        attachment = template_data.get("attachment", "")
        if attachment and Path(attachment).exists():
            self.template_attachment_path.SetValue(attachment)
        elif attachment:
            self.template_attachment_path.SetValue(
                f"Arquivo não encontrado: {Path(attachment).name}"
            )
        else:
            self.template_attachment_path.Clear()

        self._update_ui_state()

    def _on_select_template(self, event: wx.CommandEvent) -> None:
        sel_index = event.GetSelection()
        if sel_index != wx.NOT_FOUND:
            self._populate_form(self.templates_data[sel_index])

    def _on_new(self, event: wx.CommandEvent) -> None:
        self._clear_form()

    def _on_delete(self, event: wx.CommandEvent) -> None:
        sel_index = self.template_list_box.GetSelection()
        if sel_index == wx.NOT_FOUND:
            return

        template = self.templates_data[sel_index]
        if (
            wx.MessageBox(
                f"Tem certeza que deseja excluir permanentemente o modelo '{template['name']}'?",
                "Confirmar Exclusão",
                wx.YES_NO | wx.ICON_WARNING,
                self,
            )
            == wx.ID_YES
        ):
            try:
                # Bloco try/except para capturar erros na exclusão
                if self.bot.delete_template(template["id"]):
                    self._load_templates()
                    logging.info(f"Modelo '{template['name']}' excluído.")
                else:
                    wx.MessageBox(
                        "Falha ao excluir o modelo.",
                        "Erro",
                        wx.OK | wx.ICON_ERROR,
                        self,
                    )
                    logging.warning(f"Falha ao excluir o modelo '{template['name']}'.")
            except Exception as e:
                wx.MessageBox(
                    f"Ocorreu um erro inesperado ao excluir o modelo:\n\n{e}",
                    "Erro Crítico",
                    wx.OK | wx.ICON_ERROR,
                    self,
                )
                logging.error(f"Erro inesperado ao excluir modelo: {e}")

    def _on_save(self, event: wx.CommandEvent) -> None:
        template_name = self.template_name.GetValue().strip()
        if not template_name:
            wx.MessageBox(
                "O nome do modelo é obrigatório.",
                "Erro de Validação",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        attachment_path = self.template_attachment_path.GetValue()
        if "Arquivo não encontrado" in attachment_path:
            attachment_path = ""  # Nao salvar caminho invalido

        template_data = {
            "id": self.current_template_id,
            "name": template_name,
            "message": self.template_msg.GetValue(),
            "attachment": attachment_path,
        }

        try:
            # Bloco try/except para capturar erros no salvamento
            saved_id = self.bot.save_template(template_data)
            if saved_id:
                self._load_templates()
                new_selection = next(
                    (i for i, tpl in enumerate(self.templates_data) if tpl.get("id") == saved_id),
                    -1,
                )
                if new_selection != -1:
                    self.template_list_box.SetSelection(new_selection)
                    self._populate_form(self.templates_data[new_selection])
                logging.info(f"Modelo '{template_name}' salvo/atualizado.")
            else:
                wx.MessageBox(
                    "O modelo não pôde ser salvo por um motivo desconhecido.",
                    "Falha ao Salvar",
                    wx.OK | wx.ICON_ERROR,
                    self,
                )
                logging.warning(f"Falha ao salvar modelo '{template_name}'.")
        except Exception as e:
            wx.MessageBox(
                f"Ocorreu um erro inesperado ao salvar o modelo:\n\n{e}",
                "Erro Crítico",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            logging.error(f"Erro inesperado ao salvar modelo: {e}")

    def _on_browse_attachment(self, event: wx.CommandEvent) -> None:
        path = show_file_dialog(self, "Selecionar Anexo para o Modelo", WILDCARD_ALL_ATTACHMENTS)
        if path:
            self.template_attachment_path.SetValue(path)
        self._update_ui_state()

    def _on_clear_attachment(self, event: wx.CommandEvent) -> None:
        self.template_attachment_path.Clear()
        self._update_ui_state()


# --- DIÁLOGO DE SELEÇÃO DE MODELO ---
class TemplatePickerDialog(wx.Dialog):
    """Diálogo simplificado para selecionar um modelo existente."""

    def __init__(self, parent: wx.Window, templates: list[dict[str, Any]]):
        super().__init__(
            parent,
            title=f"Selecionar Modelo - {APP_NAME}",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.templates = templates
        self.selected_template: dict[str, Any] | None = None
        self.SetMinSize((600, 400))
        self.SetBackgroundColour(wx.Colour(THEME_COLORS["panel"]))
        self.SetForegroundColour(wx.Colour(THEME_COLORS["text"]))

        self._init_ui()
        self._bind_events()
        self.CentreOnParent()

    def _init_ui(self) -> None:
        """Inicializa a interface do seletor."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(panel, label="Selecione um modelo para carregar:")
        label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        sizer.Add(label, 0, wx.ALL | wx.EXPAND, 10)

        choices = [f"{tpl['name']}" for tpl in self.templates]
        self.list_box = wx.ListBox(panel, choices=choices)
        self.list_box.SetToolTip(
            "Lista de modelos disponíveis. Selecione um modelo e clique em 'Carregar', "
            "ou dê um clique duplo. Use as setas do teclado para navegar."
        )
        sizer.Add(self.list_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        btn_sizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(panel, wx.ID_OK, label="&Carregar")
        ok_btn.SetToolTip(
            "Carregar o modelo selecionado. Atalho: Enter. Botão acessível por teclado."
        )
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, label="&Cancelar")
        cancel_btn.SetToolTip("Fechar o diálogo sem selecionar um modelo. Atalho: Esc.")
        btn_sizer.AddButton(ok_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        panel.SetSizer(sizer)
        main_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizerAndFit(main_sizer)

    def _bind_events(self) -> None:
        """Associa eventos aos componentes."""
        self.list_box.Bind(wx.EVT_LISTBOX_DCLICK, self._on_ok)
        self.Bind(wx.EVT_BUTTON, self._on_ok, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CANCEL), id=wx.ID_CANCEL)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_down)

    def _on_key_down(self, event: wx.KeyEvent) -> None:
        """Gerencia atalhos."""
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN and self.list_box.GetSelection() != wx.NOT_FOUND:
            self._on_ok(event)
            return
        if keycode == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _on_ok(self, event: wx.CommandEvent) -> None:
        """Confirma a seleção e fecha."""
        selection = self.list_box.GetSelection()
        if selection != wx.NOT_FOUND:
            self.selected_template = self.templates[selection]
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox(
                "Por favor, selecione um modelo da lista.",
                "Aviso",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )

    def get_selected_template(self) -> dict[str, Any] | None:
        return self.selected_template


# --- DIÁLOGO DE RELATÓRIOS ---


class ReportsDialog(wx.Dialog):
    """Diálogo para exibir, exportar e gerenciar relatórios de campanhas."""

    def __init__(self, parent: wx.Window, bot_service: BotService):
        logging.debug("Abrindo ReportsDialog.")
        super().__init__(
            parent,
            title=f"Relatórios de Campanha - {APP_NAME}",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MINIMIZE_BOX,
        )
        logging.debug("Abrindo ReportsDialog.")
        self.bot = bot_service
        self.SetMinSize((750, 500))
        self.SetBackgroundColour(wx.Colour(THEME_COLORS["panel"]))
        self.SetForegroundColour(wx.Colour(THEME_COLORS["text"]))

        self._init_ui()
        self._bind_events()
        self._refresh_report_list()
        self.CentreOnParent()

    def _init_ui(self) -> None:
        """Inicializa a interface de relatórios."""
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Painel Esquerdo (Lista de Relatórios)
        left_panel = wx.Panel(self)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_label = wx.StaticText(left_panel, label="Relatórios Disponíveis:")
        left_label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        left_sizer.Add(left_label, 0, wx.ALL | wx.EXPAND, 10)
        self.report_list = wx.ListBox(left_panel)
        self.report_list.SetToolTip(
            "Lista de relatórios disponíveis. Selecione um relatório para visualizar seu conteúdo. "
            "Use as setas do teclado para navegar."
        )
        left_sizer.Add(self.report_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        left_panel.SetSizer(left_sizer)

        # Painel Direito (Detalhes e Ações)
        right_panel = wx.Panel(self)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        right_label = wx.StaticText(right_panel, label="Detalhes do Relatório Selecionado:")
        right_label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        right_sizer.Add(right_label, 0, wx.ALL | wx.EXPAND, 10)
        self.report_content = wx.TextCtrl(
            right_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
        )
        self.report_content.SetToolTip(
            "Campo somente leitura. Exibe o conteúdo detalhado do relatório selecionado. "
            "A navegação é acessível por teclado."
        )
        self.report_content.SetBackgroundColour(wx.Colour(THEME_COLORS["background"]))
        right_sizer.Add(self.report_content, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.export_btn = wx.Button(right_panel, label="&Exportar para CSV")
        self.export_btn.SetToolTip(
            "Exportar o relatório selecionado para um arquivo CSV. Atalho: Ctrl+E."
        )
        self.delete_btn = wx.Button(right_panel, label="&Excluir Relatório")
        self.delete_btn.SetToolTip(
            "Excluir o relatório selecionado permanentemente. Atalho: Ctrl+D. "
            "Confirmação será solicitada."
        )
        close_btn = wx.Button(right_panel, id=wx.ID_CANCEL, label="&Fechar")
        close_btn.SetToolTip(
            "Fechar esta janela de diálogo. Atalho: Esc. A navegação é acessível por teclado."
        )

        button_sizer.Add(self.export_btn, 0, wx.RIGHT, 10)
        button_sizer.Add(self.delete_btn, 0)
        button_sizer.AddStretchSpacer()
        button_sizer.Add(close_btn, 0)
        right_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)
        right_panel.SetSizer(right_sizer)

        main_sizer.Add(left_panel, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(right_panel, 2, wx.EXPAND | wx.ALL, 10)
        self.SetSizerAndFit(main_sizer)

    def _bind_events(self) -> None:
        """Associa eventos."""
        self.report_list.Bind(wx.EVT_LISTBOX, self._on_report_selected)
        self.delete_btn.Bind(wx.EVT_BUTTON, self._on_delete_report)
        self.export_btn.Bind(wx.EVT_BUTTON, self._on_export_report)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CANCEL), id=wx.ID_CANCEL)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_down)

    def _on_key_down(self, event: wx.KeyEvent) -> None:
        """Gerencia atalhos."""
        keycode = event.GetKeyCode()
        if event.ControlDown():
            if keycode == ord("E"):
                self._on_export_report(event)
                return
            elif keycode == ord("D"):
                self._on_delete_report(event)
                return
        if keycode == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _refresh_report_list(self) -> None:
        """Atualiza a lista de relatórios e reseta a UI."""
        try:
            self.report_list.Clear()
            reports = self.bot.get_reports()
            if reports:
                self.report_list.InsertItems(reports, 0)
            self.report_content.Clear()
            self.delete_btn.Disable()
            self.export_btn.Disable()
            logging.debug(f"{len(reports)} relatórios carregados no ReportsDialog.")
        except Exception as exc:
            logging.error(f"Erro ao carregar relatórios no ReportsDialog: {exc}")

    def _on_report_selected(self, event: wx.CommandEvent) -> None:
        """Exibe o conteúdo do relatório ao selecioná-lo."""
        selected_report = event.GetString()
        if selected_report:
            self.report_content.SetValue(self.bot.get_report_content(selected_report))
            self.delete_btn.Enable()
            self.export_btn.Enable()

    def _on_delete_report(self, event: wx.CommandEvent) -> None:
        """Exclui o relatório selecionado."""
        selected_report = self.report_list.GetStringSelection()
        if not selected_report:
            return

        if (
            wx.MessageBox(
                f"Tem certeza que deseja excluir o relatório '{selected_report}'?\n"
                "Esta ação não pode ser desfeita.",
                "Confirmar Exclusão",
                wx.YES_NO | wx.ICON_WARNING,
                self,
            )
            == wx.ID_YES
        ):
            try:
                # Bloco try/except para capturar erros na exclusão
                if self.bot.delete_report(selected_report):
                    self._refresh_report_list()
                    logging.info(f"Relatório '{selected_report}' excluído.")
                else:
                    wx.MessageBox(
                        "Falha ao excluir o relatório.",
                        "Erro",
                        wx.OK | wx.ICON_ERROR,
                        self,
                    )
                    logging.warning(f"Falha ao excluir relatório '{selected_report}'.")
            except Exception as e:
                wx.MessageBox(
                    f"Ocorreu um erro inesperado ao excluir o relatório:\n\n{e}",
                    "Erro Crítico",
                    wx.OK | wx.ICON_ERROR,
                    self,
                )
                logging.error(f"Erro inesperado ao excluir relatório: {e}")

    def _on_export_report(self, event: wx.CommandEvent) -> None:
        """Exporta o relatório atual para um arquivo CSV."""
        report_filename = self.report_list.GetStringSelection()
        if not report_filename:
            return

        default_filename = f"{Path(report_filename).stem}.csv"
        with wx.FileDialog(
            self,
            "Salvar Relatório como CSV",
            wildcard="Arquivos CSV (*.csv)|*.csv",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            defaultFile=default_filename,
        ) as fd:
            if fd.ShowModal() == wx.ID_OK:
                csv_path = fd.GetPath()
                try:
                    # Bloco try/except para capturar erros na exportação
                    if self.bot.export_report_to_csv(report_filename, csv_path):
                        wx.MessageBox(
                            f"Relatório exportado com sucesso para:\n{csv_path}",
                            "Exportação Concluída",
                            wx.OK | wx.ICON_INFORMATION,
                        )
                        logging.info(f"Relatório '{report_filename}' exportado para {csv_path}.")
                    else:
                        wx.MessageBox(
                            "Falha ao exportar o relatório.",
                            "Erro",
                            wx.OK | wx.ICON_ERROR,
                            self,
                        )
                        logging.warning(f"Falha ao exportar relatório '{report_filename}'.")
                except Exception as e:
                    wx.MessageBox(
                        f"Ocorreu um erro inesperado ao exportar o relatório:\n\n{e}",
                        "Erro Crítico",
                        wx.OK | wx.ICON_ERROR,
                        self,
                    )
                    logging.error(f"Erro inesperado ao exportar relatório: {e}")


# --- DIÁLOGO DE AGENDAMENTO DE CAMPANHAS ---
class CampaignSchedulerDialog(wx.Dialog):
    """Diálogo completo para agendar, configurar e gerenciar campanhas."""

    def __init__(self, parent: wx.Window, bot_service: BotService):
        super().__init__(
            parent,
            title=f"Gerenciar Campanhas Agendadas - {APP_NAME}",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MINIMIZE_BOX,
        )
        self.bot = bot_service
        self.current_schedule_id: str | None = None
        self.schedules_data: list[dict[str, Any]] = []

        self.SetMinSize((900, 700))
        self.SetBackgroundColour(wx.Colour(THEME_COLORS["panel"]))
        self.SetForegroundColour(wx.Colour(THEME_COLORS["text"]))

        self._init_ui()
        self._bind_events()
        self._load_schedules()
        self.CentreOnParent()

    def _init_ui(self):
        """Inicializa a complexa UI do agendador."""
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Painel Esquerdo (Lista de Agendamentos)
        left_panel = self._create_schedule_list_panel()

        # Painel Direito (Notebook com Abas de Configuração)
        right_panel = self._create_schedule_form_panel()

        main_sizer.Add(left_panel, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(right_panel, 2, wx.EXPAND | wx.ALL, 10)
        self.SetSizerAndFit(main_sizer)

    def _create_schedule_list_panel(self) -> wx.Panel:
        """Cria o painel esquerdo com a lista de agendamentos."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(panel, label="Campanhas Agendadas:")
        label.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        sizer.Add(label, 0, wx.ALL | wx.EXPAND, 5)

        self.schedule_list_box = wx.ListBox(panel)
        self.schedule_list_box.SetToolTip("Selecione uma campanha para editar ou visualizar.")
        sizer.Add(self.schedule_list_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        btn_sizer = wx.GridSizer(1, 3, 5, 5)
        self.new_btn = wx.Button(panel, label="&Nova")
        self.new_btn.SetToolTip("Criar uma nova campanha agendada (Ctrl+N)")
        self.copy_btn = wx.Button(panel, label="&Duplicar")
        self.copy_btn.SetToolTip("Criar uma cópia da campanha selecionada (Ctrl+P)")
        self.delete_btn = wx.Button(panel, label="&Excluir")
        self.delete_btn.SetToolTip("Excluir a campanha selecionada (Ctrl+D)")

        btn_sizer.Add(self.new_btn, 1, wx.EXPAND)
        btn_sizer.Add(self.copy_btn, 1, wx.EXPAND)
        btn_sizer.Add(self.delete_btn, 1, wx.EXPAND)
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_schedule_form_panel(self) -> wx.Panel:
        """Cria o painel direito com o notebook de configuração."""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(panel)
        self.notebook.SetBackgroundColour(wx.Colour(THEME_COLORS["panel"]))

        self.general_panel = self._create_general_panel(self.notebook)
        # Reutiliza o ContentPanel refatorado!
        self.content_panel = ContentPanel(self.notebook, self.bot)
        self.recipients_panel = self._create_recipients_panel(self.notebook)

        self.notebook.AddPage(self.general_panel, "1. Geral e Gatilho")
        self.notebook.AddPage(self.content_panel, "2. Conteúdo (Mensagem/Anexo)")
        self.notebook.AddPage(self.recipients_panel, "3. Destinatários (Contatos/Grupos)")

        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

        btn_sizer = wx.StdDialogButtonSizer()
        self.save_btn = wx.Button(panel, wx.ID_SAVE, label="Salvar Campanha")
        self.save_btn.SetToolTip("Salvar ou atualizar a campanha agendada (Ctrl+S)")
        close_btn = wx.Button(panel, wx.ID_CANCEL, label="Fechar")
        close_btn.SetToolTip("Fechar o diálogo (Esc)")
        btn_sizer.AddButton(self.save_btn)
        btn_sizer.AddButton(close_btn)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def _create_general_panel(self, parent: wx.Window) -> wx.Panel:
        """Cria a aba 'Geral e Gatilho'."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Identificação
        name_box = wx.StaticBox(panel, label="Identificação da Campanha")
        name_sizer = wx.StaticBoxSizer(name_box, wx.VERTICAL)
        gbs_name = wx.GridBagSizer(5, 10)
        gbs_name.Add(
            wx.StaticText(panel, label="Nome da Campanha:"),
            pos=(0, 0),
            flag=wx.ALIGN_CENTER_VERTICAL,
        )
        self.schedule_name = wx.TextCtrl(panel)
        self.schedule_name.SetToolTip("Digite um nome único para esta campanha agendada.")
        self.schedule_name.SetHint("Ex.: Lembretes de Vencimento - Mensal")
        gbs_name.Add(self.schedule_name, pos=(0, 1), flag=wx.EXPAND)
        self.schedule_enabled = wx.CheckBox(panel, label="Agendamento Ativo")
        self.schedule_enabled.SetToolTip("Marque para ativar o envio automático desta campanha.")
        gbs_name.Add(self.schedule_enabled, pos=(1, 1), flag=wx.TOP, border=10)
        gbs_name.AddGrowableCol(1)
        name_sizer.Add(gbs_name, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Novo layout: spins lado a lado, refletindo data real
        trigger_box = wx.StaticBox(panel, label="Agendar para (data base: hoje)")
        trigger_sizer = wx.StaticBoxSizer(trigger_box, wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        now = datetime.now()
        current_month = now.month
        current_day = now.day
        current_year = now.year
        current_hour = now.hour
        current_minute = now.minute

        hbox.Add(wx.StaticText(panel, label="Mês:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.spin_month = wx.SpinCtrl(panel, min=current_month, max=12, initial=current_month)
        self.spin_month.SetToolTip("Selecione o mês de envio (a partir do mês atual).")
        hbox.Add(self.spin_month, 0, wx.RIGHT, 12)

        hbox.Add(wx.StaticText(panel, label="Dia:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        max_day = calendar.monthrange(current_year, current_month)[1]
        self.spin_day = wx.SpinCtrl(panel, min=current_day, max=max_day, initial=current_day)
        self.spin_day.SetToolTip(
            "Selecione o dia do mês (a partir do dia atual, ajustado conforme o mês escolhido)."
        )
        hbox.Add(self.spin_day, 0, wx.RIGHT, 12)

        hbox.Add(wx.StaticText(panel, label="Horas:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.spin_hours = wx.SpinCtrl(panel, min=current_hour, max=23, initial=current_hour)
        self.spin_hours.SetToolTip("Selecione a hora do envio (a partir da hora atual).")
        hbox.Add(self.spin_hours, 0, wx.RIGHT, 12)

        hbox.Add(wx.StaticText(panel, label="Minutos:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
        self.spin_minutes = wx.SpinCtrl(panel, min=current_minute, max=59, initial=current_minute)
        self.spin_minutes.SetToolTip("Selecione os minutos do envio (a partir dos minutos atuais).")
        hbox.Add(self.spin_minutes, 0)

        def update_spins():
            month = self.spin_month.GetValue()
            year = now.year
            min_day = current_day if month == current_month else 1
            max_day = calendar.monthrange(year, month)[1]
            self.spin_day.SetMin(min_day)
            self.spin_day.SetMax(max_day)
            if self.spin_day.GetValue() < min_day:
                self.spin_day.SetValue(min_day)
            elif self.spin_day.GetValue() > max_day:
                self.spin_day.SetValue(max_day)

            day = self.spin_day.GetValue()
            # Se for hoje, trava hora/minuto; se for futuro, destrava tudo
            if month == current_month and day == current_day:
                min_hour = current_hour
                self.spin_hours.SetMin(min_hour)
                self.spin_hours.SetMax(23)
                if self.spin_hours.GetValue() < min_hour:
                    self.spin_hours.SetValue(min_hour)

                hour = self.spin_hours.GetValue()
                if hour == current_hour:
                    min_minute = current_minute
                else:
                    min_minute = 0
                self.spin_minutes.SetMin(min_minute)
                self.spin_minutes.SetMax(59)
                if self.spin_minutes.GetValue() < min_minute:
                    self.spin_minutes.SetValue(min_minute)
            else:
                self.spin_hours.SetMin(0)
                self.spin_hours.SetMax(23)
                if self.spin_hours.GetValue() < 0:
                    self.spin_hours.SetValue(0)
                self.spin_minutes.SetMin(0)
                self.spin_minutes.SetMax(59)
                if self.spin_minutes.GetValue() < 0:
                    self.spin_minutes.SetValue(0)

        def on_month_change(event):
            update_spins()
            event.Skip()

        def on_day_change(event):
            update_spins()
            event.Skip()

        def on_hour_change(event):
            update_spins()
            event.Skip()

        self.spin_month.Bind(wx.EVT_SPINCTRL, on_month_change)
        self.spin_day.Bind(wx.EVT_SPINCTRL, on_day_change)
        self.spin_hours.Bind(wx.EVT_SPINCTRL, on_hour_change)

        trigger_sizer.Add(hbox, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Add(trigger_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(sizer)
        return panel

    def _create_recipients_panel(self, parent: wx.Window) -> wx.Panel:
        """Cria a aba 'Destinatários'."""
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        source_box = wx.StaticBox(panel, label="Fonte dos Destinatários")
        source_sizer = wx.StaticBoxSizer(source_box, wx.VERTICAL)
        self.rb_schedule_list = wx.RadioButton(
            panel, label="Enviar para uma Lista de Contatos", style=wx.RB_GROUP
        )
        self.rb_schedule_list.SetToolTip(
            "A campanha será enviada para os números de telefone em um arquivo .txt ou .xlsx."
        )
        self.rb_schedule_groups = wx.RadioButton(panel, label="Enviar para uma Lista de Grupos")
        self.rb_schedule_groups.SetToolTip(
            "A campanha será enviada para os grupos do WhatsApp cujos nomes estão em um arquivo."
        )
        source_sizer.Add(self.rb_schedule_list, 0, wx.ALL, 10)
        source_sizer.Add(self.rb_schedule_groups, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        sizer.Add(source_sizer, 0, wx.EXPAND | wx.ALL, 10)

        file_box = wx.StaticBox(panel, label="Arquivo de Destinatários (.txt ou .xlsx)")
        file_sizer = wx.StaticBoxSizer(file_box, wx.HORIZONTAL)
        self.schedule_contact_path = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.schedule_contact_path.SetToolTip(
            "Caminho do arquivo de contatos ou grupos selecionado."
        )
        self.schedule_browse_contacts = wx.Button(panel, label="Selecionar Arquivo...")
        self.schedule_browse_contacts.SetToolTip(
            "Procurar pelo arquivo de destinatários (Ctrl+B na aba)"
        )
        file_sizer.Add(self.schedule_contact_path, 1, wx.EXPAND | wx.ALL, 5)
        file_sizer.Add(self.schedule_browse_contacts, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        sizer.Add(file_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(sizer)
        return panel

    def _bind_events(self) -> None:
        """Associa todos os eventos do agendador."""
        self.new_btn.Bind(wx.EVT_BUTTON, self._on_new)
        self.copy_btn.Bind(wx.EVT_BUTTON, self._on_copy)
        self.delete_btn.Bind(wx.EVT_BUTTON, self._on_delete)
        self.Bind(wx.EVT_BUTTON, self._on_save, id=wx.ID_SAVE)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.EndModal(wx.ID_CANCEL), id=wx.ID_CANCEL)
        self.schedule_list_box.Bind(wx.EVT_LISTBOX, self._on_select_schedule)
        self.schedule_browse_contacts.Bind(wx.EVT_BUTTON, self._on_browse_schedule_contacts)
        # Evento do ContentPanel para carregar template
        self.content_panel.use_template_btn.Bind(wx.EVT_BUTTON, self._on_use_template)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_down)

    def _on_key_down(self, event: wx.KeyEvent) -> None:
        keycode = event.GetKeyCode()
        # Cria eventos "falsos" do tipo CommandEvent para os handlers

        def fake_evt(handler):
            evt = wx.CommandEvent(wx.EVT_BUTTON.typeId)
            handler(evt)

        if event.ControlDown():
            if keycode == ord("N"):
                fake_evt(self._on_new)
                return
            elif keycode == ord("P"):
                fake_evt(self._on_copy)
                return
            elif keycode == ord("D"):
                fake_evt(self._on_delete)
                return
            elif keycode == ord("S"):
                fake_evt(self._on_save)
                return
            elif keycode == ord("B") and self.notebook.GetSelection() == 2:
                fake_evt(self._on_browse_schedule_contacts)
                return
        if keycode == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _load_schedules(self):
        self.schedules_data = self.bot.get_schedules()
        self.schedule_list_box.Clear()
        for schedule in self.schedules_data:
            status = "🟢 Ativo" if schedule.get("enabled") else "🔴 Inativo"
            sch_id = schedule.get("id") or ""
            next_run = self.bot.get_next_run_time(str(sch_id)) if sch_id else None
            next_run_str = f" | Próximo: {next_run.strftime('%a %H:%M')}" if next_run else ""
            self.schedule_list_box.Append(f"{schedule['name']} ({status}){next_run_str}")
        if self.schedules_data:
            self.schedule_list_box.SetSelection(0)
            self._populate_form(self.schedules_data[0])
        else:
            self._clear_form()

    def _clear_form(self):
        self.current_schedule_id = None
        self.schedule_name.Clear()
        self.schedule_enabled.SetValue(True)
        now = datetime.now()
        # Spins: mínimo = valor atual
        self.spin_month.SetRange(now.month, 12)
        self.spin_month.SetValue(now.month)
        max_day = calendar.monthrange(now.year, now.month)[1]
        self.spin_day.SetRange(now.day, max_day)
        self.spin_day.SetValue(now.day)
        self.spin_hours.SetRange(now.hour, 23)
        self.spin_hours.SetValue(now.hour)
        self.spin_minutes.SetRange(now.minute, 59)
        self.spin_minutes.SetValue(now.minute)
        self.content_panel.set_value({})
        self.schedule_contact_path.Clear()
        self.rb_schedule_list.SetValue(True)
        self.schedule_name.SetFocus()
        # Não limpa a seleção da lista aqui
        self._update_ui_state()

    def _populate_form(self, schedule_data: dict[str, Any]):
        # Não limpa o formulário inteiro, apenas atualiza os campos
        # Mantém a seleção da lista
        self.current_schedule_id = schedule_data.get("id")
        self.schedule_name.SetValue(schedule_data.get("name", ""))
        self.schedule_enabled.SetValue(schedule_data.get("enabled", False))

        trigger = schedule_data.get("trigger", {})
        month = trigger.get("month")
        day = trigger.get("day")
        hour = trigger.get("hour")
        minute = trigger.get("minute")
        now = datetime.now()
        # Fallback para nomes antigos se necessário
        if month is None:
            month = trigger.get("months", now.month)
        if day is None:
            day = trigger.get("days", now.day)
        if hour is None:
            hour = trigger.get("hours", now.hour)
        if minute is None:
            minute = trigger.get("minutes", now.minute)
        # Spins: mínimo = valor atual
        self.spin_month.SetRange(now.month, 12)
        self.spin_month.SetValue(max(month, now.month))
        max_day = calendar.monthrange(now.year, max(month, now.month))[1]
        min_day = now.day if month == now.month else 1
        self.spin_day.SetRange(min_day, max_day)
        self.spin_day.SetValue(max(min(day, max_day), min_day))
        self.spin_hours.SetRange(now.hour, 23)
        self.spin_hours.SetValue(max(hour, now.hour))
        self.spin_minutes.SetRange(now.minute, 59)
        self.spin_minutes.SetValue(max(minute, now.minute))

        config = schedule_data.get("campaign_config", {})
        self.content_panel.set_value(config)
        self.schedule_contact_path.SetValue(config.get("contact_source", ""))
        is_group_list = SourceType[config.get("source_type", "LIST")] == SourceType.GROUP_LIST
        self.rb_schedule_groups.SetValue(is_group_list)
        self.rb_schedule_list.SetValue(not is_group_list)

        self._update_ui_state()

    def _on_select_schedule(self, event: wx.CommandEvent):
        sel_index = event.GetSelection()
        if sel_index != wx.NOT_FOUND:
            self.schedule_list_box.SetSelection(sel_index)
            self._populate_form(self.schedules_data[sel_index])

    def _on_new(self, event: wx.CommandEvent):
        self._clear_form()

    def _on_copy(self, event: wx.CommandEvent):
        sel_index = self.schedule_list_box.GetSelection()
        if sel_index == wx.NOT_FOUND:
            return

        original = copy.deepcopy(self.schedules_data[sel_index])
        original.pop("id", None)
        original["name"] = f"Cópia de {original['name']}"
        original["enabled"] = False
        self._populate_form(original)
        self.schedule_list_box.SetSelection(wx.NOT_FOUND)

    def _on_delete(self, event: wx.CommandEvent):
        sel_index = self.schedule_list_box.GetSelection()
        if sel_index == wx.NOT_FOUND:
            return

        schedule = self.schedules_data[sel_index]
        agendamento_nome = schedule.get("name", "Desconhecido")
        agendamento_id = schedule.get("id", "SEM_ID")
        if (
            wx.MessageBox(
                (
                    f"Tem certeza que deseja excluir a campanha agendada "
                    f"'{agendamento_nome}'?\n(ID: {agendamento_id})"
                ),
                "Confirmar Exclusão",
                wx.YES_NO | wx.ICON_WARNING,
                self,
            )
            == wx.ID_YES
        ):
            try:
                # Limpa campos antes de excluir
                self._clear_form()
                # Bloco try/except para capturar erros na exclusão
                result = self.bot.delete_schedule(agendamento_id)
                if result:
                    wx.MessageBox(
                        f"Agendamento '{agendamento_nome}' excluído com sucesso!",
                        "Exclusão concluída",
                        wx.OK | wx.ICON_INFORMATION,
                        self,
                    )
                    self._load_schedules()
                else:
                    wx.MessageBox(
                        (
                            f"Falha ao excluir o agendamento (ID: {agendamento_id}).\n"
                            "Verifique se o arquivo não está em uso por outro programa."
                        ),
                        "Erro",
                        wx.OK | wx.ICON_ERROR,
                        self,
                    )
            except Exception as e:
                wx.MessageBox(
                    (
                        f"Ocorreu um erro inesperado ao excluir a campanha "
                        f"(ID: {agendamento_id}):\n"
                        f"Erro: {e}"
                    ),
                    "Erro Crítico",
                    wx.OK | wx.ICON_ERROR,
                    self,
                )

    def _on_save(self, event: wx.CommandEvent):
        # --- Validação ---
        if not self.schedule_name.GetValue().strip():
            wx.MessageBox(
                "O nome da campanha é obrigatório.",
                "Erro de Validação",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        contact_path = self.schedule_contact_path.GetValue()
        if not contact_path or not Path(contact_path).exists():
            wx.MessageBox(
                "Um arquivo de destinatários válido é obrigatório.",
                "Erro de Validação",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        content = self.content_panel.get_value()
        if not content["message"].strip() and not content["attachment"]:
            wx.MessageBox(
                "A campanha deve ter ao menos um texto de mensagem ou um anexo.",
                "Erro de Validação",
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        # --- Coleta de Dados ---
        schedule_data = {
            "id": self.current_schedule_id,
            "name": self.schedule_name.GetValue().strip(),
            "enabled": self.schedule_enabled.IsChecked(),
            "trigger": {
                "month": self.spin_month.GetValue(),
                "day": self.spin_day.GetValue(),
                "hours": self.spin_hours.GetValue(),
                "minutes": self.spin_minutes.GetValue(),
            },
            "campaign_config": {
                "source_type": ("GROUP_LIST" if self.rb_schedule_groups.GetValue() else "LIST"),
                "contact_source": contact_path,
                **content,
            },
        }

        try:
            saved_id = self.bot.save_schedule(schedule_data)
            if saved_id:
                self._load_schedules()
                for i, sch in enumerate(self.schedules_data):
                    if sch.get("id") == saved_id:
                        self.schedule_list_box.SetSelection(i)
                        self._populate_form(sch)
                        break
            else:
                wx.MessageBox(
                    "O agendamento não pôde ser salvo por um motivo desconhecido.",
                    "Falha ao Salvar",
                    wx.OK | wx.ICON_ERROR,
                    self,
                )
        except Exception as e:
            wx.MessageBox(
                f"Ocorreu um erro inesperado ao salvar o agendamento:\n\n{e}",
                "Erro Crítico",
                wx.OK | wx.ICON_ERROR,
                self,
            )

    def _on_use_template(self, event: wx.CommandEvent):
        templates = self.bot.get_templates()
        if not templates:
            wx.MessageBox("Nenhum modelo foi criado.", "Aviso", wx.OK | wx.ICON_INFORMATION, self)
            return

        with TemplatePickerDialog(self, templates) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                template = dialog.GetSelectedTemplate()
                if template:
                    self.content_panel.set_value(template)

    def _update_ui_state(self):
        has_selection = self.schedule_list_box.GetSelection() != wx.NOT_FOUND
        self.copy_btn.Enable(has_selection)
        self.delete_btn.Enable(has_selection)

        is_new = self.current_schedule_id is None
        self.save_btn.SetLabel("&Salvar Nova" if is_new else "&Atualizar Campanha")

    def _on_browse_schedule_contacts(self, event: wx.CommandEvent) -> None:
        path = show_file_dialog(self, "Selecionar Lista de Destinatários", WILDCARD_CONTACTS)
        if path:
            self.schedule_contact_path.SetValue(path)
