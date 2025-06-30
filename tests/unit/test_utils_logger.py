import logging
import os
from src.utils.logger import logger

def test_logger_writes(tmp_path, monkeypatch):
    log_file = tmp_path / "app.log"
    monkeypatch.setenv("LOGFILE", str(log_file))
    # Reconfigure basicConfig to write to our tmp file
    logging.basicConfig(filename=str(log_file), level=logging.DEBUG)
    logger.debug("test message")
    assert log_file.exists()
    content = log_file.read_text()
    assert "test message" in content
