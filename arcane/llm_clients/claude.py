"""Claude LLM Client - Implementation for Anthropic's Claude API."""

import os
from .base import BaseLLMClient


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
        """Generate text using Claude."""
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            # Enhanced error handling with specific guidance
            error_msg = str(e)
            if "credit balance is too low" in error_msg.lower():
                # Estimate credits needed based on prompt size
                estimated_tokens = len(prompt.split()) * 1.3 + 8000  # Input + max output tokens
                estimated_cost = estimated_tokens * 0.000015  # Approximate cost per token for Claude
                raise RuntimeError(
                    f"❌ Insufficient Anthropic API credits\n\n"
                    f"💰 Estimated cost for this request: ~${estimated_cost:.2f}\n"
                    f"📊 Estimated tokens needed: ~{int(estimated_tokens):,}\n\n"
                    f"Solutions:\n"
                    f"  1. Add credits at: https://console.anthropic.com/settings/billing\n"
                    f"  2. Use a different provider (add OPENAI_API_KEY or GOOGLE_API_KEY to .env)\n\n"
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