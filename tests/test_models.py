"""Tests for arcane.models module and model-related functionality."""

import pytest

from arcane.models import (
    SUPPORTED_MODELS,
    DEFAULT_MODEL,
    ModelInfo,
    resolve_model,
    _MODEL_ID_TO_ALIAS,
)
from arcane.utils.cost_estimator import estimate_generation_cost, _resolve_model_id


class TestSupportedModels:
    """Tests for the SUPPORTED_MODELS registry."""

    def test_default_model_exists(self):
        """The DEFAULT_MODEL alias exists in SUPPORTED_MODELS."""
        assert DEFAULT_MODEL in SUPPORTED_MODELS

    def test_default_model_is_sonnet(self):
        """Default model is sonnet."""
        assert DEFAULT_MODEL == "sonnet"

    def test_all_models_have_required_fields(self):
        """Every model entry has alias, provider, model_id, description."""
        for alias, info in SUPPORTED_MODELS.items():
            assert info.alias == alias
            assert info.provider
            assert info.model_id
            assert info.description

    def test_reverse_lookup_matches(self):
        """_MODEL_ID_TO_ALIAS correctly maps every model_id back to its alias."""
        for alias, info in SUPPORTED_MODELS.items():
            assert _MODEL_ID_TO_ALIAS[info.model_id] == alias


class TestResolveModel:
    """Tests for the resolve_model function."""

    def test_resolve_alias_sonnet(self):
        """Resolve 'sonnet' alias to correct ModelInfo."""
        info = resolve_model("sonnet")
        assert info.provider == "anthropic"
        assert info.model_id == "claude-sonnet-4-20250514"
        assert info.alias == "sonnet"

    def test_resolve_alias_opus(self):
        """Resolve 'opus' alias to correct ModelInfo."""
        info = resolve_model("opus")
        assert info.provider == "anthropic"
        assert info.model_id == "claude-opus-4-20250514"
        assert info.alias == "opus"

    def test_resolve_alias_haiku(self):
        """Resolve 'haiku' alias to correct ModelInfo."""
        info = resolve_model("haiku")
        assert info.provider == "anthropic"
        assert info.model_id == "claude-haiku-4-5-20251001"
        assert info.alias == "haiku"

    def test_resolve_full_model_id(self):
        """Resolve a full model ID like 'claude-sonnet-4-20250514'."""
        info = resolve_model("claude-sonnet-4-20250514")
        assert info.alias == "sonnet"
        assert info.provider == "anthropic"
        assert info.model_id == "claude-sonnet-4-20250514"

    def test_resolve_full_model_id_opus(self):
        """Resolve full opus model ID."""
        info = resolve_model("claude-opus-4-20250514")
        assert info.alias == "opus"

    def test_resolve_invalid_model_raises(self):
        """Unknown model raises ValueError with helpful message."""
        with pytest.raises(ValueError, match="Unknown model.*gpt-5"):
            resolve_model("gpt-5")

    def test_resolve_invalid_model_lists_available(self):
        """Error message includes available models."""
        with pytest.raises(ValueError, match="sonnet"):
            resolve_model("nonexistent")

    def test_model_info_is_frozen(self):
        """ModelInfo instances are immutable."""
        info = resolve_model("sonnet")
        with pytest.raises(AttributeError):
            info.alias = "modified"


class TestCostEstimatorModelResolution:
    """Tests for model alias resolution in the cost estimator."""

    def test_resolve_model_id_from_alias(self):
        """_resolve_model_id resolves 'sonnet' to full model ID."""
        assert _resolve_model_id("sonnet") == "claude-sonnet-4-20250514"

    def test_resolve_model_id_passthrough(self):
        """_resolve_model_id passes through full model IDs unchanged."""
        assert _resolve_model_id("claude-sonnet-4-20250514") == "claude-sonnet-4-20250514"

    def test_resolve_model_id_unknown(self):
        """_resolve_model_id returns unknown model IDs unchanged (for fallback pricing)."""
        assert _resolve_model_id("unknown-model") == "unknown-model"

    def test_estimate_cost_with_alias(self):
        """estimate_generation_cost works with model aliases."""
        estimate = estimate_generation_cost(model="sonnet")
        assert estimate.estimated_cost_usd > 0

    def test_estimate_cost_with_full_id(self):
        """estimate_generation_cost works with full model IDs."""
        estimate = estimate_generation_cost(model="claude-sonnet-4-20250514")
        assert estimate.estimated_cost_usd > 0

    def test_estimate_cost_opus_more_expensive(self):
        """Opus should be more expensive than Sonnet."""
        sonnet = estimate_generation_cost(model="sonnet")
        opus = estimate_generation_cost(model="opus")
        assert opus.estimated_cost_usd > sonnet.estimated_cost_usd

    def test_estimate_cost_default_uses_sonnet(self):
        """Default model parameter uses sonnet pricing."""
        default = estimate_generation_cost()
        sonnet = estimate_generation_cost(model="sonnet")
        assert default.estimated_cost_usd == sonnet.estimated_cost_usd
