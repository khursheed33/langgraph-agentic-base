"""Configuration management."""

from pathlib import Path
from typing import Dict, Any
import yaml

from app.guardrails.config import GuardrailConfig
from app.utils.logger import logger


def load_api_config() -> Dict[str, Any]:
    """Load API configuration from config.yaml.

    Returns:
        Dictionary containing API configuration.
    """
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    api_config = {
        "host": "0.0.0.0",
        "port": 8000,
        "title": "LangGraph Agentic Base API",
        "version": "0.1.0",
        "description": "Multi-agent system API with supervisor and task planner",
        "enable_cors": True,
        "cors_origins": ["*"],
        "prefix": "/api/v1",
    }

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
                api_config_from_file = config_data.get("api", {})
                api_config.update(api_config_from_file)
        except Exception as e:
            logger.warning(f"Failed to load API config from {config_path}: {e}")

    return api_config


def load_guardrail_config() -> GuardrailConfig:
    """Load guardrail configuration from config.yaml.

    Returns:
        GuardrailConfig instance with loaded configuration.
    """
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    # Default guardrail configuration
    guardrail_config = GuardrailConfig()

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
                guardrail_data = config_data.get("guardrails", {})

                # Update guardrail config from file
                for key, value in guardrail_data.items():
                    if hasattr(guardrail_config, key):
                        # Handle GuardrailSettings objects
                        if key in ['input_safety', 'input_content_filter', 'output_safety',
                                 'output_quality', 'rate_limiting', 'ethical_boundaries', 'scope_validation']:
                            from app.guardrails.config import GuardrailSettings
                            if isinstance(value, dict):
                                setattr(guardrail_config, key, GuardrailSettings(**value))
                            else:
                                setattr(guardrail_config, key, value)
                        else:
                            setattr(guardrail_config, key, value)

        except Exception as e:
            logger.warning(f"Failed to load guardrail config from {config_path}: {e}")

    return guardrail_config