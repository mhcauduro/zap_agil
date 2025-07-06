from zap_agil.core import schedule_manager


def test_schedule_manager_module_exists():
    """Verifica se o módulo schedule_manager pode ser importado."""
    assert schedule_manager is not None
