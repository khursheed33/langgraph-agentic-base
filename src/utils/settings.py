"""Singleton SettingsManager using dynaconf for configuration management."""

import logging
from typing import Optional

from dynaconf import Dynaconf
from dynaconf import Validator

# Use basic logging to avoid circular dependency with logger module
_logger = logging.getLogger(__name__)


class SettingsManager:
    """Singleton settings manager using dynaconf."""

    _instance: Optional["SettingsManager"] = None
    _settings: Optional[Dynaconf] = None

    def __new__(cls) -> "SettingsManager":
        """Create or return existing SettingsManager instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize settings if not already initialized."""
        if self._settings is None:
            self._setup_settings()

    def _setup_settings(self) -> None:
        """Set up dynaconf settings."""
        try:
            self._settings = Dynaconf(
                envvar_prefix=False,
                settings_files=[],
                environments=False,
                load_dotenv=True,
                dotenv_path=".env",
                validators=[
                    Validator("GROQ_API_KEY", must_exist=True),
                    Validator("GROQ_MODEL", default="llama-3.1-70b-versatile"),
                    Validator("NEO4J_URI", default="bolt://localhost:7687"),
                    Validator("NEO4J_USER", default="neo4j"),
                    Validator("NEO4J_PASSWORD", default=""),
                    Validator("LOG_LEVEL", default="INFO"),
                    Validator("MAX_ITERATIONS", default=50, cast=int),
                ],
            )
            _logger.info("SettingsManager initialized successfully")
        except Exception as e:
            _logger.error(f"Failed to initialize SettingsManager: {e}")
            raise

    @property
    def GROQ_API_KEY(self) -> str:
        """Get Groq API key."""
        return self._settings.GROQ_API_KEY

    @property
    def GROQ_MODEL(self) -> str:
        """Get Groq model name."""
        return self._settings.GROQ_MODEL

    @property
    def NEO4J_URI(self) -> str:
        """Get Neo4j URI."""
        return self._settings.NEO4J_URI

    @property
    def NEO4J_USER(self) -> str:
        """Get Neo4j username."""
        return self._settings.NEO4J_USER

    @property
    def NEO4J_PASSWORD(self) -> str:
        """Get Neo4j password."""
        return self._settings.NEO4J_PASSWORD

    @property
    def LOG_LEVEL(self) -> str:
        """Get log level."""
        return self._settings.LOG_LEVEL

    @property
    def MAX_ITERATIONS(self) -> int:
        """Get maximum iterations."""
        return self._settings.MAX_ITERATIONS

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value by key."""
        return getattr(self._settings, key, default)


# Create module-level instance
settings = SettingsManager()


def get_settings() -> SettingsManager:
    """Get the singleton SettingsManager instance."""
    return settings

