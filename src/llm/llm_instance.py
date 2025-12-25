"""Singleton LLM instance using Groq."""

from typing import Optional

from langchain_groq import ChatGroq

from src.utils.logger import logger
from src.utils.settings import settings


class LLMInstance:
    """Singleton LLM instance."""

    _instance: Optional["LLMInstance"] = None
    _llm: Optional[ChatGroq] = None

    def __new__(cls) -> "LLMInstance":
        """Create or return existing LLM instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize LLM if not already initialized."""
        if self._llm is None:
            self._setup_llm()

    def _setup_llm(self) -> None:
        """Set up the Groq LLM instance."""
        api_key = settings.GROQ_API_KEY
        model = settings.GROQ_MODEL

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )

        try:
            self._llm = ChatGroq(
                groq_api_key=api_key,
                model_name=model,
                temperature=0.1,
            )
            logger.info(f"LLM initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    def get_llm(self) -> ChatGroq:
        """Get the LLM instance."""
        if self._llm is None:
            self._setup_llm()
        return self._llm


def get_llm() -> ChatGroq:
    """Get the singleton LLM instance."""
    return LLMInstance().get_llm()

