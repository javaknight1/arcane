"""Claude LLM Client - Implementation for Anthropic's Claude API."""

import os
import time
import random
from typing import Optional, Dict, Any, List, Tuple
from .base import BaseLLMClient
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# Default models for Claude
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_HAIKU_MODEL = "claude-haiku-4-20250514"


class ClaudeLLMClient(BaseLLMClient):
    """Claude (Anthropic) LLM client."""

    def __init__(self, model: Optional[str] = None):
        """Initialize Claude client.

        Args:
            model: Optional model name (e.g., 'claude-sonnet-4-20250514', 'claude-haiku-4-20250514')
        """
        super().__init__("claude", model)
        self._validate_api_key("ANTHROPIC_API_KEY")
        self.client = self._initialize_client()

    def _get_default_model(self) -> str:
        """Get the default Claude model."""
        return DEFAULT_CLAUDE_MODEL

    def _initialize_client(self):
        """Initialize the Anthropic client."""
        try:
            import anthropic
            return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def generate(self, prompt: str, max_tokens: int = None) -> str:
        """Generate text using Claude with retry logic for overload errors."""
        max_retries = 5
        base_delay = 2.0  # Start with 2 seconds
        max_delay = 60.0  # Max 60 seconds between retries

        # Use appropriate token limit within Claude API constraints (max 8192)
        if max_tokens is None:
            # Claude 3.5 Sonnet has a max of 8192 output tokens
            max_tokens = 8192

        # Always use streaming for roadmap generation to avoid timeout
        use_streaming = 'roadmap' in prompt.lower() or max_tokens >= 8000

        for attempt in range(max_retries + 1):
            try:
                model_name = self.get_model_name()

                if use_streaming:
                    # Use streaming for large responses to avoid timeout
                    response_text = ""
                    with self.client.messages.stream(
                        model=model_name,
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    ) as stream:
                        for text in stream.text_stream:
                            response_text += text
                    return response_text
                else:
                    # Use regular request for smaller responses
                    response = self.client.messages.create(
                        model=model_name,
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text

            except Exception as e:
                error_msg = str(e)

                # Check for streaming requirement error first
                if "streaming is required" in error_msg.lower():
                    # Retry with streaming enabled
                    logger.warning("Request requires streaming due to duration. Retrying with streaming enabled...")
                    use_streaming = True
                    continue

                # Check if this is a retryable error (overload, rate limit, temporary issues)
                is_retryable = self._is_retryable_error(error_msg)

                if is_retryable and attempt < max_retries:
                    # Calculate exponential backoff with jitter
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)

                    # Log retry attempt
                    logger.warning(
                        "Claude API temporarily overloaded (attempt %d/%d). Waiting %.1f seconds before retry...",
                        attempt + 1, max_retries + 1, delay
                    )

                    time.sleep(delay)
                    continue

                # Handle non-retryable errors or final retry failure
                return self._handle_final_error(error_msg, attempt + 1, max_retries + 1)

    def _is_retryable_error(self, error_msg: str) -> bool:
        """Check if an error is retryable."""
        retryable_indicators = [
            "overloaded",
            "overloaded_error",
            "rate_limit",
            "429",  # Rate limit HTTP code
            "529",  # Service overloaded HTTP code
            "502",  # Bad gateway
            "503",  # Service unavailable
            "504",  # Gateway timeout
            "connection",
            "timeout",
            "temporary"
        ]

        error_lower = error_msg.lower()
        return any(indicator in error_lower for indicator in retryable_indicators)

    def _handle_final_error(self, error_msg: str, attempts_made: int, max_attempts: int) -> str:
        """Handle the final error after all retries are exhausted."""
        if "credit balance is too low" in error_msg.lower():
            # Estimate credits needed - this code stays the same
            estimated_tokens = 10000  # Rough estimate since we don't have prompt here
            estimated_cost = estimated_tokens * 0.000015
            raise RuntimeError(
                f"❌ Insufficient Anthropic API credits\n\n"
                f"💰 Estimated cost per request: ~${estimated_cost:.2f}\n"
                f"📊 Estimated tokens needed: ~{int(estimated_tokens):,}\n\n"
                f"Solutions:\n"
                f"  1. Add credits at: https://console.anthropic.com/settings/billing\n"
                f"  2. Use a different provider (add OPENAI_API_KEY or GOOGLE_API_KEY to .env)\n\n"
                f"Original error: {error_msg}"
            )
        elif "overloaded" in error_msg.lower() or "529" in error_msg:
            raise RuntimeError(
                f"❌ Claude API is currently overloaded\n\n"
                f"🔄 Tried {attempts_made} times over several minutes\n"
                f"⚠️  This is a temporary issue with Claude's servers\n\n"
                f"Solutions:\n"
                f"  1. Wait a few minutes and try again\n"
                f"  2. Use a different provider (add OPENAI_API_KEY or GOOGLE_API_KEY to .env)\n"
                f"  3. Try during off-peak hours\n\n"
                f"Original error: {error_msg}"
            )
        elif "invalid_request_error" in error_msg:
            raise RuntimeError(f"❌ Claude API request error: {error_msg}")
        elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            raise RuntimeError(
                f"❌ Authentication failed\n\n"
                f"Please check your ANTHROPIC_API_KEY in .env file\n"
                f"Get your API key at: https://console.anthropic.com/\n\n"
                f"Original error: {error_msg}"
            )
        else:
            raise RuntimeError(f"Claude API error: {error_msg}")

    def generate_with_cached_system(
        self,
        system_prompt: str,
        user_prompt: str,
        cache_system: bool = True,
        max_tokens: int = None
    ) -> str:
        """Generate text using Claude with a cached system prompt.

        Uses Claude's prompt caching to reduce costs when the same system
        prompt is used repeatedly. Cached prompts are stored for up to 5 minutes.

        Args:
            system_prompt: The system prompt to cache
            user_prompt: The user prompt (varies per request)
            cache_system: Whether to enable caching on the system prompt
            max_tokens: Maximum tokens in response

        Returns:
            Generated text from Claude
        """
        max_retries = 5
        base_delay = 2.0
        max_delay = 60.0

        if max_tokens is None:
            max_tokens = 8192

        # Build system configuration with optional cache control
        system_config: Dict[str, Any] = {
            "type": "text",
            "text": system_prompt,
        }

        if cache_system:
            system_config["cache_control"] = {"type": "ephemeral"}

        for attempt in range(max_retries + 1):
            try:
                model_name = self.get_model_name()

                response = self.client.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    system=[system_config],
                    messages=[{"role": "user", "content": user_prompt}]
                )

                # Log cache usage if available
                if hasattr(response, 'usage'):
                    usage = response.usage
                    cache_creation = getattr(usage, 'cache_creation_input_tokens', 0)
                    cache_read = getattr(usage, 'cache_read_input_tokens', 0)
                    if cache_creation or cache_read:
                        logger.info(
                            f"Cache stats - created: {cache_creation}, read: {cache_read}"
                        )

                return response.content[0].text

            except Exception as e:
                error_msg = str(e)
                is_retryable = self._is_retryable_error(error_msg)

                if is_retryable and attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    logger.warning(
                        "Claude API temporarily overloaded (attempt %d/%d). Waiting %.1f seconds...",
                        attempt + 1, max_retries + 1, delay
                    )
                    time.sleep(delay)
                    continue

                return self._handle_final_error(error_msg, attempt + 1, max_retries + 1)

    def create_cacheable_context(self, roadmap_context: str) -> str:
        """Create a system prompt with roadmap context for caching.

        This method builds a system prompt that includes the roadmap context
        in a format optimized for Claude's prompt caching. The roadmap context
        is placed at the beginning of the prompt for efficient caching.

        Args:
            roadmap_context: The full roadmap context to include

        Returns:
            A system prompt string suitable for caching
        """
        return f"""You are generating content for a software development roadmap.

=== ROADMAP CONTEXT (CACHED) ===
{roadmap_context}

=== INSTRUCTIONS ===
Generate content that is consistent with the roadmap context above.
Use the same technologies, patterns, and approaches mentioned.
Ensure your output:
- Maintains consistency with previously generated items
- Uses the established naming conventions
- References dependencies appropriately
- Follows the overall project architecture
"""

    def generate_batch_with_cached_system(
        self,
        system_prompt: str,
        user_prompts: List[str],
        cache_system: bool = True,
        max_tokens: int = None
    ) -> List[str]:
        """Generate multiple responses with the same cached system prompt.

        This method is optimized for batch generation where the same system
        context is used for multiple user prompts. After the first request,
        subsequent requests will read from the cache.

        Args:
            system_prompt: The system prompt to cache
            user_prompts: List of user prompts to process
            cache_system: Whether to enable caching on the system prompt
            max_tokens: Maximum tokens per response

        Returns:
            List of generated responses
        """
        responses = []
        total_cache_reads = 0
        total_cache_writes = 0

        for i, user_prompt in enumerate(user_prompts):
            logger.debug(f"Processing prompt {i + 1}/{len(user_prompts)}")

            response = self.generate_with_cached_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                cache_system=cache_system,
                max_tokens=max_tokens
            )
            responses.append(response)

        logger.info(
            f"Batch generation complete: {len(responses)} responses"
        )

        return responses

    def get_cache_pricing_info(self) -> Dict[str, Any]:
        """Get pricing information for prompt caching.

        Returns:
            Dictionary with cache pricing details
        """
        return {
            'cache_write_cost_per_token': 0.00000375,  # $3.75 per 1M tokens
            'cache_read_cost_per_token': 0.0000003,    # $0.30 per 1M tokens
            'base_input_cost_per_token': 0.000003,     # $3.00 per 1M tokens
            'cache_ttl_minutes': 5,
            'min_cacheable_tokens': 1024,
            'note': 'Cache reads are 10x cheaper than base input. '
                    'First request pays write cost, subsequent reads save 90%.'
        }

    def generate_with_thinking(
        self,
        prompt: str,
        thinking_budget: int = 10000,
        max_tokens: int = 16000
    ) -> Tuple[str, str]:
        """Generate with extended thinking for complex tasks.

        Extended thinking allows Claude to reason through complex problems
        before responding, producing higher quality outputs for strategic
        decisions like roadmap planning and architecture design.

        Args:
            prompt: The prompt to generate from
            thinking_budget: Token budget for thinking (1000-100000)
            max_tokens: Maximum tokens in the response

        Returns:
            Tuple of (thinking_content, response_content)
        """
        max_retries = 5
        base_delay = 2.0
        max_delay = 60.0

        # Ensure thinking budget is within valid range
        thinking_budget = max(1000, min(100000, thinking_budget))

        for attempt in range(max_retries + 1):
            try:
                model_name = self.get_model_name()

                response = self.client.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    thinking={
                        "type": "enabled",
                        "budget_tokens": thinking_budget
                    },
                    messages=[{"role": "user", "content": prompt}]
                )

                thinking_content = ""
                response_content = ""

                for block in response.content:
                    if block.type == "thinking":
                        thinking_content = block.thinking
                    elif block.type == "text":
                        response_content = block.text

                # Log thinking usage
                if hasattr(response, 'usage'):
                    usage = response.usage
                    input_tokens = getattr(usage, 'input_tokens', 0)
                    output_tokens = getattr(usage, 'output_tokens', 0)
                    logger.info(
                        f"Extended thinking - input: {input_tokens}, output: {output_tokens}, "
                        f"thinking budget: {thinking_budget}"
                    )

                return thinking_content, response_content

            except Exception as e:
                error_msg = str(e)
                is_retryable = self._is_retryable_error(error_msg)

                if is_retryable and attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    logger.warning(
                        "Claude API temporarily overloaded (attempt %d/%d). Waiting %.1f seconds...",
                        attempt + 1, max_retries + 1, delay
                    )
                    time.sleep(delay)
                    continue

                self._handle_final_error(error_msg, attempt + 1, max_retries + 1)

        # Should never reach here, but return empty tuple for type safety
        return "", ""

    def generate_with_thinking_and_system(
        self,
        system_prompt: str,
        user_prompt: str,
        thinking_budget: int = 10000,
        cache_system: bool = True,
        max_tokens: int = 16000
    ) -> Tuple[str, str]:
        """Generate with extended thinking and cached system prompt.

        Combines extended thinking with prompt caching for complex items
        that need deep reasoning while maintaining context efficiency.

        Args:
            system_prompt: The system prompt to cache
            user_prompt: The user prompt
            thinking_budget: Token budget for thinking
            cache_system: Whether to cache the system prompt
            max_tokens: Maximum tokens in the response

        Returns:
            Tuple of (thinking_content, response_content)
        """
        max_retries = 5
        base_delay = 2.0
        max_delay = 60.0

        thinking_budget = max(1000, min(100000, thinking_budget))

        # Build system configuration
        system_config: Dict[str, Any] = {
            "type": "text",
            "text": system_prompt,
        }

        if cache_system:
            system_config["cache_control"] = {"type": "ephemeral"}

        for attempt in range(max_retries + 1):
            try:
                model_name = self.get_model_name()

                response = self.client.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    system=[system_config],
                    thinking={
                        "type": "enabled",
                        "budget_tokens": thinking_budget
                    },
                    messages=[{"role": "user", "content": user_prompt}]
                )

                thinking_content = ""
                response_content = ""

                for block in response.content:
                    if block.type == "thinking":
                        thinking_content = block.thinking
                    elif block.type == "text":
                        response_content = block.text

                # Log cache and thinking usage
                if hasattr(response, 'usage'):
                    usage = response.usage
                    cache_read = getattr(usage, 'cache_read_input_tokens', 0)
                    if cache_read:
                        logger.info(f"Cache read: {cache_read} tokens")

                return thinking_content, response_content

            except Exception as e:
                error_msg = str(e)
                is_retryable = self._is_retryable_error(error_msg)

                if is_retryable and attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    logger.warning(
                        "Claude API temporarily overloaded (attempt %d/%d). Waiting %.1f seconds...",
                        attempt + 1, max_retries + 1, delay
                    )
                    time.sleep(delay)
                    continue

                self._handle_final_error(error_msg, attempt + 1, max_retries + 1)

        return "", ""

    def get_thinking_pricing_info(self) -> Dict[str, Any]:
        """Get pricing information for extended thinking.

        Returns:
            Dictionary with thinking pricing details
        """
        return {
            'thinking_input_cost_per_token': 0.000003,   # Same as regular input
            'thinking_output_cost_per_token': 0.000015,  # Same as regular output
            'min_thinking_budget': 1000,
            'max_thinking_budget': 100000,
            'recommended_budgets': {
                'simple': 5000,
                'moderate': 10000,
                'complex': 20000,
                'strategic': 30000,
            },
            'note': 'Thinking tokens count toward output costs. '
                    'Higher budgets enable deeper reasoning for complex tasks.'
        }

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        tool_name: str = "create_roadmap_item",
        tool_description: str = "Create a structured roadmap item",
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """Generate structured output using Claude's tool use feature.

        This method uses Claude's tool use capability to enforce structured
        output that matches the provided JSON schema. This is more reliable
        than parsing free-form text responses.

        Args:
            prompt: The prompt describing what to generate
            schema: JSON schema defining the expected output structure
            tool_name: Name of the tool (used in the API call)
            tool_description: Description of what the tool does
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary containing the structured output

        Raises:
            ValueError: If no tool use is found in the response
        """
        max_retries = 5
        base_delay = 2.0
        max_delay = 60.0

        for attempt in range(max_retries + 1):
            try:
                model_name = self.get_model_name()

                response = self.client.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    tools=[{
                        "name": tool_name,
                        "description": tool_description,
                        "input_schema": schema
                    }],
                    tool_choice={"type": "tool", "name": tool_name},
                    messages=[{"role": "user", "content": prompt}]
                )

                # Extract structured data from tool use
                for block in response.content:
                    if block.type == "tool_use":
                        logger.debug(f"Structured output generated with tool: {tool_name}")
                        return block.input

                raise ValueError(f"No tool use found in response for {tool_name}")

            except ValueError:
                # Re-raise ValueError (no tool use) without retry
                raise

            except Exception as e:
                error_msg = str(e)
                is_retryable = self._is_retryable_error(error_msg)

                if is_retryable and attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    logger.warning(
                        "Claude API temporarily overloaded (attempt %d/%d). Waiting %.1f seconds...",
                        attempt + 1, max_retries + 1, delay
                    )
                    time.sleep(delay)
                    continue

                self._handle_final_error(error_msg, attempt + 1, max_retries + 1)

    def generate_structured_with_system(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        tool_name: str = "create_roadmap_item",
        tool_description: str = "Create a structured roadmap item",
        cache_system: bool = True,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """Generate structured output with a cached system prompt.

        Combines prompt caching with structured output for efficient
        batch generation of structured items.

        Args:
            system_prompt: The system prompt to cache
            user_prompt: The user prompt (varies per request)
            schema: JSON schema defining the expected output structure
            tool_name: Name of the tool
            tool_description: Description of the tool
            cache_system: Whether to enable caching on the system prompt
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary containing the structured output
        """
        max_retries = 5
        base_delay = 2.0
        max_delay = 60.0

        # Build system configuration with optional cache control
        system_config: Dict[str, Any] = {
            "type": "text",
            "text": system_prompt,
        }

        if cache_system:
            system_config["cache_control"] = {"type": "ephemeral"}

        for attempt in range(max_retries + 1):
            try:
                model_name = self.get_model_name()

                response = self.client.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    system=[system_config],
                    tools=[{
                        "name": tool_name,
                        "description": tool_description,
                        "input_schema": schema
                    }],
                    tool_choice={"type": "tool", "name": tool_name},
                    messages=[{"role": "user", "content": user_prompt}]
                )

                # Log cache usage if available
                if hasattr(response, 'usage'):
                    usage = response.usage
                    cache_creation = getattr(usage, 'cache_creation_input_tokens', 0)
                    cache_read = getattr(usage, 'cache_read_input_tokens', 0)
                    if cache_creation or cache_read:
                        logger.info(
                            f"Cache stats - created: {cache_creation}, read: {cache_read}"
                        )

                # Extract structured data from tool use
                for block in response.content:
                    if block.type == "tool_use":
                        return block.input

                raise ValueError(f"No tool use found in response for {tool_name}")

            except ValueError:
                raise

            except Exception as e:
                error_msg = str(e)
                is_retryable = self._is_retryable_error(error_msg)

                if is_retryable and attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    logger.warning(
                        "Claude API temporarily overloaded (attempt %d/%d). Waiting %.1f seconds...",
                        attempt + 1, max_retries + 1, delay
                    )
                    time.sleep(delay)
                    continue

                self._handle_final_error(error_msg, attempt + 1, max_retries + 1)


# =============================================================================
# Structured Output Schemas for Roadmap Items
# =============================================================================

TASK_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Brief title for the task"
        },
        "description": {
            "type": "string",
            "description": "Detailed description of what the task accomplishes"
        },
        "goal_description": {
            "type": "string",
            "description": "The specific goal this task achieves"
        },
        "benefits": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of benefits from completing this task"
        },
        "claude_code_prompt": {
            "type": "string",
            "description": "A prompt that can be used with Claude Code to implement this task"
        },
        "work_type": {
            "type": "string",
            "enum": ["implementation", "design", "research", "testing", "documentation", "configuration", "deployment"],
            "description": "The type of work this task involves"
        },
        "complexity": {
            "type": "string",
            "enum": ["simple", "moderate", "complex"],
            "description": "Complexity level of the task"
        },
        "duration_hours": {
            "type": "integer",
            "minimum": 1,
            "maximum": 40,
            "description": "Estimated hours to complete the task"
        },
        "priority": {
            "type": "string",
            "enum": ["Critical", "High", "Medium", "Low"],
            "description": "Priority level of the task"
        },
        "prerequisites": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of prerequisites that must be completed first"
        },
        "technical_requirements": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Technical requirements for implementing this task"
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tags for categorizing the task (e.g., 'backend', 'api', 'database')"
        }
    },
    "required": ["title", "description", "work_type", "complexity", "duration_hours"]
}

STORY_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Brief title for the user story"
        },
        "description": {
            "type": "string",
            "description": "Detailed description of the user story"
        },
        "user_value": {
            "type": "string",
            "description": "The value this story provides to users (As a user, I want...so that...)"
        },
        "acceptance_criteria": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of acceptance criteria that define when the story is complete"
        },
        "scope_in": {
            "type": "array",
            "items": {"type": "string"},
            "description": "What is explicitly included in this story's scope"
        },
        "scope_out": {
            "type": "array",
            "items": {"type": "string"},
            "description": "What is explicitly excluded from this story's scope"
        },
        "benefits": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Benefits of completing this story"
        },
        "technical_requirements": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Technical requirements for implementing this story"
        },
        "prerequisites": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Prerequisites that must be completed first"
        },
        "work_type": {
            "type": "string",
            "enum": ["feature", "enhancement", "bugfix", "refactoring", "research", "infrastructure"],
            "description": "The type of work this story involves"
        },
        "complexity": {
            "type": "string",
            "enum": ["simple", "moderate", "complex"],
            "description": "Complexity level of the story"
        },
        "priority": {
            "type": "string",
            "enum": ["Critical", "High", "Medium", "Low"],
            "description": "Priority level of the story"
        },
        "duration_hours": {
            "type": "integer",
            "minimum": 1,
            "maximum": 80,
            "description": "Estimated hours to complete the story"
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tags for categorizing the story"
        }
    },
    "required": ["title", "description", "user_value", "acceptance_criteria", "work_type"]
}

EPIC_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Brief title for the epic"
        },
        "description": {
            "type": "string",
            "description": "Detailed description of the epic"
        },
        "goals": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The goals this epic achieves"
        },
        "benefits": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Benefits of completing this epic"
        },
        "success_metrics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Metrics that define success for this epic"
        },
        "risks_and_mitigations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "risk": {"type": "string"},
                    "mitigation": {"type": "string"}
                },
                "required": ["risk", "mitigation"]
            },
            "description": "Potential risks and their mitigations"
        },
        "technical_requirements": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Technical requirements for this epic"
        },
        "prerequisites": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Prerequisites that must be completed first"
        },
        "work_type": {
            "type": "string",
            "enum": ["feature", "infrastructure", "platform", "integration", "security", "performance"],
            "description": "The type of work this epic involves"
        },
        "complexity": {
            "type": "string",
            "enum": ["simple", "moderate", "complex"],
            "description": "Complexity level of the epic"
        },
        "priority": {
            "type": "string",
            "enum": ["Critical", "High", "Medium", "Low"],
            "description": "Priority level"
        },
        "duration_hours": {
            "type": "integer",
            "minimum": 8,
            "maximum": 400,
            "description": "Estimated hours to complete"
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tags for categorizing the epic"
        }
    },
    "required": ["title", "description", "goals", "work_type"]
}

MILESTONE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Brief title for the milestone"
        },
        "description": {
            "type": "string",
            "description": "Detailed description of the milestone"
        },
        "goal": {
            "type": "string",
            "description": "The primary goal of this milestone"
        },
        "key_deliverables": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Key deliverables that mark completion of this milestone"
        },
        "benefits": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Benefits of completing this milestone"
        },
        "success_criteria": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Criteria that define success for this milestone"
        },
        "risks_if_delayed": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Risks if this milestone is delayed"
        },
        "technical_requirements": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Technical requirements for this milestone"
        },
        "prerequisites": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Prerequisites that must be completed first"
        },
        "work_type": {
            "type": "string",
            "enum": ["foundation", "feature", "release", "infrastructure", "integration"],
            "description": "The type of work this milestone represents"
        },
        "complexity": {
            "type": "string",
            "enum": ["simple", "moderate", "complex"],
            "description": "Complexity level of the milestone"
        },
        "priority": {
            "type": "string",
            "enum": ["Critical", "High", "Medium", "Low"],
            "description": "Priority level"
        },
        "duration_hours": {
            "type": "integer",
            "minimum": 40,
            "maximum": 2000,
            "description": "Estimated hours to complete"
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tags for categorizing the milestone"
        }
    },
    "required": ["title", "description", "goal", "key_deliverables", "work_type"]
}