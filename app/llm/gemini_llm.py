"""Gemini LLM provider implementation using Google's Generative AI."""

from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI

from app.utils.logger import logger
from app.utils.settings import settings


class GeminiLLM:
    """Gemini LLM provider wrapper."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """Initialize Gemini LLM.

        Args:
            api_key: Google API key. If None, loaded from settings.
            model: Model name. If None, loaded from settings.
            temperature: Temperature setting. If None, loaded from settings.
            max_tokens: Max tokens. If None, loaded from settings.
            timeout: Request timeout. If None, loaded from settings.
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro")
        self.temperature = temperature or settings.LLM_TEMPERATURE
        self.max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        self.timeout = timeout or settings.LLM_TIMEOUT

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )

        self._initialize_llm()

    def _initialize_llm(self) -> None:
        """Initialize the Gemini LLM instance."""
        try:
            gemini_kwargs: dict[str, Any] = {
                "google_api_key": self.api_key,
                "model": self.model,
                "temperature": self.temperature,
            }

            # Add optional parameters
            if self.max_tokens:
                gemini_kwargs["max_output_tokens"] = self.max_tokens

            self.llm = ChatGoogleGenerativeAI(**gemini_kwargs)

            logger.info(
                f"Gemini LLM initialized: model={self.model}, "
                f"temperature={self.temperature}, max_tokens={self.max_tokens}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {e}")
            raise

    def get_llm(self) -> ChatGoogleGenerativeAI:
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
