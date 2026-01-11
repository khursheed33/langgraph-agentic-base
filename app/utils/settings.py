"""Singleton SettingsManager using dynaconf for configuration management."""

import logging
from pathlib import Path
from typing import Any, Optional

import yaml
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
            # Load config.yaml if it exists
            config_file = Path(__file__).parent.parent / "config" / "config.yaml"
            config_data: dict[str, Any] = {}
            
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f) or {}
                _logger.info(f"Loaded config from {config_file}")
            else:
                _logger.warning(f"Config file not found: {config_file}. Using defaults.")
            
            # Extract defaults from config.yaml
            llm_config = config_data.get("llm", {})
            workflow_config = config_data.get("workflow", {})
            neo4j_config = config_data.get("neo4j", {})
            logging_config = config_data.get("logging", {})
            output_config = config_data.get("output", {})
            
            self._settings = Dynaconf(
                envvar_prefix=False,
                settings_files=[],
                environments=False,
                load_dotenv=True,
                dotenv_path=".env",
                validators=[
                    # LLM provider selection
                    Validator("LLM_PROVIDER", default=llm_config.get("provider", "groq")),
                    Validator("LLM_TEMPERATURE", default=llm_config.get("temperature", 0.1), cast=float),
                    Validator("LLM_MAX_TOKENS", default=llm_config.get("max_tokens", 8192), cast=int),
                    Validator("LLM_MAX_INPUT_TOKENS", default=llm_config.get("max_input_tokens", 32768), cast=int),
                    Validator("LLM_TOP_P", default=llm_config.get("top_p", 1.0), cast=float),
                    Validator("LLM_TIMEOUT", default=llm_config.get("timeout", 60), cast=int),
                    # Groq settings
                    Validator("GROQ_API_KEY", default=""),
                    Validator("GROQ_MODEL", default=llm_config.get("groq_model", "llama-3.1-70b-versatile")),
                    # Gemini settings
                    Validator("GEMINI_API_KEY", default=""),
                    Validator("GEMINI_MODEL", default=llm_config.get("gemini_model", "gemini-1.5-pro")),
                    # Perplexity settings
                    Validator("PERPLEXITY_API_KEY", default=""),
                    Validator("PERPLEXITY_MODEL", default=llm_config.get("perplexity_model", "llama-2-70b-chat")),
                    # Neo4j settings
                    Validator("NEO4J_URI", default=neo4j_config.get("uri", "bolt://localhost:7687")),
                    Validator("NEO4J_USER", default=neo4j_config.get("user", "neo4j")),
                    Validator("NEO4J_PASSWORD", default=neo4j_config.get("password", "")),
                    # JWT settings
                    Validator("JWT_SECRET_KEY", default="your-secret-key-change-in-production"),
                    # Workflow settings
                    Validator("LOG_LEVEL", default=logging_config.get("level", "INFO")),
                    Validator("MAX_ITERATIONS", default=workflow_config.get("max_iterations", 50), cast=int),
                    # Output settings
                    Validator("OUTPUT_DIRECTORY", default=output_config.get("directory", "output")),
                    Validator("OUTPUT_AUTO_CREATE", default=output_config.get("auto_create", True), cast=bool),
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
    def GEMINI_API_KEY(self) -> str:
        """Get Gemini API key."""
        return self._settings.GEMINI_API_KEY

    @property
    def GEMINI_MODEL(self) -> str:
        """Get Gemini model name."""
        return self._settings.GEMINI_MODEL

    @property
    def PERPLEXITY_API_KEY(self) -> str:
        """Get Perplexity API key."""
        return self._settings.PERPLEXITY_API_KEY

    @property
    def PERPLEXITY_MODEL(self) -> str:
        """Get Perplexity model name."""
        return self._settings.PERPLEXITY_MODEL

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

    @property
    def LLM_PROVIDER(self) -> str:
        """Get LLM provider."""
        return self._settings.LLM_PROVIDER

    @property
    def LLM_TEMPERATURE(self) -> float:
        """Get LLM temperature."""
        return self._settings.LLM_TEMPERATURE

    @property
    def LLM_MAX_TOKENS(self) -> int:
        """Get LLM max tokens."""
        return self._settings.LLM_MAX_TOKENS

    @property
    def LLM_MAX_INPUT_TOKENS(self) -> int:
        """Get LLM max input tokens."""
        return self._settings.LLM_MAX_INPUT_TOKENS

    @property
    def LLM_TOP_P(self) -> float:
        """Get LLM top-p."""
        return self._settings.LLM_TOP_P

    @property
    def LLM_TIMEOUT(self) -> int:
        """Get LLM timeout."""
        return self._settings.LLM_TIMEOUT

    @property
    def JWT_SECRET_KEY(self) -> str:
        """Get JWT secret key."""
        return self._settings.JWT_SECRET_KEY

    @property
    def OUTPUT_DIRECTORY(self) -> str:
        """Get output directory path."""
        return self._settings.OUTPUT_DIRECTORY

    @property
    def OUTPUT_AUTO_CREATE(self) -> bool:
        """Get whether to auto-create output directory."""
        return self._settings.OUTPUT_AUTO_CREATE

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value by key."""
        return getattr(self._settings, key, default)


# Create module-level instance
settings = SettingsManager()


def get_settings() -> SettingsManager:
    """Get the singleton SettingsManager instance."""
    return settings

