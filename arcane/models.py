"""Supported AI models for Arcane.

Provides a curated list of supported models with aliases, provider mapping,
and a resolve_model() function to look up models by alias or full model ID.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelInfo:
    """Information about a supported AI model."""

    alias: str
    provider: str
    model_id: str
    description: str


# Curated list of supported models
SUPPORTED_MODELS: dict[str, ModelInfo] = {
    "sonnet": ModelInfo(
        alias="sonnet",
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        description="Claude Sonnet 4 — fast, balanced (recommended)",
    ),
    "opus": ModelInfo(
        alias="opus",
        provider="anthropic",
        model_id="claude-opus-4-20250514",
        description="Claude Opus 4 — most capable, slower",
    ),
    "haiku": ModelInfo(
        alias="haiku",
        provider="anthropic",
        model_id="claude-haiku-4-5-20251001",
        description="Claude Haiku 4.5 — fastest, cheapest",
    ),
}

DEFAULT_MODEL = "sonnet"

# Reverse lookup: full model ID -> alias
_MODEL_ID_TO_ALIAS: dict[str, str] = {
    info.model_id: alias for alias, info in SUPPORTED_MODELS.items()
}


def resolve_model(model: str) -> ModelInfo:
    """Resolve a model alias or full model ID to a ModelInfo.

    Lookup order:
    1. Check if it's a known alias (e.g., "sonnet", "opus", "haiku")
    2. Check if it's a known full model ID (e.g., "claude-sonnet-4-20250514")
    3. Raise ValueError with a helpful message

    Args:
        model: A model alias or full model ID.

    Returns:
        ModelInfo with provider, model_id, and description.

    Raises:
        ValueError: If the model is not recognized.
    """
    # Check aliases first
    if model in SUPPORTED_MODELS:
        return SUPPORTED_MODELS[model]

    # Check full model IDs
    if model in _MODEL_ID_TO_ALIAS:
        alias = _MODEL_ID_TO_ALIAS[model]
        return SUPPORTED_MODELS[alias]

    # Not found
    available = [
        f"  {alias:<8} ({info.model_id}) — {info.description}"
        for alias, info in SUPPORTED_MODELS.items()
    ]
    raise ValueError(
        f"Unknown model: '{model}'\n\n"
        f"Available models:\n" + "\n".join(available)
    )
