"""Gemini LLM Client - Implementation for Google's Gemini API."""

import os
from .base import BaseLLMClient


class GeminiLLMClient(BaseLLMClient):
    """Google Gemini LLM client."""

    def __init__(self):
        super().__init__("gemini")
        self._validate_api_key("GOOGLE_API_KEY")
        self.client = self._initialize_client()

    def _initialize_client(self):
        """Initialize the Gemini client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            return genai.GenerativeModel('gemini-1.5-pro')
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")

    def generate(self, prompt: str) -> str:
        """Generate text using Gemini."""
        try:
            import google.generativeai as genai
            response = self.client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=8000,
                    temperature=0.7
                )
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")