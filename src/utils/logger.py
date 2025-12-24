"""Singleton logger implementation."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class Logger:
    """Singleton logger that logs to both file and console."""

    _instance: Optional["Logger"] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls) -> "Logger":
        """Create or return existing logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize logger if not already initialized."""
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self) -> None:
        """Set up the logger with file and console handlers."""
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"{timestamp}_log.log"

        # Create logger
        self._logger = logging.getLogger("langgraph_agentic_base")
        self._logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        self._logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        console_handler.setLevel(getattr(logging, log_level, logging.INFO))
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

        self._logger.info(f"Logger initialized. Log file: {log_file}")

    def get_logger(self) -> logging.Logger:
        """Get the logger instance."""
        if self._logger is None:
            self._setup_logger()
        return self._logger


def get_logger() -> logging.Logger:
    """Get the singleton logger instance."""
    return Logger().get_logger()

