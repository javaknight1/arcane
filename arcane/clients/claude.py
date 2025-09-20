"""Claude LLM Client - Implementation for Anthropic's Claude API."""

import os
import time
import random
from .base import BaseLLMClient
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ClaudeLLMClient(BaseLLMClient):
    """Claude (Anthropic) LLM client."""

    def __init__(self):
        super().__init__("claude")
        self._validate_api_key("ANTHROPIC_API_KEY")
        self.client = self._initialize_client()

    def _initialize_client(self):
        """Initialize the Anthropic client."""
        try:
            import anthropic
            return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def generate(self, prompt: str) -> str:
        """Generate text using Claude with retry logic for overload errors."""
        max_retries = 5
        base_delay = 2.0  # Start with 2 seconds
        max_delay = 60.0  # Max 60 seconds between retries

        for attempt in range(max_retries + 1):
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

            except Exception as e:
                error_msg = str(e)

                # Check if this is a retryable error (overload, rate limit, temporary issues)
                is_retryable = self._is_retryable_error(error_msg)

                if is_retryable and attempt < max_retries:
                    # Calculate exponential backoff with jitter
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)

                    # Log retry attempt
                    logger.warning(
                        "Claude API temporarily overloaded (attempt %d/%d). Waiting %.1f seconds before retry...",
                        attempt + 1, max_retries + 1, delay
                    )

                    time.sleep(delay)
                    continue

                # Handle non-retryable errors or final retry failure
                return self._handle_final_error(error_msg, attempt + 1, max_retries + 1)

    def _is_retryable_error(self, error_msg: str) -> bool:
        """Check if an error is retryable."""
        retryable_indicators = [
            "overloaded",
            "overloaded_error",
            "rate_limit",
            "429",  # Rate limit HTTP code
            "529",  # Service overloaded HTTP code
            "502",  # Bad gateway
            "503",  # Service unavailable
            "504",  # Gateway timeout
            "connection",
            "timeout",
            "temporary"
        ]

        error_lower = error_msg.lower()
        return any(indicator in error_lower for indicator in retryable_indicators)

    def _handle_final_error(self, error_msg: str, attempts_made: int, max_attempts: int) -> str:
        """Handle the final error after all retries are exhausted."""
        if "credit balance is too low" in error_msg.lower():
            # Estimate credits needed - this code stays the same
            estimated_tokens = 10000  # Rough estimate since we don't have prompt here
            estimated_cost = estimated_tokens * 0.000015
            raise RuntimeError(
                f"❌ Insufficient Anthropic API credits\n\n"
                f"💰 Estimated cost per request: ~${estimated_cost:.2f}\n"
                f"📊 Estimated tokens needed: ~{int(estimated_tokens):,}\n\n"
                f"Solutions:\n"
                f"  1. Add credits at: https://console.anthropic.com/settings/billing\n"
                f"  2. Use a different provider (add OPENAI_API_KEY or GOOGLE_API_KEY to .env)\n\n"
                f"Original error: {error_msg}"
            )
        elif "overloaded" in error_msg.lower() or "529" in error_msg:
            raise RuntimeError(
                f"❌ Claude API is currently overloaded\n\n"
                f"🔄 Tried {attempts_made} times over several minutes\n"
                f"⚠️  This is a temporary issue with Claude's servers\n\n"
                f"Solutions:\n"
                f"  1. Wait a few minutes and try again\n"
                f"  2. Use a different provider (add OPENAI_API_KEY or GOOGLE_API_KEY to .env)\n"
                f"  3. Try during off-peak hours\n\n"
                f"Original error: {error_msg}"
            )
        elif "invalid_request_error" in error_msg:
            raise RuntimeError(f"❌ Claude API request error: {error_msg}")
        elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            raise RuntimeError(
                f"❌ Authentication failed\n\n"
                f"Please check your ANTHROPIC_API_KEY in .env file\n"
                f"Get your API key at: https://console.anthropic.com/\n\n"
                f"Original error: {error_msg}"
            )
        else:
            raise RuntimeError(f"Claude API error: {error_msg}")