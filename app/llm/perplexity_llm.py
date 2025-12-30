"""Perplexity LLM provider implementation using OpenAI-compatible API."""

from typing import Any, Optional

from langchain_openai import ChatOpenAI

from app.utils.logger import logger
from app.utils.settings import settings


class PerplexityLLM:
    """Perplexity LLM provider wrapper using OpenAI-compatible API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """Initialize Perplexity LLM.

        Args:
            api_key: Perplexity API key. If None, loaded from settings.
            model: Model name. If None, loaded from settings.
            temperature: Temperature setting. If None, loaded from settings.
            max_tokens: Max tokens. If None, loaded from settings.
            timeout: Request timeout. If None, loaded from settings.
        """
        self.api_key = api_key or settings.PERPLEXITY_API_KEY
        self.model = model or getattr(settings, "PERPLEXITY_MODEL", "llama-2-70b-chat")
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self.timeout = timeout or settings.LLM_TIMEOUT

        if not self.api_key:
            raise ValueError(
                "PERPLEXITY_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )

        self._initialize_llm()

    def _initialize_llm(self) -> None:
        """Initialize the Perplexity LLM instance."""
        try:
            perplexity_kwargs: dict[str, Any] = {
                "api_key": self.api_key,
                "model": self.model,
                "base_url": "https://api.perplexity.ai",
                "temperature": self.temperature,
            }

            # Add optional parameters
            if self.max_tokens:
                perplexity_kwargs["max_tokens"] = self.max_tokens

            if self.timeout:
                perplexity_kwargs["request_timeout"] = self.timeout

            # Use OpenAI-compatible interface for Perplexity
            self.llm = ChatOpenAI(**perplexity_kwargs)

            logger.info(
                f"Perplexity LLM initialized: model={self.model}, "
                f"temperature={self.temperature}, max_tokens={self.max_tokens}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity LLM: {e}")
            raise

    def get_llm(self) -> ChatOpenAI:
        """Get the LLM instance."""
        return self.llm

    def invoke(self, messages: list) -> Any:
        """Invoke the LLM with messages.

        Args:
            messages: List of messages to send to LLM.

        Returns:
            LLM response.
        """
        return self.llm.invoke(messages)

    def batch(self, messages_list: list[list]) -> list:
        """Batch invoke the LLM.

        Args:
            messages_list: List of message lists.

        Returns:
            List of LLM responses.
        """
        return self.llm.batch(messages_list)
