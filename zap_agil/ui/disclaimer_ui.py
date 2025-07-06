"""
Define o diálogo de exibição do aviso de responsabilidade do Zap Fácil.
"""

import wx

from zap_agil.core.constants import APP_NAME, COMPANY_NAME


class DisclaimerDialog(wx.Dialog):
    """Diálogo para exibir e aceitar os termos de responsabilidade do aplicativo."""

    def __init__(self, parent: wx.Window):
        super().__init__(
            parent,
            title=f"Aviso de Responsabilidade - {APP_NAME}",
            size=wx.Size(600, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._init_ui()
        self._bind_events()
        self.Center()

    def _init_ui(self) -> None:
        """Inicializa os componentes da interface do diálogo."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Texto do aviso
        disclaimer_text = (
            f"Aviso de Responsabilidade\n\n"
            f"O {APP_NAME} é uma ferramenta de automação para envio de mensagens pelo WhatsApp, "
            f"desenvolvida pela {COMPANY_NAME}. "
            f"O uso desta ferramenta é de total responsabilidade do usuário. "
            f"A {COMPANY_NAME} não se responsabiliza por quaisquer danos, "
            f"perdas ou problemas legais decorrentes do uso inadequado do software, "
            f"incluindo, mas não se limitando a, envio de mensagens não autorizadas, "
            f"spam ou qualquer violação dos termos de serviço do WhatsApp.\n\n"
            f"Certifique-se de usar o {APP_NAME} em conformidade com as leis locais "
            f"e os termos de serviço do WhatsApp. "
            f"Ao marcar a caixa abaixo, você declara que leu, entendeu e concorda "
            f"com estas condições."
        )
        text_ctrl = wx.TextCtrl(
            self,
            value=disclaimer_text,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP,
            size=wx.Size(-1, 250),
        )
        main_sizer.Add(text_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        # Checkbox para aceitação
        self.accept_checkbox = wx.CheckBox(
            self, label="Eu li e aceito os termos de responsabilidade"
        )
        main_sizer.Add(self.accept_checkbox, 0, wx.ALL | wx.CENTER, 10)

        # Botões de ação
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.ok_button = wx.Button(self, wx.ID_OK, label="Continuar")
        self.ok_button.Enable(False)
        cancel_button = wx.Button(self, wx.ID_CANCEL, label="Fechar")

        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(self.ok_button, 0, wx.RIGHT, 10)
        button_sizer.Add(cancel_button, 0)

        main_sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(main_sizer)

    def _bind_events(self) -> None:
        """Associa eventos aos componentes da interface."""
        self.accept_checkbox.Bind(wx.EVT_CHECKBOX, self._on_checkbox_toggle)
        self.ok_button.Bind(wx.EVT_BUTTON, self._on_ok)
        self.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_down)

    def _on_key_down(self, event: wx.KeyEvent) -> None:
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
            return
        event.Skip()

    def _on_checkbox_toggle(self, event: wx.CommandEvent) -> None:
        """Habilita ou desabilita o botão OK com base no estado da checkbox."""
        self.ok_button.Enable(self.accept_checkbox.IsChecked())

    def _on_ok(self, event: wx.CommandEvent) -> None:
        """Fecha o diálogo com resultado OK se os termos forem aceitos."""
        if self.accept_checkbox.IsChecked():
            self.EndModal(wx.ID_OK)
        else:
            wx.MessageBox(
                "Você deve aceitar os termos para continuar.",
                "Aviso",
                wx.OK | wx.ICON_WARNING,
                self,
            )

    def _on_cancel(self, event: wx.CommandEvent) -> None:
        """Fecha o diálogo com resultado Cancel."""
        self.EndModal(wx.ID_CANCEL)
