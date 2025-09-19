"""OpenAI LLM Client - Implementation for OpenAI's GPT API."""

import os
import time
import random
from .base import BaseLLMClient


class OpenAILLMClient(BaseLLMClient):
    """OpenAI (ChatGPT) LLM client."""

    def __init__(self):
        super().__init__("openai")
        self._validate_api_key("OPENAI_API_KEY")
        self.client = self._initialize_client()

    def _initialize_client(self):
        """Initialize the OpenAI client."""
        try:
            import openai
            return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def generate(self, prompt: str) -> str:
        """Generate text using OpenAI GPT with retry logic."""
        max_retries = 5
        base_delay = 2.0
        max_delay = 60.0

        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are a senior technical product manager and architect."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=8000,
                    temperature=0.7
                )
                return response.choices[0].message.content

            except Exception as e:
                error_msg = str(e)

                # Check if this is a retryable error
                is_retryable = self._is_retryable_error(error_msg)

                if is_retryable and attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    print(f"🔄 OpenAI API temporarily unavailable (attempt {attempt + 1}/{max_retries + 1})")
                    print(f"⏳ Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)
                    continue

                # Handle final error
                return self._handle_final_error(error_msg, attempt + 1, max_retries + 1)

    def _is_retryable_error(self, error_msg: str) -> bool:
        """Check if an error is retryable."""
        retryable_indicators = [
            "rate_limit",
            "429",
            "500",
            "502",
            "503",
            "504",
            "connection",
            "timeout",
            "temporary",
            "overloaded"
        ]
        error_lower = error_msg.lower()
        return any(indicator in error_lower for indicator in retryable_indicators)

    def _handle_final_error(self, error_msg: str, attempts_made: int, max_attempts: int) -> str:
        """Handle the final error after retries."""
        if "insufficient_quota" in error_msg.lower() or "billing" in error_msg.lower():
            estimated_tokens = 10000
            estimated_cost = estimated_tokens * 0.00003
            raise RuntimeError(
                f"❌ Insufficient OpenAI API credits\n\n"
                f"💰 Estimated cost per request: ~${estimated_cost:.2f}\n"
                f"📊 Estimated tokens needed: ~{int(estimated_tokens):,}\n\n"
                f"Solutions:\n"
                f"  1. Add credits at: https://platform.openai.com/account/billing\n"
                f"  2. Use a different provider (add ANTHROPIC_API_KEY or GOOGLE_API_KEY to .env)\n\n"
                f"Original error: {error_msg}"
            )
        elif "rate_limit" in error_msg.lower() or "429" in error_msg:
            raise RuntimeError(
                f"❌ OpenAI API rate limit exceeded\n\n"
                f"🔄 Tried {attempts_made} times over several minutes\n"
                f"⚠️  Your API usage has exceeded the rate limits\n\n"
                f"Solutions:\n"
                f"  1. Wait a few minutes and try again\n"
                f"  2. Upgrade your OpenAI plan for higher limits\n"
                f"  3. Use a different provider (add ANTHROPIC_API_KEY or GOOGLE_API_KEY to .env)\n\n"
                f"Original error: {error_msg}"
            )
        elif "unauthorized" in error_msg.lower() or "invalid_api_key" in error_msg.lower():
            raise RuntimeError(
                f"❌ Authentication failed\n\n"
                f"Please check your OPENAI_API_KEY in .env file\n"
                f"Get your API key at: https://platform.openai.com/api-keys\n\n"
                f"Original error: {error_msg}"
            )
        else:
            raise RuntimeError(f"OpenAI API error: {error_msg}")