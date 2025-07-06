"""
Ponto de entrada principal para iniciar o app.
Inicializa o ambiente e a interface.
"""

import wx
import sys
import os

# Adiciona o diretório do script ao path para garantir que o pacote 'zap_agil' seja encontrado
# Isso torna o script executável de qualquer lugar.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from zap_agil.utils.config_manager import ConfigManager
from zap_agil.ui.disclaimer_ui import DisclaimerDialog
from zap_agil.ui.main_frame import MainFrame


def main():
    app = wx.App(False)
    config = ConfigManager()

    # Verifica se o termo de responsabilidade foi aceito
    disclaimer_accepted = (
        config.get_setting("General", "disclaimer_accepted", "false").lower() == "true"
    )

    if not disclaimer_accepted:
        dialog = DisclaimerDialog(None)
        result = dialog.ShowModal()
        dialog.Destroy()

        if result == wx.ID_OK:
            config.save_setting("General", "disclaimer_accepted", "True")
        else:
            return

    frame = MainFrame()
    # O frame.Show() já é chamado dentro do __init__ da MainFrame

    # Inicia o loop de eventos da interface
    app.MainLoop()


if __name__ == "__main__":
    main()
