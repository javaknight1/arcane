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
            raise RuntimeError(f"OpenAI API error: {str(e)}")