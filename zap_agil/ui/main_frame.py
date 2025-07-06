"""
Define a janela principal (MainFrame) do Zap Fácil, com uma interface
responsiva, intuitiva e um fluxo de trabalho claro, utilizando um modelo
de comunicação desacoplado para máxima performance.
"""

import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import wx
import wx.adv

from zap_agil.core.app_events import (
    EVT_CAMPAIGN_STATUS,
    EVT_CONNECTION_STATUS,
    EVT_LOG,
    EVT_PROGRESS_UPDATE,
    EVT_STATUS_UPDATE,
    AudioStateEvent,
    CampaignStatusEvent,
    ConnectionStatusEvent,
    LogEvent,
    ProgressUpdateEvent,
    StatusUpdateEvent,
)
from zap_agil.core.bot_service import BotService
from zap_agil.core.constants import (
    APP_ICON_FILENAME,
    APP_NAME,
    APP_VERSION,
    CLIENT_LOGO_FILENAME,
    COMPANY_NAME,
    THEME_COLORS,
    WILDCARD_CONTACTS,
    CampaignState,
    ConnectionState,
)
from zap_agil.ui.dialogs import (
    CampaignSchedulerDialog,
    NewsDialog,
    ReportsDialog,
    TemplatePickerDialog,
    TemplatesDialog,
    TipsDialog,
)
from zap_agil.ui.panels import ContentPanel
from zap_agil.ui.settings_dialog import SettingsDialog
from zap_agil.ui.ui_utils import show_file_dialog
from zap_agil.utils.config_manager import ConfigManager
from zap_agil.utils.logging_config import logging
from zap_agil.utils.system_utils import resource_path

if TYPE_CHECKING:
    import wx


class TaskBarIcon(wx.adv.TaskBarIcon):
    """Ícone da bandeja do sistema para acesso rápido e notificações."""

    def __init__(self, frame: wx.Frame) -> None:
        super().__init__()
        self.frame: wx.Frame = frame
        icon_path: str = str(resource_path(APP_ICON_FILENAME))
        if Path(icon_path).exists():
            icon: wx.Icon = wx.Icon(icon_path, wx.BITMAP_TYPE_ICO)
            self.SetIcon(icon, f"{APP_NAME} - {COMPANY_NAME}")

        # Restaurar janela com clique simples, duplo clique ou Enter
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.frame._on_restore)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_UP, self.frame._on_restore)
        # self.Bind(wx.adv.EVT_TASKBAR_KEY_DOWN, self._on_key_down)  # Evento não existe no wx.adv

    def _on_key_down(self, event: wx.Event) -> None:
        # Restaura janela ao pressionar Enter no ícone da bandeja
        if hasattr(event, "GetKeyCode") and event.GetKeyCode() in (
            wx.WXK_RETURN,
            wx.WXK_NUMPAD_ENTER,
        ):
            self.frame._on_restore(event)

    def create_popup_menu(self) -> wx.Menu:
        """Cria o menu de contexto ao clicar com o botão direito na bandeja."""
        menu: wx.Menu = wx.Menu()
        menu.Append(wx.ID_OPEN, "&Restaurar Janela")
        menu.AppendSeparator()
        menu.Append(wx.ID_EXIT, "&Fechar Aplicativo")
        self.Bind(wx.EVT_MENU, self.frame._on_restore, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.frame._on_request_close, id=wx.ID_EXIT)
        return menu


class MainFrame(wx.Frame):
    """A janela principal do Zap Fácil, o centro de controle da aplicação."""

    is_shutting_down: bool
    config: ConfigManager
    bot_service: BotService
    task_bar_icon: TaskBarIcon | None
    notebook: wx.Notebook
    content_panel: ContentPanel
    progress_bar: wx.Gauge
    log: wx.TextCtrl
    status_bar: wx.StatusBar
    activity_indicator: wx.ActivityIndicator
    rb_manual: wx.RadioButton
    rb_list_numbers: wx.RadioButton
    rb_list_groups: wx.RadioButton
    list_panel: wx.Panel
    contact_list_path: wx.TextCtrl
    browse_contacts_btn: wx.Button
    manual_panel: wx.Panel
    manual_name: wx.TextCtrl
    manual_number: wx.TextCtrl
    add_contact_btn: wx.Button
    manual_contact_list: wx.ListCtrl
    remove_contact_btn: wx.Button
    delay_input: wx.SpinCtrl
    pause_campaign_btn: wx.Button
    stop_campaign_btn: wx.Button
    start_campaign_btn: wx.Button

    # Removido __init__ duplicado conforme apontado pelo Ruff

    def __init__(self: "MainFrame") -> None:
        super().__init__(None, title=f"{APP_NAME} v{APP_VERSION}", style=wx.DEFAULT_FRAME_STYLE)
        self.is_shutting_down = False
        self.config = ConfigManager()
        self.bot_service = BotService()

        self.SetMinSize(wx.Size(800, 750))
        self.SetBackgroundColour(wx.Colour(THEME_COLORS["background"]))
        self.SetIcon(wx.Icon(str(resource_path(APP_ICON_FILENAME)), wx.BITMAP_TYPE_ICO))
        self.task_bar_icon: TaskBarIcon | None = TaskBarIcon(self)

        try:
            self._init_ui()
            self._create_menu_bar()
            self._bind_ui_events()
            self._subscribe_to_bot_events()
            logging.debug("MainFrame inicializado com sucesso.")
        except Exception as exc:
            logging.error(f"Erro ao inicializar MainFrame: {exc}\n{traceback.format_exc()}")
            wx.MessageBox(
                f"Erro crítico ao inicializar a interface: {exc}",
                "Erro",
                wx.OK | wx.ICON_ERROR,
            )
            raise

        self._log_message(f"Bem-vindo ao {APP_NAME}!", THEME_COLORS["accent_purple"])
        wx.CallLater(1500, self.start_background_services)

        self.Center()
        self.Show()
        self._update_button_states()

    def start_background_services(self: "MainFrame") -> None:
        """Inicia serviços de conexão em thread separada."""
        try:
            threading.Thread(target=self.bot_service.start_connection, daemon=True).start()
            logging.debug("Serviços de conexão iniciados em thread background.")
        except Exception as exc:
            logging.error(f"Erro ao iniciar serviços de conexão: {exc}")

    def _init_ui(self: "MainFrame") -> None:
        """Inicializa os componentes visuais da janela principal."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 1. Cabeçalho
        header_sizer = self._create_header_panel(panel)
        # Tooltip acessível para o cabeçalho
        for child in header_sizer.GetChildren():
            wnd = child.GetWindow()
            if wnd and isinstance(wnd, wx.StaticText):
                wnd.SetToolTip(f"{APP_NAME} - Sistema de campanhas automatizadas para WhatsApp.")
        main_sizer.Add(header_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # 2. Notebook com abas para o fluxo de trabalho
        self.notebook = wx.Notebook(panel)
        self.notebook.SetBackgroundColour(wx.Colour(THEME_COLORS["panel"]))

        recipients_panel = self._create_recipients_panel(self.notebook)
        recipients_panel.SetToolTip(
            "Aba de destinatários: defina contatos ou grupos para envio da campanha."
        )
        self.notebook.AddPage(recipients_panel, "1. Destinatários")

        self.content_panel = ContentPanel(self.notebook, self.bot_service)
        self.content_panel.SetToolTip(
            "Aba de mensagem e anexos: escreva a mensagem e anexe arquivos, mídias ou áudios."
        )
        self.notebook.AddPage(self.content_panel, "2. Mensagem e Anexos")

        main_sizer.Add(self.notebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # 3. Barra de Progresso (inicialmente oculta)
        self.progress_bar = wx.Gauge(panel, range=100, style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        self.progress_bar.SetToolTip("Barra de progresso da campanha em execução.")
        self.progress_bar.Hide()
        main_sizer.Add(self.progress_bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # 4. Histórico de Eventos
        log_box = wx.StaticBox(panel, label="Histórico de Eventos")
        log_sizer = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        self.log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.log.SetBackgroundColour(wx.Colour(THEME_COLORS["background"]))
        self.log.SetToolTip(
            "Área de histórico: registro detalhado de atividades, conexões e eventos do sistema."
        )
        log_sizer.Add(self.log, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(log_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # 5. Painel de Controle (Pausa e Botões de Ação)
        control_sizer = self._create_control_panel(panel)
        # Tooltip geral para o painel de controle
        for child in control_sizer.GetChildren():
            wnd = child.GetWindow()
            if wnd and isinstance(wnd, wx.Button) and not wnd.GetToolTip():
                wnd.SetToolTip("Botão de controle da campanha.")
        main_sizer.Add(control_sizer, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(main_sizer)
        self.status_bar = self.CreateStatusBar(2)
        self.status_bar.SetStatusWidths([-3, -1])
        self.status_bar.SetStatusText("Inicializando...", 0)
        self.notebook.SetFocus()

    def _create_header_panel(self: "MainFrame", parent: wx.Panel) -> wx.BoxSizer:
        """Cria o painel de cabeçalho com logo, título e indicador de atividade."""
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        logo_path = str(resource_path(CLIENT_LOGO_FILENAME))
        if Path(logo_path).exists():
            logo_img = wx.Image(logo_path, wx.BITMAP_TYPE_ANY).Scale(150, 40, wx.IMAGE_QUALITY_HIGH)
            # wx.BitmapBundle.FromBitmap garante compatibilidade com wxPython 4+
            logo_bmp_bundle = wx.BitmapBundle.FromBitmap(wx.Bitmap(logo_img))
            logo_widget = wx.StaticBitmap(parent, wx.ID_ANY, logo_bmp_bundle)
            header_sizer.Add(logo_widget, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 20)

        title = wx.StaticText(parent, label=APP_NAME)
        title.SetFont(wx.Font(20, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        title.SetForegroundColour(wx.Colour(THEME_COLORS["primary"]))
        header_sizer.Add(title, 0, wx.ALIGN_CENTER_VERTICAL)
        header_sizer.AddStretchSpacer()

        self.activity_indicator = wx.ActivityIndicator(parent)
        self.activity_indicator.SetToolTip("Indica atividade de conexão ou campanha em andamento.")
        header_sizer.Add(self.activity_indicator, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        return header_sizer

    def _create_recipients_panel(self: "MainFrame", parent_notebook: wx.Notebook) -> wx.Panel:
        """Cria o painel de seleção de destinatários."""
        panel = wx.Panel(parent_notebook)
        panel.SetBackgroundColour(wx.Colour(THEME_COLORS["panel"]))
        sizer = wx.GridBagSizer(10, 10)

        # Seletor da Fonte dos Contatos
        source_box = wx.StaticBox(panel, label="Fonte dos Destinatários")
        source_sizer = wx.StaticBoxSizer(source_box, wx.VERTICAL)
        self.rb_manual = wx.RadioButton(
            panel, label="Adicionar Contatos Manualmente", style=wx.RB_GROUP
        )
        self.rb_manual.SetToolTip("Selecione para adicionar contatos manualmente.")
        self.rb_list_numbers = wx.RadioButton(panel, label="Usar Lista de Números (.txt/.xlsx)")
        self.rb_list_numbers.SetToolTip("Selecione para importar uma lista de números de telefone.")
        self.rb_list_groups = wx.RadioButton(panel, label="Usar Nomes de Grupos (.txt/.xlsx)")
        self.rb_list_groups.SetToolTip(
            "Selecione para importar uma lista de nomes de grupos do WhatsApp."
        )
        source_sizer.Add(self.rb_manual, 0, wx.ALL, 5)
        source_sizer.Add(self.rb_list_numbers, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        source_sizer.Add(self.rb_list_groups, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        sizer.Add(source_sizer, pos=(0, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL, border=5)

        # Painel de Lista de Arquivo
        self.list_panel = wx.Panel(panel)
        list_box = wx.StaticBox(self.list_panel, label="Carregar de Arquivo")
        list_sizer = wx.StaticBoxSizer(list_box, wx.HORIZONTAL)
        self.contact_list_path = wx.TextCtrl(self.list_panel, style=wx.TE_READONLY)
        self.contact_list_path.SetToolTip("Caminho do arquivo de contatos ou grupos selecionado.")
        self.browse_contacts_btn = wx.Button(self.list_panel, label="Selecionar Lista...")
        self.browse_contacts_btn.SetToolTip("Escolher arquivo de contatos ou grupos (Ctrl+B)")
        list_sizer.Add(self.contact_list_path, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        list_sizer.Add(self.browse_contacts_btn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.list_panel.SetSizerAndFit(list_sizer)
        sizer.Add(self.list_panel, pos=(1, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL, border=5)

        # Painel de Contatos Manuais
        self.manual_panel = wx.Panel(panel)
        manual_box = wx.StaticBox(self.manual_panel, label="Contatos Manuais")
        manual_sizer = wx.StaticBoxSizer(manual_box, wx.VERTICAL)

        input_sizer = wx.FlexGridSizer(2, 2, 10, 10)
        input_sizer.AddGrowableCol(1, 1)
        nome_label = wx.StaticText(self.manual_panel, label="Nome:")
        nome_label.SetToolTip("Nome do contato (opcional, para personalização de mensagem)")
        input_sizer.Add(nome_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.manual_name = wx.TextCtrl(self.manual_panel, name="Nome")
        self.manual_name.SetHint("Ex.: João Silva (Opcional, para usar @Nome)")
        self.manual_name.SetToolTip("Digite o nome do contato (opcional)")
        input_sizer.Add(self.manual_name, 1, wx.EXPAND)
        numero_label = wx.StaticText(self.manual_panel, label="Número:")
        numero_label.SetToolTip("Número do contato no formato internacional. Ex: 5511987654321")
        input_sizer.Add(numero_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        self.manual_number = wx.TextCtrl(self.manual_panel, name="Numero")
        self.manual_number.SetHint("Ex.: 5511987654321")
        self.manual_number.SetToolTip("Digite o número do contato (obrigatório)")
        input_sizer.Add(self.manual_number, 1, wx.EXPAND)
        manual_sizer.Add(input_sizer, 0, wx.EXPAND | wx.ALL, 10)

        self.add_contact_btn = wx.Button(self.manual_panel, label="Adicionar à Lista")
        self.add_contact_btn.SetToolTip(
            "Adicionar o contato preenchido à lista abaixo (Ctrl+Enter)"
        )
        manual_sizer.Add(self.add_contact_btn, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 10)

        self.manual_contact_list = wx.ListCtrl(
            self.manual_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        self.manual_contact_list.InsertColumn(0, "Nome", width=200)
        self.manual_contact_list.InsertColumn(1, "Número", width=150)
        self.manual_contact_list.SetToolTip("Lista de contatos adicionados manualmente.")
        manual_sizer.Add(self.manual_contact_list, 1, wx.EXPAND | wx.ALL, 10)

        self.remove_contact_btn = wx.Button(self.manual_panel, label="Remover Selecionado")
        self.remove_contact_btn.SetToolTip("Remover o contato selecionado da lista (Delete)")
        manual_sizer.Add(self.remove_contact_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.manual_panel.SetSizerAndFit(manual_sizer)
        sizer.Add(
            self.manual_panel,
            pos=(2, 0),
            span=(1, 2),
            flag=wx.EXPAND | wx.ALL,
            border=5,
        )

        sizer.AddGrowableRow(2)
        sizer.AddGrowableCol(0)
        panel.SetSizer(sizer)

        self.manual_panel.Hide()
        self.rb_list_numbers.SetValue(True)

        return panel

    def _create_control_panel(self: "MainFrame", parent: wx.Panel) -> wx.BoxSizer:
        """Cria o painel de controle com botões de ação."""
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        delay_label = wx.StaticText(parent, label="Pausa entre envios:")
        sizer.Add(delay_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.delay_input = wx.SpinCtrl(parent, value="2", min=1, max=120, size=wx.Size(70, -1))
        self.delay_input.SetToolTip("Intervalo em segundos entre cada mensagem enviada (1 a 120).")
        sizer.Add(self.delay_input, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sizer.Add(wx.StaticText(parent, label="segundos"), 0, wx.ALIGN_CENTER_VERTICAL)

        sizer.AddStretchSpacer()

        self.pause_campaign_btn = wx.Button(parent, label="Pausar Campanha")
        self.pause_campaign_btn.SetToolTip("Pausar temporariamente a campanha em execução.")
        self.stop_campaign_btn = wx.Button(parent, label="Parar Campanha")
        self.stop_campaign_btn.SetToolTip("Interromper totalmente a campanha atual.")
        self.start_campaign_btn = wx.Button(parent, label="▶ Iniciar Campanha")
        self.start_campaign_btn.SetFont(
            wx.Font(
                10,
                wx.FONTFAMILY_DEFAULT,
                wx.FONTSTYLE_NORMAL,
                wx.FONTWEIGHT_BOLD,
            )
        )
        self.start_campaign_btn.SetBackgroundColour(wx.Colour(THEME_COLORS["primary"]))
        self.start_campaign_btn.SetForegroundColour(wx.Colour("white"))
        self.start_campaign_btn.SetToolTip("Iniciar o envio da campanha configurada.")

        sizer.Add(self.pause_campaign_btn, 0, wx.ALL, 5)
        sizer.Add(self.stop_campaign_btn, 0, wx.ALL, 5)
        sizer.Add(self.start_campaign_btn, 0, wx.ALL, 5)
        return sizer

    def _create_menu_bar(self: "MainFrame") -> None:
        """Cria a barra de menus da aplicação."""
        menu_bar = wx.MenuBar()

        # Menu Arquivo
        file_menu = wx.Menu()
        news_menu = file_menu.Append(wx.ID_ANY, "&Novidades do Programa\tCtrl+n")
        news_menu.SetHelp("Veja as novidades e atualizações do sistema (Ctrl+N)")
        tips_menu = file_menu.Append(wx.ID_ANY, "&Dicas de Uso\tCtrl+d")
        tips_menu.SetHelp("Acesse dicas rápidas de uso e atalhos (Ctrl+D)")
        file_menu.AppendSeparator()
        menu_minimize = file_menu.Append(wx.ID_ANY, "&Minimizar para Bandeja\tCtrl+M")
        menu_minimize.SetHelp("Minimiza o programa para a bandeja do sistema")
        file_menu.AppendSeparator()
        menu_exit = file_menu.Append(wx.ID_EXIT, "&Fechar Aplicativo\tCtrl+Q")
        menu_exit.SetHelp("Encerra o Zap Fácil com segurança")
        menu_bar.Append(file_menu, "&Arquivo")
        self.Bind(wx.EVT_MENU, self._on_show_news_dialog, news_menu)
        self.Bind(wx.EVT_MENU, self._on_show_tips_dialog, tips_menu)
        self.Bind(wx.EVT_MENU, self._on_minimize_to_tray_menu, menu_minimize)
        self.Bind(wx.EVT_MENU, self._on_request_close, menu_exit)

        # Menu Ferramentas
        tools_menu = wx.Menu()
        menu_templates = tools_menu.Append(wx.ID_ANY, "&Gerenciar Modelos...\tCtrl+T")
        menu_templates.SetHelp("Crie, edite e gerencie modelos de mensagem e anexo")
        menu_schedules = tools_menu.Append(wx.ID_ANY, "&Agendar Campanhas...\tCtrl+A")
        menu_schedules.SetHelp("Programe envios automáticos para datas e horários específicos")
        menu_reports = tools_menu.Append(wx.ID_ANY, "Visualizar &Relatórios...\tCtrl+R")
        menu_reports.SetHelp("Acesse o histórico de envios e exporte relatórios")
        menu_bar.Append(tools_menu, "&Ferramentas")
        self.Bind(wx.EVT_MENU, self._on_show_templates_dialog, menu_templates)
        self.Bind(wx.EVT_MENU, self._on_show_scheduler_dialog, menu_schedules)
        self.Bind(wx.EVT_MENU, self._on_show_reports_dialog, menu_reports)

        settings_menu = wx.Menu()
        menu_open_settings = settings_menu.Append(wx.ID_ANY, "&Abrir Configurações...\tCtrl+G")
        menu_open_settings.SetHelp("Ajuste preferências, temas e integrações do sistema")
        menu_bar.Append(settings_menu, "&Configurações")
        self.Bind(wx.EVT_MENU, self._on_show_settings_dialog, menu_open_settings)

        self.SetMenuBar(menu_bar)

    def _bind_ui_events(self: "MainFrame") -> None:
        """Associa eventos da interface aos métodos da classe e define atalhos globais."""
        self.rb_manual.Bind(wx.EVT_RADIOBUTTON, self._on_source_type_change)
        self.rb_list_numbers.Bind(wx.EVT_RADIOBUTTON, self._on_source_type_change)
        self.rb_list_groups.Bind(wx.EVT_RADIOBUTTON, self._on_source_type_change)
        self.browse_contacts_btn.Bind(wx.EVT_BUTTON, self._on_browse_contacts)
        self.add_contact_btn.Bind(wx.EVT_BUTTON, self._on_add_manual_contact)
        self.remove_contact_btn.Bind(wx.EVT_BUTTON, self._on_remove_manual_contact)
        self.start_campaign_btn.Bind(wx.EVT_BUTTON, self._on_start_campaign)
        self.pause_campaign_btn.Bind(wx.EVT_BUTTON, self._on_pause_campaign)
        self.stop_campaign_btn.Bind(wx.EVT_BUTTON, self._on_stop_campaign)
        self.content_panel.use_template_btn.Bind(wx.EVT_BUTTON, self._on_use_template)

        self.Bind(wx.EVT_CLOSE, self._on_request_close)
        self.Bind(wx.EVT_ICONIZE, self._on_minimize_to_tray)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_down)

        # Atalhos globais para novidades (Ctrl+N) e dicas (Ctrl+D)
        # IDs para atalhos
        self._id_show_news = wx.NewIdRef()
        self._id_show_tips = wx.NewIdRef()
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord("N"), self._id_show_news),
            (wx.ACCEL_CTRL, ord("D"), self._id_show_tips),
        ])
        self.SetAcceleratorTable(accel_tbl)
        self.Bind(wx.EVT_MENU, self._on_show_news_dialog, id=self._id_show_news)
        self.Bind(wx.EVT_MENU, self._on_show_tips_dialog, id=self._id_show_tips)

        self.Bind(EVT_LOG, self._on_log_event_ui)
        self.Bind(EVT_STATUS_UPDATE, self._on_status_update_event_ui)
        self.Bind(EVT_PROGRESS_UPDATE, self._on_progress_update_event_ui)
        self.Bind(EVT_CONNECTION_STATUS, self._on_connection_status_event_ui)
        self.Bind(EVT_CAMPAIGN_STATUS, self._on_campaign_status_event_ui)

    def _subscribe_to_bot_events(self: "MainFrame") -> None:
        """
        Assina eventos do core para atualização da UI,
        garantindo robustez e logging de integração.
        """

        def safe_callafter_postevent(event_factory, *args, **kwargs):
            try:
                wx.CallAfter(wx.PostEvent, self, event_factory(*args, **kwargs))
            except Exception as exc:
                tb = traceback.format_exc()
                self._log_message(
                    f"[ERRO INTEGRAÇÃO UI-CORE] {event_factory.__name__}: {exc}\n{tb}",
                    THEME_COLORS["log_warning"],
                )
                logging.error(f"[ERRO INTEGRAÇÃO UI-CORE] {event_factory.__name__}: {exc}\n{tb}")

        # Garante que não há duplicidade de subscription
        self.bot_service.subscribe(
            "log",
            lambda msg, color: safe_callafter_postevent(LogEvent, message=msg, color_hex=color),
        )
        self.bot_service.subscribe(
            "status_update",
            lambda text: safe_callafter_postevent(StatusUpdateEvent, text=text),
        )
        self.bot_service.subscribe(
            "progress_update",
            lambda val, max_val, msg: safe_callafter_postevent(
                ProgressUpdateEvent, value=val, max_value=max_val, message=msg
            ),
        )
        self.bot_service.subscribe(
            "connection_status",
            lambda status: safe_callafter_postevent(ConnectionStatusEvent, status=status),
        )
        self.bot_service.subscribe(
            "campaign_status",
            lambda status: safe_callafter_postevent(CampaignStatusEvent, status=status),
        )
        self.bot_service.subscribe(
            "audio_state",
            lambda state, duration=0.0: safe_callafter_postevent(
                AudioStateEvent, state=state, duration=duration
            ),
        )

    # --- Manipuladores de Eventos do Bot (Notificações) ---

    def _on_key_down(self: "MainFrame", event: wx.Event) -> None:
        """Manipula atalhos de teclado, seguindo boas práticas e evitando conflitos."""
        # Só processa atalhos se for KeyEvent
        if isinstance(event, wx.KeyEvent):
            keycode: int = event.GetKeyCode()
            ctrl: bool = event.ControlDown()
            shift: bool = event.ShiftDown()

            # Atalhos para campanha (sem conflito com existentes)
            if ctrl and shift:
                if keycode == ord("I"):
                    wx.PostEvent(
                        self,
                        wx.CommandEvent(
                            wx.EVT_BUTTON.typeId,
                            self.start_campaign_btn.GetId(),
                        ),
                    )
                    return
                if keycode == ord("P"):
                    wx.PostEvent(
                        self,
                        wx.CommandEvent(
                            wx.EVT_BUTTON.typeId,
                            self.pause_campaign_btn.GetId(),
                        ),
                    )
                    return
                if keycode == ord("S"):
                    wx.PostEvent(
                        self,
                        wx.CommandEvent(
                            wx.EVT_BUTTON.typeId,
                            self.stop_campaign_btn.GetId(),
                        ),
                    )
                    return
            # Ctrl+Enter para iniciar campanha
            if ctrl and keycode == wx.WXK_RETURN:
                wx.PostEvent(
                    self,
                    wx.CommandEvent(
                        wx.EVT_BUTTON.typeId,
                        self.start_campaign_btn.GetId(),
                    ),
                )
                return

            # Atalhos já existentes e atalhos de formulário
            if (
                keycode == wx.WXK_DELETE
                and self.rb_manual.GetValue()
                and self.manual_contact_list.HasFocus()
            ):
                wx.PostEvent(
                    self,
                    wx.CommandEvent(
                        wx.EVT_BUTTON.typeId,
                        self.remove_contact_btn.GetId(),
                    ),
                )
                return
            if keycode == wx.WXK_RETURN and self.FindFocus() in (
                self.manual_name,
                self.manual_number,
            ):
                wx.PostEvent(
                    self,
                    wx.CommandEvent(
                        wx.EVT_BUTTON.typeId,
                        self.add_contact_btn.GetId(),
                    ),
                )
                return

        event.Skip()

    # --- Manipuladores de Eventos da UI (recebidos do BotService) ---
    def _on_log_event_ui(self: "MainFrame", event: LogEvent) -> None:
        try:
            self._log_message(event.message, event.color_hex)
        except Exception as exc:
            tb = traceback.format_exc()
            logging.error(f"Falha ao processar evento de log: {exc}\n{tb}")

    def _on_status_update_event_ui(self: "MainFrame", event: StatusUpdateEvent) -> None:
        try:
            self.status_bar.SetStatusText(event.text, 0)
        except Exception as exc:
            tb = traceback.format_exc()
            logging.error(f"Falha ao processar evento de status: {exc}\n{tb}")

    def _on_progress_update_event_ui(self: "MainFrame", event: ProgressUpdateEvent) -> None:
        try:
            if event.max_value > 0:
                if not self.progress_bar.IsShown():
                    self.progress_bar.Show()
                    self.Layout()
                self.progress_bar.SetRange(event.max_value)
                self.progress_bar.SetValue(event.value)
                if event.message:
                    self.status_bar.SetStatusText(event.message, 0)
            else:
                if self.progress_bar.IsShown():
                    self.progress_bar.Hide()
                    self.Layout()
        except Exception as exc:
            tb = traceback.format_exc()
            logging.error(f"Falha ao processar evento de progresso: {exc}\n{tb}")

    def _on_connection_status_event_ui(self: "MainFrame", event: ConnectionStatusEvent) -> None:
        try:
            status_map: dict[ConnectionState, tuple[str, bool]] = {
                ConnectionState.CONNECTING: ("Conectando ao WhatsApp...", True),
                ConnectionState.NEEDS_QR_SCAN: ("Aguardando leitura do QR Code...", True),
                ConnectionState.CONNECTED: ("Conectado", False),
                ConnectionState.FAILED: ("Falha na conexão", False),
                ConnectionState.DISCONNECTED: ("Desconectado", False),
            }
            text, is_running = status_map.get(event.status, ("Status desconhecido", False))
            self.status_bar.SetStatusText(text, 0)
            if is_running:
                self.activity_indicator.Start()
            else:
                self.activity_indicator.Stop()
            self._update_button_states()
        except Exception as exc:
            tb = traceback.format_exc()
            logging.error(f"Falha ao processar evento de conexão: {exc}\n{tb}")

    def _on_campaign_status_event_ui(self: "MainFrame", event: CampaignStatusEvent) -> None:
        try:
            if event.status == CampaignState.RUNNING:
                self.status_bar.SetStatusText("Campanha em execução...", 1)
                self.pause_campaign_btn.SetLabel("Pausar Campanha")
                self.progress_bar.SetValue(0)
                if not self.progress_bar.IsShown():
                    self.progress_bar.Show()
            elif event.status == CampaignState.PAUSED:
                self.status_bar.SetStatusText("Campanha pausada", 1)
                self.pause_campaign_btn.SetLabel("Retomar Campanha")
            elif event.status in [
                CampaignState.IDLE,
                CampaignState.FINISHED,
                CampaignState.STOPPED,
            ]:
                self.status_bar.SetStatusText("Ocioso", 1)
                self.pause_campaign_btn.SetLabel("Pausar Campanha")
                if self.progress_bar.IsShown():
                    self.progress_bar.Hide()
            self.Layout()
            self._update_button_states()
        except Exception as exc:
            tb = traceback.format_exc()
            logging.error(f"Falha ao processar evento de campanha: {exc}\n{tb}")

    # --- Manipuladores de Ações do Usuário (Cliques, etc.) ---
    def _get_manual_contacts(self: "MainFrame") -> list[dict[str, str]]:
        """Extrai e formata os contatos da lista manual da UI."""
        contacts: list[dict[str, str]] = []
        for i in range(self.manual_contact_list.GetItemCount()):
            nome: str = self.manual_contact_list.GetItem(i, 0).GetText().strip()
            numero: str = self.manual_contact_list.GetItem(i, 1).GetText().strip()
            if not numero:
                continue
            contacts.append({
                "Nome": nome if nome else numero,
                "identifier": numero,
            })
        return contacts

    def _on_start_campaign(self: "MainFrame", event: wx.CommandEvent) -> None:
        """Valida e inicia a campanha, garantindo integração robusta UI-core."""

        try:
            # Compatível com ContentPanel: get_value()
            if hasattr(self.content_panel, "get_value"):
                content_cfg = self.content_panel.get_value()
            else:
                raise AttributeError("ContentPanel não possui método get_value().")
        except Exception as exc:
            wx.MessageBox(
                f"Erro ao obter dados do painel de conteúdo: {exc}", "Erro", wx.OK | wx.ICON_ERROR
            )
            self._log_message(
                f"[ERRO] Falha ao obter dados do ContentPanel: {exc}", THEME_COLORS["log_warning"]
            )
            return

        if (
            not content_cfg.get("message", "").strip()
            and not content_cfg.get("attachment", "").strip()
        ):
            wx.MessageBox(
                "A campanha deve ter ao menos uma mensagem ou um anexo.",
                "Erro",
                wx.OK | wx.ICON_ERROR,
            )
            return

        campaign_config = dict(content_cfg)
        campaign_config["delay"] = self.delay_input.GetValue()

        if self.rb_manual.GetValue():
            contacts = self._get_manual_contacts()
            if not contacts:
                wx.MessageBox(
                    "Adicione contatos válidos na lista manual antes de iniciar.",
                    "Erro",
                    wx.OK | wx.ICON_ERROR,
                )
                return
            campaign_config["source_type"] = "MANUAL_LIST"
            campaign_config["contact_source"] = contacts
        else:
            path = self.contact_list_path.GetValue()
            if not path or not Path(path).exists():
                wx.MessageBox(
                    "Selecione um arquivo de contatos válido.",
                    "Erro",
                    wx.OK | wx.ICON_ERROR,
                )
                return
            campaign_config["source_type"] = (
                "GROUP_LIST" if self.rb_list_groups.GetValue() else "LIST"
            )
            campaign_config["contact_source"] = path

        try:
            self.bot_service.start_campaign(campaign_config)
        except Exception as exc:
            wx.MessageBox(f"Erro ao iniciar campanha: {exc}", "Erro", wx.OK | wx.ICON_ERROR)
            logging.error(f"Falha ao iniciar campanha: {exc}")
        # Foca no botão de pausar após iniciar
        self.pause_campaign_btn.SetFocus()

    def _on_pause_campaign(self: "MainFrame", event: wx.CommandEvent) -> None:
        self.bot_service.toggle_pause_campaign()
        # Mantém o foco no botão de pausar/retomar
        self.pause_campaign_btn.SetFocus()

    def _on_stop_campaign(self: "MainFrame", event: wx.CommandEvent) -> None:
        dialog = wx.MessageDialog(
            parent=self,
            message=(
                "Tem certeza que deseja parar a campanha atual?\nEsta ação não pode ser desfeita."
            ),
            caption="Confirmar Interrupção",
            style=wx.YES_NO | wx.ICON_WARNING | wx.NO_DEFAULT,
        )

        dialog.SetYesNoLabels("Sim", "Não")

        result = dialog.ShowModal()

        dialog.Destroy()

        if result == wx.ID_YES:
            self.bot_service.stop_campaign()

    def _on_source_type_change(self: "MainFrame", event: wx.CommandEvent) -> None:
        is_manual = self.rb_manual.GetValue()
        self.manual_panel.Show(is_manual)
        self.list_panel.Show(not is_manual)

        if is_manual:
            # Limpa o caminho do arquivo para evitar confusão
            self.contact_list_path.Clear()
            self.manual_name.SetFocus()

        self.Layout()
        self._update_button_states()

    def _on_browse_contacts(self: "MainFrame", event: wx.CommandEvent) -> None:
        path = show_file_dialog(self, "Selecionar Lista de Contatos/Grupos", WILDCARD_CONTACTS)
        if path:
            self.contact_list_path.SetValue(path)
        self._update_button_states()

    def _on_add_manual_contact(self: "MainFrame", event: wx.CommandEvent) -> None:
        name = self.manual_name.GetValue().strip()
        number = self.manual_number.GetValue().strip()
        if not number:
            wx.MessageBox("O campo 'Número' é obrigatório.", "Erro", wx.OK | wx.ICON_ERROR)
            self.manual_number.SetFocus()
            return

        index = self.manual_contact_list.InsertItem(
            self.manual_contact_list.GetItemCount(), name or " "
        )
        self.manual_contact_list.SetItem(index, 1, number)
        self.manual_name.Clear()
        self.manual_number.Clear()
        self.manual_name.SetFocus()
        self._update_button_states()

    def _on_remove_manual_contact(self: "MainFrame", event: wx.CommandEvent) -> None:
        idx = self.manual_contact_list.GetFirstSelected()
        if idx != -1:
            self.manual_contact_list.DeleteItem(idx)
        self._update_button_states()

    # --- Handlers de Menus e Diálogos ---
    def _on_show_news_dialog(self: "MainFrame", event: wx.CommandEvent) -> None:
        with NewsDialog(self) as dialog:
            dialog.ShowModal()

    def _on_show_tips_dialog(self: "MainFrame", event: wx.CommandEvent) -> None:
        with TipsDialog(self) as dialog:
            dialog.ShowModal()

    def _on_show_templates_dialog(self: "MainFrame", event: wx.CommandEvent) -> None:
        with TemplatesDialog(self, self.bot_service) as dialog:
            dialog.ShowModal()

    def _on_show_reports_dialog(self: "MainFrame", event: wx.CommandEvent) -> None:
        with ReportsDialog(self, self.bot_service) as dialog:
            dialog.ShowModal()

    def _on_show_scheduler_dialog(self: "MainFrame", event: wx.CommandEvent) -> None:
        with CampaignSchedulerDialog(self, self.bot_service) as dialog:
            dialog.ShowModal()

    def _on_show_settings_dialog(self: "MainFrame", event: wx.CommandEvent) -> None:
        with SettingsDialog(self, self.bot_service, self.config) as dialog:
            dialog.ShowModal()

    def _on_use_template(self: "MainFrame", event: wx.CommandEvent) -> None:
        try:
            templates = self.bot_service.get_templates()
        except Exception as exc:
            wx.MessageBox(f"Erro ao buscar modelos: {exc}", "Erro", wx.OK | wx.ICON_ERROR)

            logging.error(f"Falha ao buscar modelos: {exc}")
            return
        if not templates:
            wx.MessageBox(
                "Nenhum modelo foi criado. Vá em Ferramentas > Gerenciar Modelos.",
                "Aviso",
                wx.OK | wx.ICON_INFORMATION,
            )
            return
        with TemplatePickerDialog(self, templates) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                template = dialog.GetSelectedTemplate()
                if template:
                    self._log_message(
                        f"Modelo '{template['name']}' carregado.",
                        THEME_COLORS["accent_purple"],
                    )
                    try:
                        # Compatível com ContentPanel: set_value()
                        if hasattr(self.content_panel, "set_value"):
                            self.content_panel.set_value(template)
                        else:
                            raise AttributeError("ContentPanel não possui método set_value().")
                    except Exception as exc:
                        wx.MessageBox(
                            f"Erro ao aplicar modelo: {exc}", "Erro", wx.OK | wx.ICON_ERROR
                        )
                        logging.error(f"Falha ao aplicar modelo: {exc}")

    # --- Handlers de Janela e Encerramento ---
    def _on_minimize_to_tray(self: "MainFrame", event: wx.IconizeEvent) -> None:
        # Apenas minimiza normalmente, não esconde a janela automaticamente
        event.Skip()

    def _on_minimize_to_tray_menu(self: "MainFrame", event: wx.CommandEvent) -> None:
        self.Hide()

    def _on_restore(self: "MainFrame", event: wx.Event | None) -> None:
        if not self.IsShown():
            self.Show()
        self.Iconize(False)
        self.Raise()

    def _on_request_close(self: "MainFrame", event: wx.Event | None) -> None:
        if (
            wx.MessageDialog(
                self,
                "Tem certeza que deseja fechar o Zap Fácil?",
                "Confirmar Saída",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
            ).ShowModal()
            == wx.ID_YES
        ):
            self._on_exit_app()
        elif event and isinstance(event, wx.CloseEvent):
            event.Veto()

    def _on_exit_app(self: "MainFrame") -> None:
        if self.is_shutting_down:
            return
        self.is_shutting_down = True

        if self.task_bar_icon:
            self.task_bar_icon.Destroy()
            self.task_bar_icon = None

        self._log_message("Encerrando...", THEME_COLORS["log_warning"])
        self.bot_service.shutdown()
        self.Destroy()

    def _log_message(self: "MainFrame", message: str, color_hex: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.SetInsertionPointEnd()
        self.log.SetDefaultStyle(wx.TextAttr(wx.Colour(color_hex)))
        self.log.AppendText(f"[{timestamp}] {message}\n")

    def _update_button_states(self: "MainFrame") -> None:
        """
        Atualiza o estado de todos os botões de ação com base no estado do app,
        mantendo o foco do botão ativo.
        """
        try:
            # Salva o botão atualmente focado
            focused_widget = wx.Window.FindFocus()

            conn_ok = self.bot_service.connection_state == ConnectionState.CONNECTED
            camp_idle = self.bot_service.campaign_state in [
                CampaignState.IDLE,
                CampaignState.FINISHED,
                CampaignState.STOPPED,
            ]
            camp_running = self.bot_service.campaign_state in [
                CampaignState.RUNNING,
                CampaignState.PAUSED,
            ]

            can_start = False
            if conn_ok and camp_idle:
                if self.rb_manual.GetValue():
                    can_start = self.manual_contact_list.GetItemCount() > 0
                else:
                    path_str = self.contact_list_path.GetValue()
                    can_start = bool(path_str) and Path(path_str).exists()

            self.start_campaign_btn.Enable(can_start)
            self.pause_campaign_btn.Enable(camp_running)
            self.stop_campaign_btn.Enable(camp_running)

            # Impede alterações de configuração durante uma campanha
            for widget in [
                self.rb_manual,
                self.rb_list_numbers,
                self.rb_list_groups,
                self.browse_contacts_btn,
                self.add_contact_btn,
                self.remove_contact_btn,
                self.content_panel,
                self.delay_input,
            ]:
                widget.Enable(camp_idle)

            # Restaura o foco se o widget ainda existir e estiver habilitado
            if focused_widget and focused_widget.IsEnabled():
                focused_widget.SetFocus()
        except Exception as exc:
            logging.error(f"Falha ao atualizar botões: {exc}")
