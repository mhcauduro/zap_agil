from zap_agil.core import constants


def test_constants_exist():
    assert hasattr(constants, "APP_NAME")
