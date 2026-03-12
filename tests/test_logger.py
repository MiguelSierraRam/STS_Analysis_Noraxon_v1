import os
import logging
import pytest
from src.logger import LoggerManager, get_logger
from src.config import get_config


def test_logger_creation(tmp_path):
    log_dir = tmp_path / "logs"
    LoggerManager.configure(log_dir=str(log_dir))
    logger = get_logger("tests.logger")
    assert isinstance(logger, logging.Logger)
    logger.info("Test message")
    log_file = log_dir / "sts_analysis.log"
    assert log_file.exists()
    content = log_file.read_text()
    assert "Test message" in content


def test_logger_rotation(tmp_path):
    # ensure handler setup doesn't crash and optionally rotates
    log_dir = tmp_path / "logs2"
    # temporarily override config file_size_mb very small
    config = get_config()
    config.set('logging.file_size_mb', 0.0001)
    config.set('logging.backup_count', 1)
    # force reconfigure even if previously configured
    LoggerManager._configured = False
    LoggerManager.configure(log_dir=str(log_dir))
    logger = get_logger("tests.logger2")
    for i in range(200):
        logger.debug("spam")
    files = list(log_dir.glob("sts_analysis.log*"))
    assert len(files) >= 1
