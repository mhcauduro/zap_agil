from zap_agil.core import whatsapp_manager


def test_whatsapp_manager_has_class():
    """Verifica se a classe WhatsAppManager existe no módulo."""
    assert hasattr(whatsapp_manager, "WhatsAppManager")
