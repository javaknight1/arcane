"""Protocol definitions for LLM client interfaces."""

from typing import Protocol, Dict, Any, Optional, NamedTuple


class GenerationResultProtocol(Protocol):
    """Protocol for LLM generation results."""

    def __init__(
        self,
        content: str,
        tokens_used: int,
        cost: float,
        model: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Initialize generation result."""
        ...

    @property
    def content(self) -> str:
        """Generated content."""
        ...

    @property
    def tokens_used(self) -> int:
        """Number of tokens used in generation."""
        ...

    @property
    def cost(self) -> float:
        """Cost of the generation."""
        ...

    @property
    def model(self) -> str:
        """Model used for generation."""
        ...

    @property
    def success(self) -> bool:
        """Whether generation was successful."""
        ...

    @property
    def error(self) -> Optional[str]:
        """Error message if generation failed."""
        ...


class LLMClientProtocol(Protocol):
    """Protocol for LLM client implementations."""

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
    ) -> str:
        """Generate text based on prompt."""
        ...

    def generate_with_result(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
    ) -> GenerationResultProtocol:
        """Generate text and return detailed result information."""
        ...

    def estimate_cost(
        self,
        prompt: str,
        estimated_output_tokens: int = 1000
    ) -> float:
        """Estimate cost for a generation request."""
        ...

    @property
    def model_name(self) -> str:
        """Name of the model being used."""
        ...

    @property
    def provider(self) -> str:
        """Name of the LLM provider."""
        ...

    def is_available(self) -> bool:
        """Check if the LLM client is available and configured."""
        ...


class CostEstimationProtocol(Protocol):
    """Protocol for cost estimation functionality."""

    def estimate_cost(
        self,
        llm_provider: str,
        input_text: str,
        estimated_output_tokens: int
    ) -> 'CostResult':
        """Estimate cost for LLM generation."""
        ...

    def estimate_individual_item_costs(
        self,
        llm_provider: str,
        item_counts: Dict[str, int],
        context: str
    ) -> Dict[str, Any]:
        """Estimate costs for individual roadmap items."""
        ...

    def format_individual_item_costs(
        self,
        cost_data: Dict[str, Any]
    ) -> str:
        """Format cost data for display."""
        ...


class CostResult(NamedTuple):
    """Cost estimation result."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float