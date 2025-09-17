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
            raise RuntimeError(f"Claude API error: {str(e)}")