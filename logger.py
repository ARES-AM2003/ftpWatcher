"""
Logging configuration for FTP upload system.
Provides structured logging with rotation and multiple handlers.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config import Config


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str, log_file: Optional[str] = None, level: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.

    Args:
        name: Logger name
        log_file: Optional log file path (uses Config.LOG_FILE if not provided)
        level: Optional log level (uses Config.LOG_LEVEL if not provided)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set log level
    log_level = getattr(logging, (level or Config.LOG_LEVEL).upper(), logging.INFO)
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    if log_file or Config.LOG_FILE:
        file_path = Path(log_file or Config.LOG_FILE)

        # Handle absolute paths that may require permissions
        if file_path.is_absolute():
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                # Fallback to local directory if we don't have permissions
                fallback_path = Path.cwd() / file_path.name
                logger.warning(
                    f"Permission denied creating {file_path.parent}. "
                    f"Using fallback: {fallback_path}"
                )
                file_path = fallback_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=Config.LOG_MAX_BYTES,
                backupCount=Config.LOG_BACKUP_COUNT,
            )
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            logger.warning(f"Could not create file handler for {file_path}: {e}")

    return logger


# Create default logger
default_logger = setup_logger("ftp_processor")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return setup_logger(name)
