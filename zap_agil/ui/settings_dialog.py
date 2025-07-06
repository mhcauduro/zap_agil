"""
Diálogo de configurações do Zap Fácil, incluindo inicialização com o Windows
e opções adicionais, com UI responsiva e intuitiva.
"""

import wx

from zap_agil.core.bot_service import BotService
from zap_agil.core.constants import APP_NAME, THEME_COLORS
from zap_agil.utils.config_manager import ConfigManager
from zap_agil.utils.system_utils import add_to_startup


class SettingsDialog(wx.Dialog):
    """
    Diálogo para gerenciar as configurações gerais do Zap Fácil.
    A UI é projetada para ser responsiva e clara.
    """

    def __init__(self, parent: wx.Window, bot_service: BotService, config_manager: ConfigManager):
        """
        Inicializa o diálogo de configurações.

        Args:
            parent (wx.Window): A janela pai.
            bot_service (BotService): A instância do serviço do bot para notificações.
            config_manager (ConfigManager): O gerenciador de configurações.
        """
        super().__init__(
            parent,
            title=f"Configurações - {APP_NAME}",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MINIMIZE_BOX,
        )
        self.bot_service = bot_service
        self.config = config_manager

        self.SetBackgroundColour(wx.Colour(THEME_COLORS["panel"]))
        self.SetForegroundColour(wx.Colour(THEME_COLORS["text"]))
        self.SetMinSize(wx.Size(450, 280))

        self._init_ui()
        self._bind_events()
        self._load_settings()

        self.CenterOnParent()

    def _init_ui(self) -> None:
        """Inicializa os componentes da interface do diálogo de forma responsiva."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(self)

        gbs = wx.GridBagSizer(10, 10)

        # 1. Configuração de inicialização com o Windows
        startup_box = wx.StaticBox(panel, label="Inicialização do Sistema")
        startup_sizer = wx.StaticBoxSizer(startup_box, wx.VERTICAL)

        self.startup_checkbox = wx.CheckBox(
            panel, label="Iniciar o Zap Fácil automaticamente com o Windows"
        )
        self.startup_checkbox.SetToolTip(
            "Marque para que o Zap Fácil seja iniciado automaticamente junto com o Windows. "
            "Opção acessível por teclado e compatível com leitores de tela."
        )
        startup_sizer.Add(self.startup_checkbox, 0, wx.ALL, 10)
        gbs.Add(startup_sizer, pos=(0, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL, border=10)

        # 2. Configuração de delay padrão para campanhas
        delay_box = wx.StaticBox(panel, label="Padrões de Campanha")
        delay_sizer = wx.StaticBoxSizer(delay_box, wx.HORIZONTAL)

        delay_label = wx.StaticText(panel, label="Pausa padrão entre envios (segundos):")
        delay_sizer.Add(delay_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        self.delay_ctrl = wx.SpinCtrl(panel, min=1, max=120, size=wx.Size(80, -1))
        self.delay_ctrl.SetToolTip(
            "Define o intervalo padrão (em segundos) entre o envio de cada mensagem em uma "
            "campanha. Valores permitidos: 1 a 120 segundos. Campo acessível por teclado."
        )
        delay_sizer.Add(self.delay_ctrl, 1, wx.EXPAND)
        gbs.Add(delay_sizer, pos=(1, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL, border=10)

        # 3. Botões de Ação
        button_sizer = wx.StdDialogButtonSizer()
        save_button = wx.Button(panel, wx.ID_OK, label="Salvar")
        save_button.SetToolTip(
            "Salvar as alterações realizadas nas configurações. Atalho: Ctrl+S. "
            "Botão acessível por teclado."
        )
        button_sizer.AddButton(save_button)
        cancel_button = wx.Button(panel, wx.ID_CANCEL, label="Cancelar")
        cancel_button.SetToolTip(
            "Fechar a janela de configurações sem salvar alterações. Atalho: Esc. "
            "A navegação é acessível por teclado."
        )
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()

        gbs.Add(
            button_sizer,
            pos=(2, 0),
            span=(1, 2),
            flag=wx.ALIGN_RIGHT | wx.TOP | wx.RIGHT | wx.BOTTOM,
            border=10,
        )
        gbs.AddGrowableCol(1)
        panel.SetSizer(gbs)
        main_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizerAndFit(main_sizer)
        self.startup_checkbox.SetFocus()

    def _load_settings(self) -> None:
        """Carrega as configurações atuais e as aplica na UI."""
        # Usando o novo método para ler a configuração booleana de forma limpa.
        is_startup_enabled = self.config.get_boolean_setting(
            "General", "start_on_boot", fallback=False
        )
        self.startup_checkbox.SetValue(is_startup_enabled)

        default_delay_str = self.config.get_setting("Campaign", "default_delay", "2")
        try:
            delay_val = int(default_delay_str)
        except ValueError:
            delay_val = 2  # Usa um padrão seguro se o valor for inválido
        self.delay_ctrl.SetValue(delay_val)

    def _bind_events(self) -> None:
        """Associa eventos aos componentes da interface."""
        self.Bind(wx.EVT_BUTTON, self._on_ok, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_down)

    def _on_key_down(self, event: wx.KeyEvent) -> None:
        """Gerencia atalhos de teclado para salvar e cancelar."""
        if event.ControlDown() and event.GetKeyCode() == ord("S"):
            evt = wx.CommandEvent(wx.EVT_BUTTON.typeId, self.FindWindowById(wx.ID_OK).GetId())
            self._on_ok(evt)
            return
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            evt = wx.CommandEvent(wx.EVT_BUTTON.typeId, self.FindWindowById(wx.ID_CANCEL).GetId())
            self._on_cancel(evt)
            return
        event.Skip()

    def _on_ok(self, event: wx.CommandEvent) -> None:
        """Salva as configurações e fecha o diálogo."""
        try:
            # 1. Salva a configuração de inicialização com o Windows
            is_checked = self.startup_checkbox.IsChecked()
            # Tenta alterar a configuração de inicialização primeiro
            if not add_to_startup(enable=is_checked):
                # Se falhar (ex: permissão), notifica o usuário e interrompe o salvamento
                error_msg = (
                    "Falha ao modificar a configuração de inicialização com o sistema.\n"
                    "Tente executar o programa como administrador."
                )
                wx.MessageBox(error_msg, "Erro de Permissão", wx.OK | wx.ICON_ERROR, self)
                # Reverte a mudança na UI para refletir o estado real
                self.startup_checkbox.SetValue(not is_checked)
                # Interrompe a função _on_ok, mantendo o diálogo aberto
                return

            # Se a alteração foi bem-sucedida, salva o estado no arquivo de configuração
            self.config.save_setting("General", "start_on_boot", str(is_checked).lower())
            status = "ativada" if is_checked else "desativada"
            log_msg = f"Configuração 'Iniciar com o Sistema' foi {status}."
            self.bot_service._notify("log", log_msg, THEME_COLORS["log_success"])

            # 2. Salva a configuração de delay padrão
            delay_value = self.delay_ctrl.GetValue()
            self.config.save_setting("Campaign", "default_delay", str(delay_value))
            self.bot_service._notify(
                "log",
                f"Delay padrão salvo como {delay_value} segundos.",
                THEME_COLORS["log_success"],
            )

            wx.MessageBox(
                "Configurações salvas com sucesso!",
                "Sucesso",
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            self.EndModal(wx.ID_OK)

        except Exception as e:
            error_msg = f"Não foi possível salvar as configurações.\n\nErro: {e}"
            wx.MessageBox(error_msg, "Erro de Configuração", wx.OK | wx.ICON_ERROR, self)
            self.bot_service._notify(
                "log", f"Erro ao salvar configurações: {e}", THEME_COLORS["log_error"]
            )

    def _on_cancel(self, event: wx.CommandEvent) -> None:
        """Fecha o diálogo sem salvar as alterações."""
        self.EndModal(wx.ID_CANCEL)
