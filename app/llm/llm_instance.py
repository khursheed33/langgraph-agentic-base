"""Singleton LLM instance supporting multiple providers (Groq, Gemini, Perplexity)."""

from typing import Any, Optional, Union

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq

from app.utils.logger import logger
from app.utils.settings import settings


class LLMInstance:
    """Singleton LLM instance supporting multiple providers."""

    _instance: Optional["LLMInstance"] = None
    _llm: Optional[BaseChatModel] = None
    _provider: Optional[str] = None

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
        """Set up the LLM instance based on provider configuration."""
        provider = settings.LLM_PROVIDER.lower()
        self._provider = provider
        temperature = settings.LLM_TEMPERATURE
        max_tokens = settings.LLM_MAX_TOKENS
        timeout = settings.LLM_TIMEOUT

        try:
            if provider == "groq":
                self._setup_groq(temperature, max_tokens, timeout)
            elif provider == "gemini":
                self._setup_gemini(temperature, max_tokens, timeout)
            elif provider == "perplexity":
                self._setup_perplexity(temperature, max_tokens, timeout)
            else:
                raise ValueError(
                    f"Unsupported LLM provider: {provider}. "
                    "Supported providers: groq, gemini, perplexity"
                )
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    def _setup_groq(
        self, temperature: float, max_tokens: int, timeout: int
    ) -> None:
        """Set up Groq LLM provider."""
        api_key = settings.GROQ_API_KEY
        model = settings.GROQ_MODEL

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )

        groq_kwargs: dict[str, Any] = {
            "groq_api_key": api_key,
            "model_name": model,
            "temperature": temperature,
        }

        if max_tokens:
            groq_kwargs["max_tokens"] = max_tokens
        if timeout:
            groq_kwargs["timeout"] = timeout

        self._llm = ChatGroq(**groq_kwargs)
        logger.info(
            f"LLM initialized with provider: groq, model: {model}, "
            f"temperature: {temperature}, max_tokens: {max_tokens}, timeout: {timeout}"
        )

    def _setup_gemini(
        self, temperature: float, max_tokens: int, timeout: int
    ) -> None:
        """Set up Google Gemini LLM provider."""
        try:
            from app.llm.gemini_llm import GeminiLLM

            gemini = GeminiLLM(
                api_key=settings.GEMINI_API_KEY,
                model=getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro"),
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            self._llm = gemini.get_llm()
        except ImportError:
            raise ImportError(
                "langchain-google-genai not installed. "
                "Install with: pip install langchain-google-genai"
            )

    def _setup_perplexity(
        self, temperature: float, max_tokens: int, timeout: int
    ) -> None:
        """Set up Perplexity LLM provider."""
        try:
            from app.llm.perplexity_llm import PerplexityLLM

            perplexity = PerplexityLLM(
                api_key=settings.PERPLEXITY_API_KEY,
                model=getattr(settings, "PERPLEXITY_MODEL", "llama-2-70b-chat"),
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            self._llm = perplexity.get_llm()
        except ImportError:
            raise ImportError(
                "langchain-openai not properly configured for Perplexity. "
                "Install with: pip install langchain-openai"
            )

    def get_llm(self) -> BaseChatModel:
        """Get the LLM instance."""
        if self._llm is None:
            self._setup_llm()
        return self._llm

    def get_provider(self) -> str:
        """Get the current LLM provider."""
        if self._provider is None:
            self._provider = settings.LLM_PROVIDER.lower()
        return self._provider

    @staticmethod
    def reset() -> None:
        """Reset the singleton instance (useful for testing)."""
        LLMInstance._instance = None
        LLMInstance._llm = None
        LLMInstance._provider = None


def get_llm() -> BaseChatModel:
    """Get the singleton LLM instance."""
    return LLMInstance().get_llm()


def get_llm_provider() -> str:
    """Get the current LLM provider name."""
    return LLMInstance().get_provider()


