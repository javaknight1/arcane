"""OpenAI LLM Client - Implementation for OpenAI's GPT API."""

import os
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
        """Generate text using OpenAI GPT."""
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
            # Enhanced error handling with specific guidance
            error_msg = str(e)
            if "insufficient_quota" in error_msg.lower() or "billing" in error_msg.lower():
                # Estimate cost for OpenAI
                estimated_tokens = len(prompt.split()) * 1.3 + 8000
                estimated_cost = estimated_tokens * 0.00003  # Approximate cost per token for GPT-4
                raise RuntimeError(
                    f"❌ Insufficient OpenAI API credits\n\n"
                    f"💰 Estimated cost for this request: ~${estimated_cost:.2f}\n"
                    f"📊 Estimated tokens needed: ~{int(estimated_tokens):,}\n\n"
                    f"Solutions:\n"
                    f"  1. Add credits at: https://platform.openai.com/account/billing\n"
                    f"  2. Use a different provider (add ANTHROPIC_API_KEY or GOOGLE_API_KEY to .env)\n\n"
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