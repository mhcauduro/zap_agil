"""
Painel de configuração avançado para campanhas do Zap Fácil, com anexos separados
(documento, mídia, áudio), controles de gravação e UX aprimorado.
"""

import logging
import shutil
from pathlib import Path
from typing import Any

import wx

from zap_agil.core.bot_service import BotService
from zap_agil.core.constants import (
    AUDIO_EXTENSIONS,
    DEFAULT_CAMPAIGN_MSG,
    DOCUMENT_EXTENSIONS,
    IMAGE_VIDEO_EXTENSIONS,
    THEME_COLORS,
    WILDCARD_AUDIO,
    WILDCARD_DOCUMENTS,
    WILDCARD_MEDIA,
    AudioState,
)
from zap_agil.ui.ui_utils import show_file_dialog


def format_duration(seconds: float) -> str:
    """
    Formata segundos para uma string legível (ex: 1m 30s).
    """
    if seconds <= 0:
        return ""
    m = int(seconds // 60)
    s = int(seconds % 60)
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


class ContentPanel(wx.Panel):
    """
    Painel avançado para configurar o conteúdo de uma campanha (mensagem e anexos).
    """

    bot: BotService
    audio_state: AudioState
    audio_duration: float
    use_template_btn: wx.Button
    message_ctrl: wx.TextCtrl
    doc_ctrl: wx.TextCtrl
    browse_doc_btn: wx.Button
    clear_doc_btn: wx.Button
    media_ctrl: wx.TextCtrl
    browse_media_btn: wx.Button
    clear_media_btn: wx.Button
    audio_ctrl: wx.TextCtrl
    browse_audio_btn: wx.Button
    record_audio_btn: wx.Button
    clear_audio_btn: wx.Button
    play_audio_btn: wx.Button
    audio_status_lbl: wx.StaticText

    def __init__(self, parent: wx.Window, bot_service: BotService) -> None:
        """
        Inicializa o painel de conteúdo da campanha.
        Args:
            parent: Janela pai.
            bot_service: Instância do BotService para integração core.
        """
        super().__init__(parent)
        self.bot = bot_service
        self.SetBackgroundColour(wx.Colour(THEME_COLORS["panel"]))
        self.SetForegroundColour(wx.Colour(THEME_COLORS["text"]))
        self.audio_state: AudioState = AudioState.IDLE
        self.audio_duration: float = 0.0

        self._init_ui()
        self._bind_events()

        # Garante que o painel sempre está sincronizado com o estado de áudio
        self.bot.subscribe("audio_state", self.update_audio_controls)

        # Inicia a UI no estado correto
        self.update_audio_controls(AudioState.IDLE)
        self.message_ctrl.SetFocus()

    def _init_ui(self) -> None:
        """
        Inicializa os componentes visuais do painel.
        """
        main_sizer: wx.BoxSizer = wx.BoxSizer(wx.VERTICAL)

        # (Removido campo de adição manual de contato - código morto)

        # 1. Seção de Mensagem Pronta (Template)
        template_sizer: wx.BoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.use_template_btn: wx.Button = wx.Button(self, label="Escolher Mensagem Pronta...")
        self.use_template_btn.SetToolTip("Escolher uma mensagem pronta e anexo (Ctrl+T)")
        template_sizer.Add(self.use_template_btn, 0, wx.ALIGN_LEFT, 0)
        main_sizer.Add(template_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # 3. Seção de Mensagem
        msg_box: wx.StaticBox = wx.StaticBox(self, label="Texto da Mensagem")
        msg_sizer: wx.StaticBoxSizer = wx.StaticBoxSizer(msg_box, wx.VERTICAL)
        msg_hint: wx.StaticText = wx.StaticText(
            self,
            label=(
                "Dica: Use @Nome, @Vencimento, etc., para personalizar com colunas do seu arquivo."
            ),
        )
        msg_hint.SetForegroundColour(wx.Colour(THEME_COLORS["text_light"]))
        self.message_ctrl: wx.TextCtrl = wx.TextCtrl(
            self, style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER
        )
        self.message_ctrl.SetHint(
            "Ex.: Olá @Nome, sua fatura vence em @Vencimento. Segue anexo o boleto."
        )
        self.message_ctrl.SetToolTip(self.message_ctrl.GetHint())
        self.message_ctrl.SetValue(DEFAULT_CAMPAIGN_MSG)
        msg_sizer.Add(msg_hint, 0, wx.EXPAND | wx.ALL, 5)
        msg_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.ALL, 5)
        msg_sizer.Add(self.message_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(msg_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # 4. Seção de Anexos
        attachment_box: wx.StaticBox = wx.StaticBox(
            self, label="Anexo (Opcional - Apenas 1 será enviado)"
        )
        attachment_sizer: wx.StaticBoxSizer = wx.StaticBoxSizer(attachment_box, wx.VERTICAL)
        gbs: wx.GridBagSizer = wx.GridBagSizer(5, 5)
        gbs.Add(
            wx.StaticText(self, label="Documento:"),
            pos=(0, 0),
            flag=wx.ALIGN_CENTER_VERTICAL,
        )
        self.doc_ctrl: wx.TextCtrl = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.doc_ctrl.SetToolTip(
            "Campo somente leitura. Exibe o caminho do documento anexado. "
            "Clique em 'Anexar documento' para selecionar um arquivo. "
            "Use 'Descartar' para remover o anexo."
        )
        self.browse_doc_btn: wx.Button = wx.Button(self, label="Anexar documento")
        self.browse_doc_btn.SetToolTip("Selecionar e anexar um documento ao envio. Atalho: Ctrl+D.")
        self.clear_doc_btn: wx.Button = wx.Button(self, label="Descartar")
        self.clear_doc_btn.SetToolTip(
            "Remover o documento anexado. O campo ficará vazio e nenhum documento será enviado."
        )
        gbs.Add(self.doc_ctrl, pos=(0, 1), flag=wx.EXPAND)
        gbs.Add(self.browse_doc_btn, pos=(0, 2), flag=wx.LEFT, border=5)
        gbs.Add(self.clear_doc_btn, pos=(0, 3), flag=wx.LEFT, border=2)
        gbs.Add(
            wx.StaticText(self, label="Mídia:"),
            pos=(1, 0),
            flag=wx.ALIGN_CENTER_VERTICAL,
        )
        self.media_ctrl: wx.TextCtrl = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.media_ctrl.SetToolTip(
            "Campo somente leitura. Exibe o caminho da mídia anexada (imagem/vídeo). "
            "Clique em 'Anexar mídia' para selecionar um arquivo. "
            "Use 'Descartar' para remover o anexo."
        )
        self.browse_media_btn: wx.Button = wx.Button(self, label="Anexar mídia")
        self.browse_media_btn.SetToolTip(
            "Selecionar e anexar uma mídia (imagem ou vídeo) ao envio. Atalho: Ctrl+I."
        )
        self.clear_media_btn: wx.Button = wx.Button(self, label="Descartar")
        self.clear_media_btn.SetToolTip(
            "Remover a mídia anexada. O campo ficará vazio e nenhuma mídia será enviada."
        )
        gbs.Add(self.media_ctrl, pos=(1, 1), flag=wx.EXPAND)
        gbs.Add(self.browse_media_btn, pos=(1, 2), flag=wx.LEFT, border=5)
        gbs.Add(self.clear_media_btn, pos=(1, 3), flag=wx.LEFT, border=2)
        gbs.Add(
            wx.StaticText(self, label="Áudio:"),
            pos=(2, 0),
            flag=wx.ALIGN_CENTER_VERTICAL,
        )
        self.audio_ctrl: wx.TextCtrl = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.audio_ctrl.SetToolTip(
            "Campo somente leitura. Exibe o caminho do áudio anexado. "
            "Clique em 'Anexar áudio' para selecionar um arquivo, "
            "ou utilize os botões de gravação. "
            "Use 'Descartar' para remover o anexo."
        )
        self.browse_audio_btn: wx.Button = wx.Button(self, label="Anexar áudio")
        self.browse_audio_btn.SetToolTip(
            "Selecionar e anexar um arquivo de áudio ao envio. Atalho: Ctrl+A."
        )
        self.record_audio_btn: wx.Button = wx.Button(self, label="● Gravar")
        self.record_audio_btn.SetToolTip(
            "Iniciar gravação de áudio pelo microfone. Clique novamente para parar a gravação."
        )
        self.clear_audio_btn: wx.Button = wx.Button(self, label="Descartar")
        self.clear_audio_btn.SetToolTip(
            "Remover o áudio anexado ou gravado. O campo ficará vazio e nenhum áudio será enviado."
        )
        self.play_audio_btn: wx.Button = wx.Button(self, label="▶ Ouvir")
        self.play_audio_btn.SetToolTip("Ouvir o áudio anexado ou gravado.")
        self.audio_status_lbl: wx.StaticText = wx.StaticText(self, label="")
        self.audio_status_lbl.SetToolTip("Exibe o status da gravação ou reprodução do áudio.")
        audio_btn_sizer: wx.BoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        audio_btn_sizer.Add(self.browse_audio_btn, 0, wx.RIGHT, 2)
        audio_btn_sizer.Add(self.record_audio_btn, 0, wx.RIGHT, 2)
        audio_btn_sizer.Add(self.play_audio_btn, 0, wx.RIGHT, 2)
        audio_btn_sizer.Add(self.clear_audio_btn, 0, wx.RIGHT, 5)
        gbs.Add(self.audio_ctrl, pos=(2, 1), flag=wx.EXPAND)
        gbs.Add(audio_btn_sizer, pos=(2, 2), span=(1, 2), flag=wx.ALIGN_LEFT)
        gbs.Add(
            self.audio_status_lbl,
            pos=(3, 1),
            span=(1, 3),
            flag=wx.ALIGN_LEFT | wx.TOP,
            border=5,
        )
        gbs.AddGrowableCol(1)
        attachment_sizer.Add(gbs, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(attachment_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.SetSizer(main_sizer)

    def _bind_events(self) -> None:
        """
        Associa eventos e atalhos aos componentes do painel.
        """
        self.browse_doc_btn.Bind(wx.EVT_BUTTON, self._on_browse_doc)
        self.clear_doc_btn.Bind(wx.EVT_BUTTON, self._on_clear_doc)
        self.browse_media_btn.Bind(wx.EVT_BUTTON, self._on_browse_media)
        self.clear_media_btn.Bind(wx.EVT_BUTTON, self._on_clear_media)
        self.browse_audio_btn.Bind(wx.EVT_BUTTON, self._on_browse_audio)
        self.record_audio_btn.Bind(wx.EVT_BUTTON, self._on_record_audio)
        self.clear_audio_btn.Bind(wx.EVT_BUTTON, self._on_clear_audio)
        self.play_audio_btn.Bind(wx.EVT_BUTTON, self._on_play_audio)

        # Atalhos de teclado para anexos
        self.browse_doc_btn.SetAcceleratorTable(
            wx.AcceleratorTable([(wx.ACCEL_CTRL, ord("D"), self.browse_doc_btn.GetId())])
        )
        self.browse_media_btn.SetAcceleratorTable(
            wx.AcceleratorTable([(wx.ACCEL_CTRL, ord("I"), self.browse_media_btn.GetId())])
        )
        self.browse_audio_btn.SetAcceleratorTable(
            wx.AcceleratorTable([(wx.ACCEL_CTRL, ord("A"), self.browse_audio_btn.GetId())])
        )

        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy)

    # (Removido método _on_manual_contact_enter - código morto)

    def _on_destroy(self, event: wx.Event) -> None:
        """
        Desinscreve eventos do bot ao destruir o painel.
        Garante que o callback de áudio não fique registrado após o fechamento.
        """
        event.Skip()
        try:
            # Tenta remover o subscriber de forma segura
            callbacks = self.bot.subscribers.get("audio_state", [])
            if self.update_audio_controls in callbacks:
                callbacks.remove(self.update_audio_controls)
        except Exception as exc:
            logging.warning(f"Erro ao remover callback de áudio: {exc}")

    def _clear_all_attachments(self, preserve: wx.TextCtrl | None = None) -> None:
        """
        Limpa todos os campos de anexo, exceto o campo passado em `preserve`.
        Também reseta o estado de áudio na UI.
        """
        if self.doc_ctrl != preserve:
            self.doc_ctrl.Clear()
        if self.media_ctrl != preserve:
            self.media_ctrl.Clear()
        if self.audio_ctrl != preserve:
            self.audio_ctrl.Clear()
            self.bot.discard_recorded_audio()
            # Garante que a UI de áudio seja totalmente resetada
            self.update_audio_controls(AudioState.IDLE, 0.0)
        self._update_ui_states()

    # ... (Handlers _on_browse_doc, _on_clear_doc, etc. permanecem iguais) ...
    def _on_browse_doc(self, event: wx.CommandEvent) -> None:
        """
        Abre diálogo para selecionar documento e atualiza UI.
        """
        path = show_file_dialog(self, "Selecionar Documento", WILDCARD_DOCUMENTS)
        if path:
            self.doc_ctrl.SetValue(path)
            self._clear_all_attachments(preserve=self.doc_ctrl)
        self._update_ui_states()

    def _on_clear_doc(self, event: wx.CommandEvent) -> None:
        """
        Limpa o campo de documento.
        """
        self.doc_ctrl.Clear()
        self._update_ui_states()

    def _on_browse_media(self, event: wx.CommandEvent) -> None:
        """
        Abre diálogo para selecionar mídia e atualiza UI.
        """
        path = show_file_dialog(self, "Selecionar Mídia (Imagem/Vídeo)", WILDCARD_MEDIA)
        if path:
            self.media_ctrl.SetValue(path)
            self._clear_all_attachments(preserve=self.media_ctrl)
        self._update_ui_states()

    def _on_clear_media(self, event: wx.CommandEvent) -> None:
        """
        Limpa o campo de mídia.
        """
        self.media_ctrl.Clear()
        self._update_ui_states()

    def _on_browse_audio(self, event: wx.CommandEvent) -> None:
        """
        Abre diálogo para selecionar áudio e atualiza UI.
        """
        path = show_file_dialog(self, "Selecionar Áudio", WILDCARD_AUDIO)
        if path:
            self.audio_ctrl.SetValue(path)
            self._clear_all_attachments(preserve=self.audio_ctrl)
            duration = self.bot.get_audio_duration(path)
            self.update_audio_controls(AudioState.READY, duration)

    def _on_clear_audio(self, event: wx.CommandEvent) -> None:
        """
        Limpa o campo de áudio e reseta controles de áudio.
        """
        # Este método agora só precisa chamar discard e resetar a UI para IDLE
        self.audio_ctrl.Clear()
        self.bot.discard_recorded_audio()
        self.update_audio_controls(AudioState.IDLE, 0.0)

    def _on_record_audio(self, event: wx.CommandEvent) -> None:
        """
        Inicia ou para gravação de áudio conforme o estado atual.
        """
        if self.audio_state == AudioState.IDLE:
            self._clear_all_attachments(preserve=self.audio_ctrl)
            self.bot.start_recording()
        elif self.audio_state == AudioState.RECORDING:
            self.bot.stop_recording()
            self.play_audio_btn.SetFocus()

    def _on_play_audio(self, event: wx.CommandEvent) -> None:
        """
        Gerencia play/pause/resume do áudio conforme o estado atual.
        """
        """
        Esta função é um dispatcher para play/pause/resume.
        """
        # Se o áudio estiver pronto, prepara e toca.
        if self.audio_state in [AudioState.READY]:
            path = self.audio_ctrl.GetValue()
            if not path or not Path(path).exists():
                wx.MessageBox(
                    "Nenhum arquivo de áudio válido para reproduzir.",
                    "Erro",
                    wx.OK | wx.ICON_ERROR,
                )
                return
            if Path(path) != self.bot.temp_audio_path:
                try:
                    shutil.copy(path, self.bot.temp_audio_path)
                except Exception as e:
                    wx.MessageBox(
                        f"Falha ao preparar o áudio para reprodução: {e}",
                        "Erro",
                        wx.OK | wx.ICON_ERROR,
                    )
                    return
            self.bot.play_recorded_audio()

        # Se estiver tocando, pausa.
        elif self.audio_state == AudioState.PLAYING:
            self.bot.pause_playback()

        # Se estiver pausado, retoma.
        elif self.audio_state == AudioState.PAUSED:
            self.bot.resume_playback()

    def update_audio_controls(self, state: AudioState, duration: float | None = 0.0) -> None:
        """
        Atualiza os controles de áudio conforme o estado da máquina de estados.
        """
        """
        Implementa a máquina de estados estrita para os botões de áudio.
        """
        if not self:
            return  # Medida de segurança para evitar erro em objeto destruído

        self.audio_state = state
        if duration is not None and duration > 0:
            self.audio_duration = duration

        if state == AudioState.READY and self.bot.temp_audio_path.exists():
            self.audio_ctrl.SetValue(str(self.bot.temp_audio_path))

        # Salva o botão atualmente focado
        focused_widget = wx.Window.FindFocus()

        # Configurações padrão (tudo desabilitado)
        play_label = "▶ Ouvir"
        status_text = ""
        self.record_audio_btn.Enable(False)
        self.play_audio_btn.Enable(False)
        self.clear_audio_btn.Enable(False)
        self.browse_audio_btn.Enable(False)

        # Habilita botões com base no estado
        if state == AudioState.IDLE:
            self.record_audio_btn.Enable(True)
            self.browse_audio_btn.Enable(True)
        elif state == AudioState.RECORDING:
            self.record_audio_btn.Enable(True)
            status_text = "Gravando..."
        elif state == AudioState.READY:
            self.play_audio_btn.Enable(True)
            self.clear_audio_btn.Enable(True)
            duration_str = format_duration(self.audio_duration)
            status_text = f"Pronto ({duration_str})" if duration_str else "Pronto"
        elif state == AudioState.PLAYING:
            self.play_audio_btn.Enable(True)
            play_label = "❚❚ Pausar"
            status_text = "Reproduzindo..."
        elif state == AudioState.PAUSED:
            self.play_audio_btn.Enable(True)
            self.clear_audio_btn.Enable(True)
            play_label = "▶ Retomar"
            status_text = "Pausado"

        self.record_audio_btn.SetLabel("■ Parar" if state == AudioState.RECORDING else "● Gravar")
        self.play_audio_btn.SetLabel(play_label)
        self.audio_status_lbl.SetLabel(status_text)

        # Restaura o foco se o widget ainda existir e estiver habilitado
        if focused_widget and focused_widget.IsEnabled():
            focused_widget.SetFocus()

        self._update_ui_states()

    def _update_ui_states(self) -> None:
        """
        Atualiza o estado dos botões de anexo conforme preenchimento.
        Atualiza o estado dos botões que não são de áudio.
        """
        self.clear_doc_btn.Enable(bool(self.doc_ctrl.GetValue()))
        self.clear_media_btn.Enable(bool(self.media_ctrl.GetValue()))

    def get_value(self) -> dict[str, Any]:
        """
        Retorna o conteúdo atual do painel (mensagem e anexo selecionado).
        """
        doc = self.doc_ctrl.GetValue()
        media = self.media_ctrl.GetValue()
        audio = self.audio_ctrl.GetValue()
        attachment = ""
        if doc:
            attachment = doc
        elif media:
            attachment = media
        elif audio:
            attachment = audio
        return {"message": self.message_ctrl.GetValue(), "attachment": attachment}

    def set_value(self, config: dict[str, Any]) -> None:
        """
        Preenche o painel com dados de configuração externa.
        """
        self.message_ctrl.SetValue(config.get("message", ""))
        self._clear_all_attachments()

        attachment_path_str = config.get("attachment", "")
        if attachment_path_str:
            attachment_path = Path(attachment_path_str)
            if attachment_path.exists():
                ext = attachment_path.suffix.lower()
                if ext in DOCUMENT_EXTENSIONS:
                    self.doc_ctrl.SetValue(attachment_path_str)
                elif ext in IMAGE_VIDEO_EXTENSIONS:
                    self.media_ctrl.SetValue(attachment_path_str)
                elif ext in AUDIO_EXTENSIONS:
                    self.audio_ctrl.SetValue(attachment_path_str)
                    duration = self.bot.get_audio_duration(attachment_path_str)
                    # Define o estado como PRONTO para habilitar os botões corretos
                    self.update_audio_controls(AudioState.READY, duration)

        # Se nenhum anexo de áudio foi carregado, garante que o estado seja IDLE
        if not self.audio_ctrl.GetValue():
            self.update_audio_controls(AudioState.IDLE, 0.0)

        self._update_ui_states()
