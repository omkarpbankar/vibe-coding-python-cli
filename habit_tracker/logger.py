"""
Logging Configuration Module for Habit Tracker.

Sets up dual-destination logging:
- Persistent file logging to `app.log` with detailed timestamps and module origin.
- Console stream logging with clean formatting.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Global default logger name
DEFAULT_LOGGER_NAME = "habit_tracker"


def setup_logger(
    log_file: str | Path = "app.log",
    level: int = logging.INFO,
    console_output: bool = True,
    console_level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure and return the application logger with both File and Console handlers.

    :param log_file: Path to the log file (e.g., 'app.log').
    :param level: Minimum logging level for file output.
    :param console_output: Whether to attach a console/terminal stream handler.
    :param console_level: Minimum logging level for console output.
    :return: Configured logging.Logger instance.
    """
    logger = logging.getLogger(DEFAULT_LOGGER_NAME)
    logger.setLevel(logging.DEBUG)  # Capture all, let handlers filter

    # Avoid duplicate handlers if setup_logger is invoked multiple times
    if logger.handlers:
        return logger

    # Ensure log file directory exists
    log_path = Path(log_file)
    if not log_path.parent.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. File Handler (writes detailed logs to app.log)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 2. Console Stream Handler
    if console_output:
        console_formatter = logging.Formatter(
            fmt="[%(levelname)s] %(message)s"
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a hierarchical child logger or the default habit tracker logger.
    """
    if name:
        return logging.getLogger(f"{DEFAULT_LOGGER_NAME}.{name}")
    return logging.getLogger(DEFAULT_LOGGER_NAME)
