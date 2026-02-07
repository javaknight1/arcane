"""AI provider clients for Arcane.

This module provides a common interface for AI providers and
concrete implementations for supported providers.
"""

from .base import BaseAIClient, AIClientError, UsageStats
from .anthropic import AnthropicClient

__all__ = [
    "BaseAIClient",
    "AIClientError",
    "UsageStats",
    "AnthropicClient",
    "create_client",
]


def create_client(provider: str, **kwargs) -> BaseAIClient:
    """Factory to create AI clients by provider name.

    Args:
        provider: The provider name (e.g., "anthropic").
        **kwargs: Arguments to pass to the client constructor
            (e.g., api_key, model).

    Returns:
        An instance of the appropriate AI client.

    Raises:
        ValueError: If the provider is unknown.

    Example:
        >>> client = create_client("anthropic", api_key="sk-...")
        >>> client.provider_name
        'Anthropic Claude'
    """
    clients = {
        "anthropic": AnthropicClient,
    }

    if provider not in clients:
        available = list(clients.keys())
        raise ValueError(
            f"Unknown provider: {provider}. Available: {available}"
        )

    return clients[provider](**kwargs)
