"""
Configuração centralizada de logging para o Zap Ágil.
O log é utilizado apenas para erros internos e debug, nunca para mensagens ao usuário final.
"""

import logging

from zap_agil.core.constants import LOG_FILE_PATH

logging.basicConfig(
    level=logging.ERROR,  # Apenas erros internos
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding="utf-8"),
        # logging.StreamHandler()  # Descomente para debug em terminal
    ],
)
