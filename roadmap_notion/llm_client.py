"""LLM Client - Unified interface for multiple LLM providers."""

import os
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, provider: str):
        self.provider = provider

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text using the LLM."""
        pass


class ClaudeLLMClient(BaseLLMClient):
    """Claude (Anthropic) LLM client."""

    def __init__(self):
        super().__init__("claude")
        self._validate_api_key("ANTHROPIC_API_KEY")
        self.client = self._initialize_client()

    def _validate_api_key(self, key_name: str) -> None:
        """Validate API key exists."""
        if not os.getenv(key_name):
            raise ValueError(f"{key_name} environment variable not set")

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


class OpenAILLMClient(BaseLLMClient):
    """OpenAI (ChatGPT) LLM client."""

    def __init__(self):
        super().__init__("openai")
        self._validate_api_key("OPENAI_API_KEY")
        self.client = self._initialize_client()

    def _validate_api_key(self, key_name: str) -> None:
        """Validate API key exists."""
        if not os.getenv(key_name):
            raise ValueError(f"{key_name} environment variable not set")

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


class GeminiLLMClient(BaseLLMClient):
    """Google Gemini LLM client."""

    def __init__(self):
        super().__init__("gemini")
        self._validate_api_key("GOOGLE_API_KEY")
        self.client = self._initialize_client()

    def _validate_api_key(self, key_name: str) -> None:
        """Validate API key exists."""
        if not os.getenv(key_name):
            raise ValueError(f"{key_name} environment variable not set")

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


class LLMClient:
    """Factory class for creating LLM clients."""

    @staticmethod
    def create(provider: str) -> BaseLLMClient:
        """Create an LLM client for the specified provider."""
        providers = {
            'claude': ClaudeLLMClient,
            'openai': OpenAILLMClient,
            'gemini': GeminiLLMClient
        }

        if provider not in providers:
            raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {list(providers.keys())}")

        return providers[provider]()

    def __init__(self, provider: str):
        """Initialize LLM client for the specified provider."""
        self.client = self.create(provider)
        self.provider = provider

    def generate(self, prompt: str) -> str:
        """Generate text using the configured LLM."""
        return self.client.generate(prompt)

