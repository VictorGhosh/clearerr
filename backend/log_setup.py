import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(config):
    log_path = Path(config._LOG_PATH)
    if not log_path.parent.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)

    max_bytes = config.LOG_SIZE_MB * 1024 * 1024
    log_level = getattr(logging, config.LOG_LEVEL)
    formatter = logging.Formatter("%(levelname)s %(asctime)s: %(message)s", datefmt="%y-%m-%d %H:%M:%S")

    # main log
    file_handler = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=3)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    # removals log
    removals_logger = logging.getLogger("removals")
    removals_handler = RotatingFileHandler(log_path.parent / "removals.log", maxBytes=max_bytes, backupCount=3)
    removals_handler.setFormatter(formatter)
    removals_logger.addHandler(removals_handler)
    removals_logger.propagate = False

    # exemptions log
    exemptions_logger = logging.getLogger("exemptions")
    exemptions_handler = RotatingFileHandler(log_path.parent / "exemptions.log", maxBytes=max_bytes, backupCount=3)
    exemptions_handler.setFormatter(formatter)
    exemptions_logger.addHandler(exemptions_handler)
    exemptions_logger.propagate = False