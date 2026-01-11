"""Logging configuration for local development and testing.

This module provides extended logging setup when running modules locally
via main.py or scripts. When running as a Home Assistant integration,
logging is handled by Home Assistant's logging system.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(level: int = logging.DEBUG, log_file: Optional[Path] = None) -> None:
    """Set up extended logging for local development/testing.

    This function configures logging with DEBUG level, console output,
    and optional file logging. It should be called at the start of
    main.py or test scripts.

    Args:
        level: Logging level (default: DEBUG)
        log_file: Optional path to log file (default: logs/logs.log)
    """
    if log_file is None:
        log_file = Path("logs/logs.log")

    # Create logs directory if needed
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure handlers
    handlers = [logging.StreamHandler(sys.stdout), logging.FileHandler(log_file)]

    # Set up formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    for handler in handlers:
        handler.setFormatter(formatter)
        handler.setLevel(level)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = handlers


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.

    This function is kept for backward compatibility but is not required.
    Library modules should use logging.getLogger(__name__) directly.

    Args:
        name: Logger name (typically module name)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
