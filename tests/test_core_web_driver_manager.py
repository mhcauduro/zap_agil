from zap_agil.core import web_driver_manager


def test_web_driver_manager_has_class():
    """Verifica se a classe WebDriverManager existe no módulo."""
    assert hasattr(web_driver_manager, "WebDriverManager")
