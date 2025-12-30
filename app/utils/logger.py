"""Singleton logger implementation with colored console output using ANSI codes."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.utils.settings import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[31m\033[47m",  # Red on white background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        # Get the color for this log level
        log_color = self.COLORS.get(record.levelname, "")
        
        # Add color to levelname
        if log_color:
            record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset color at the end
        return formatted


class Logger:
    """Singleton logger that logs to both file and console with colors."""

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
        """Set up the logger with file and colored console handlers."""
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

        # File handler (no colors in file)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        # Colored console handler
        console_handler = logging.StreamHandler(sys.stdout)
        try:
            log_level = settings.LOG_LEVEL.upper()
        except Exception:
            # Fallback to INFO if SettingsManager fails
            log_level = "INFO"
        console_handler.setLevel(getattr(logging, log_level, logging.INFO))

        # Color formatter
        console_formatter = ColoredFormatter(
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

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.get_logger().debug(message)

    def info(self, message: str) -> None:
        """Log info message."""
        self.get_logger().info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.get_logger().warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.get_logger().error(message)

    def critical(self, message: str) -> None:
        """Log critical message."""
        self.get_logger().critical(message)

    def success(self, message: str) -> None:
        """Log success message (info level with success styling)."""
        self.get_logger().info(f"✓ {message}")


# Create module-level instance
logger_instance = Logger()
logger = logger_instance.get_logger()


def get_logger() -> logging.Logger:
    """Get the singleton logger instance."""
    return logger
