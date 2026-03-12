import os
import pytest
from src.config import load_config, get_config, Config


def test_load_default_config():
    config = load_config()
    assert isinstance(config, Config)
    assert config.get('window') == 30
    assert config.get('logging.level') in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')


def test_override_cli():
    config = load_config()
    config.set('window', 99)
    assert config.get('window') == 99


def test_custom_config_file(tmp_path):
    custom = tmp_path / "custom.yaml"
    custom.write_text("window: 42\nlogging:\n  level: 'DEBUG'\n")
    config = load_config(str(custom))
    assert config.get('window') == 42
    assert config.get('logging.level') == 'DEBUG'
