"""Claude API client: call Claude API for fix generation with prompt caching."""

import logging
import threading
import time
from typing import Optional

from anthropic import Anthropic, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for Claude API with retry logic and prompt caching."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-opus-4-1",
        max_tokens: int = 2048,
        temperature: float = 0.2,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        """Initialize Claude client.

        Args:
            api_key: Anthropic API key
            model: Model ID to use
            max_tokens: Maximum response tokens
            temperature: Sampling temperature (0-1)
            timeout_seconds: Request timeout
            max_retries: Maximum retry attempts

        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 5
        self._cb_lock = threading.Lock()

    def call_with_caching(
        self,
        system_prompt: str,
        user_message: str,
    ) -> Optional[str]:
        """Call Claude API with prompt caching enabled.

        Args:
            system_prompt: System prompt (cached)
            user_message: User message with context

        Returns:
            Response text or None on failure

        """
        with self._cb_lock:
            if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                logger.error("Circuit breaker open: too many API failures")
                return None

        for attempt in range(self.max_retries):
            try:
                start_time = time.time()

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=[
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=[
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    ],
                    timeout=self.timeout_seconds,
                )

                elapsed = time.time() - start_time
                logger.info(
                    f"Claude API call succeeded",
                    extra={
                        "model": self.model,
                        "tokens_used": response.usage.output_tokens,
                        "elapsed_seconds": elapsed,
                        "cache_hit": (
                            response.usage.cache_read_input_tokens > 0
                            if hasattr(response.usage, "cache_read_input_tokens")
                            else False
                        ),
                    },
                )

                # Reset circuit breaker on success
                with self._cb_lock:
                    self.circuit_breaker_failures = 0

                if not response.content:
                    logger.error("Claude API returned empty content")
                    return None

                return response.content[0].text

            except RateLimitError as e:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Rate limited, retrying in {wait_time}s",
                    extra={"attempt": attempt + 1, "max_retries": self.max_retries},
                )
                time.sleep(wait_time)

            except APIConnectionError as e:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Connection error, retrying in {wait_time}s",
                    extra={"attempt": attempt + 1, "error": str(e)},
                )
                time.sleep(wait_time)

            except Exception as e:
                logger.error(
                    f"Claude API error",
                    extra={
                        "error": str(e),
                        "attempt": attempt + 1,
                        "error_type": type(e).__name__,
                    },
                )
                with self._cb_lock:
                    self.circuit_breaker_failures += 1
                return None

        logger.error(
            "Claude API call failed after retries",
            extra={"max_retries": self.max_retries},
        )
        with self._cb_lock:
            self.circuit_breaker_failures += 1
        return None

    def get_system_prompt(self) -> str:
        """Get the system prompt for fix generation.

        Returns:
            System prompt text

        """
        return (
            "You are an expert debugging assistant. Your task is to analyze "
            "error information and code context to identify the root cause and "
            "propose a fix.\n\n"
            "Structure your response as follows:\n\n"
            "ROOT CAUSE: A single sentence explaining why the error occurred.\n\n"
            "FIX: A code snippet showing the fix. Use triple backticks with "
            "language specified (python, javascript, java, go).\n\n"
            "CONFIDENCE: A number from 0 to 1 or percentage (0-100%) indicating "
            "your confidence in the fix.\n\n"
            "EXPLANATION: A brief explanation of what the fix does and why it "
            "solves the problem.\n\n"
            "Be concise, accurate, and focus on the most likely root cause."
        )

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker after recovery."""
        self.circuit_breaker_failures = 0

    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open.

        Returns:
            True if circuit is open (too many failures)

        """
        with self._cb_lock:
            return self.circuit_breaker_failures >= self.circuit_breaker_threshold
