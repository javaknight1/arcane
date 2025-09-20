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
            # Enhanced error handling with specific guidance
            error_msg = str(e)
            if "quota" in error_msg.lower() or "billing" in error_msg.lower() or "exceeded" in error_msg.lower():
                raise RuntimeError(
                    f"❌ Google Gemini API quota exceeded or billing issue\n\n"
                    f"💡 Gemini has generous free tiers\n"
                    f"📊 This request requires a valid Google API setup\n\n"
                    f"Solutions:\n"
                    f"  1. Check quota at: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com\n"
                    f"  2. Enable billing if needed: https://console.cloud.google.com/billing\n"
                    f"  3. Use a different provider (add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env)\n\n"
                    f"Original error: {error_msg}"
                )
            elif "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower() or "permission" in error_msg.lower():
                raise RuntimeError(
                    f"❌ Authentication failed\n\n"
                    f"Please check your GOOGLE_API_KEY in .env file\n"
                    f"Get your API key at: https://aistudio.google.com/app/apikey\n\n"
                    f"Original error: {error_msg}"
                )
            else:
                raise RuntimeError(f"Gemini API error: {error_msg}")