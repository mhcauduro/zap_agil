from zap_agil.ui import ui_utils


def test_ui_utils_has_methods():
    """Verifica se a função show_file_dialog existe no módulo ui_utils."""
    assert hasattr(ui_utils, "show_file_dialog")
