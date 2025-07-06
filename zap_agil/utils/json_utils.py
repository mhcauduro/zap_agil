"""
Utilitários genéricos para manipulação de arquivos JSON.
"""

import json
from pathlib import Path
from typing import Any

from zap_agil.utils.logging_config import logging


def save_json_file(filepath: Path, data: list[Any] | dict[str, Any]) -> bool:
    """
    Salva dados em um arquivo JSON de forma segura.

    Args:
        filepath (Path): O caminho completo do arquivo a ser salvo.
        data (Union[List, Dict]): Os dados (lista ou dicionário) para salvar.

    Returns:
        bool: True se o arquivo foi salvo com sucesso, False caso contrário.
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except (OSError, TypeError) as e:
        logging.error(f"Erro ao salvar arquivo JSON {filepath.name}: {e}")
        return False


def load_json_file(filepath: Path, default: Any | None = None) -> Any:
    """
    Carrega dados de um arquivo JSON de forma segura.

    Args:
        filepath (Path): O caminho completo do arquivo a ser carregado.
        default (Optional[Any]): Valor a ser retornado se o arquivo não
                                 for encontrado. Padrão é None.

    Returns:
        Any: Os dados carregados, ou o valor `default` se o arquivo não
             existir ou ocorrer um erro.
    """
    if not filepath.exists():
        return default
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
            if not content:
                return default
            return json.loads(content)
    except (OSError, json.JSONDecodeError) as e:
        logging.error(f"Erro ao carregar arquivo JSON {filepath.name}: {e}")
        return default
