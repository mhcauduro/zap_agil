"""
Funções utilitárias para a interface do Zap Fácil.
"""

import wx


def show_file_dialog(
    parent: wx.Window, message: str = "Selecionar Arquivo", wildcard: str = "*.*"
) -> str | None:
    """
    Abre um diálogo de seleção de arquivo e retorna o caminho selecionado.

    Args:
        parent (wx.Window): Janela pai do diálogo.
        message (str): Título do diálogo. Padrão: "Selecionar Arquivo".
        wildcard (str): Filtro de tipos de arquivo (ex.: "*.txt;*.xlsx"). Padrão: "*.*".

    Returns:
        Optional[str]: Caminho do arquivo selecionado ou None se cancelado.
    """
    # As verificações de 'message' e 'wildcard' foram removidas por serem redundantes.
    with wx.FileDialog(
        parent, message, wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    ) as file_dialog:
        if file_dialog.ShowModal() == wx.ID_OK:
            return file_dialog.GetPath()
        return None
