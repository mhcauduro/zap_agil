import os
import tempfile
from pathlib import Path

from zap_agil.utils import json_utils


def test_save_and_load_json_file():
    data = {"foo": "bar", "num": 42}
    with tempfile.NamedTemporaryFile(delete=False, mode="w+", encoding="utf-8") as tmp:
        tmp.close()
        json_utils.save_json_file(Path(tmp.name), data)
        result = json_utils.load_json_file(Path(tmp.name))
        assert result == data
        os.remove(tmp.name)


def test_load_json_file_not_found():
    assert json_utils.load_json_file(Path("nonexistent_file.json")) is None
