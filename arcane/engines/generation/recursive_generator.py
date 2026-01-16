"""Recursive roadmap generator that processes items individually."""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt

from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task
from arcane.items.base import Item, ItemStatus
from arcane.engines.parsing.outline_parser import OutlineParser
from arcane.engines.generation.helpers.context_summarizer import ContextSummarizer
from arcane.clients.model_selector import ModelSelector, ModelConfig
from arcane.clients.factory import LLMClientFactory
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class RecursiveRoadmapGenerator:
    """Generates roadmap content by processing each item individually."""

    def __init__(self, llm_client, model_mode: str = 'tiered'):
        """Initialize the recursive generator.

        Args:
            llm_client: Default LLM client to use
            model_mode: Model selection mode ('tiered', 'premium', 'economy', 'standard')
        """
        self.llm_client = llm_client
        self.console = Console()
        self.outline_parser = OutlineParser()
        self.context_summarizer = ContextSummarizer(llm_client)

        # Initialize model selector for tiered model usage
        self.model_mode = model_mode
        provider = self._get_provider_from_client(llm_client)
        self.model_selector = ModelSelector(provider=provider, mode=model_mode)

        # Cache for LLM clients by model name
        self._client_cache: Dict[str, Any] = {}
        self._client_cache['default'] = llm_client

        # Track generation for context building
        self.generated_items: List[Item] = []

        # Prompt caching settings
        self._use_prompt_caching = True
        self._cached_system_prompt: Optional[str] = None
        self._cache_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'requests_with_caching': 0
        }

        # Extended thinking settings
        self._use_extended_thinking = True
        self._thinking_item_types = {'outline', 'milestone'}
        self._thinking_budgets = {
            'outline': 15000,    # Higher budget for strategic outline generation
            'milestone': 10000,  # Milestones need good reasoning
            'epic': 8000,        # Optional - epics with complexity flag
        }
        self._thinking_stats = {
            'items_with_thinking': 0,
            'total_thinking_tokens': 0,
        }
        self._stored_thinking: Dict[str, str] = {}  # Store thinking for debug/review

    def _get_provider_from_client(self, llm_client) -> str:
        """Extract provider name from LLM client.

        Args:
            llm_client: LLM client instance

        Returns:
            Provider name string
        """
        if hasattr(llm_client, 'provider'):
            return llm_client.provider
        # Fallback based on class name
        class_name = type(llm_client).__name__.lower()
        if 'claude' in class_name:
            return 'claude'
        elif 'openai' in class_name:
            return 'openai'
        elif 'gemini' in class_name:
            return 'gemini'
        return 'claude'  # Default fallback

    def _get_client_for_item(self, item_type: str):
        """Get appropriate LLM client for an item type.

        Uses the model selector to determine the best model for the item type
        and returns a cached client for that model.

        Args:
            item_type: Type of item being generated (e.g., 'milestone', 'task')

        Returns:
            LLM client appropriate for this item type
        """
        # In non-tiered modes, just use default client
        if self.model_mode != 'tiered':
            return self.llm_client

        # Get the appropriate model config for this item type
        model_config = self.model_selector.get_model_for_item(item_type)
        cache_key = model_config.model_name

        # Check cache first
        if cache_key not in self._client_cache:
            logger.debug(f"Creating new client for model: {model_config.model_name}")
            self._client_cache[cache_key] = LLMClientFactory.create_cached(
                model_config.provider,
                model_config.model_name
            )

        return self._client_cache[cache_key]

    def get_model_usage_stats(self) -> Dict[str, Any]:
        """Get statistics on model usage during generation.

        Returns:
            Dictionary with model usage statistics
        """
        return self.model_selector.get_usage_stats()

    def set_prompt_caching(self, enabled: bool) -> None:
        """Enable or disable prompt caching for Claude provider.

        Args:
            enabled: Whether to enable prompt caching
        """
        self._use_prompt_caching = enabled
        logger.info(f"Prompt caching {'enabled' if enabled else 'disabled'}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get prompt caching statistics.

        Returns:
            Dictionary with cache statistics
        """
        return self._cache_stats.copy()

    def set_extended_thinking(self, enabled: bool) -> None:
        """Enable or disable extended thinking for complex items.

        Args:
            enabled: Whether to enable extended thinking
        """
        self._use_extended_thinking = enabled
        logger.info(f"Extended thinking {'enabled' if enabled else 'disabled'}")

    def configure_thinking_items(
        self,
        item_types: Optional[List[str]] = None,
        budgets: Optional[Dict[str, int]] = None
    ) -> None:
        """Configure which item types use extended thinking and their budgets.

        Args:
            item_types: List of item types that should use thinking
            budgets: Dictionary mapping item types to thinking budgets
        """
        if item_types is not None:
            self._thinking_item_types = set(t.lower() for t in item_types)
            logger.info(f"Thinking enabled for: {self._thinking_item_types}")

        if budgets is not None:
            self._thinking_budgets.update(budgets)
            logger.info(f"Thinking budgets updated: {budgets}")

    def get_thinking_stats(self) -> Dict[str, Any]:
        """Get extended thinking statistics.

        Returns:
            Dictionary with thinking statistics
        """
        return {
            **self._thinking_stats,
            'stored_thinking_count': len(self._stored_thinking)
        }

    def get_stored_thinking(self, item_id: str) -> Optional[str]:
        """Get stored thinking content for an item.

        Args:
            item_id: The item ID to get thinking for

        Returns:
            Thinking content or None if not stored
        """
        return self._stored_thinking.get(item_id)

    def get_all_stored_thinking(self) -> Dict[str, str]:
        """Get all stored thinking content.

        Returns:
            Dictionary mapping item IDs to thinking content
        """
        return self._stored_thinking.copy()

    def clear_stored_thinking(self) -> int:
        """Clear all stored thinking content.

        Returns:
            Number of items cleared
        """
        count = len(self._stored_thinking)
        self._stored_thinking.clear()
        return count

    def _should_use_thinking(self, item: Item) -> bool:
        """Determine if an item should use extended thinking.

        Args:
            item: The item to check

        Returns:
            True if extended thinking should be used
        """
        if not self._use_extended_thinking:
            return False

        item_type = item.item_type.lower()

        # Check if item type is configured for thinking
        if item_type in self._thinking_item_types:
            return True

        # Special case: complex epics can use thinking
        if item_type == 'epic' and getattr(item, 'complexity', '') == 'complex':
            return True

        return False

    def _get_thinking_budget(self, item: Item) -> int:
        """Get the thinking budget for an item.

        Args:
            item: The item to get budget for

        Returns:
            Thinking token budget
        """
        item_type = item.item_type.lower()
        return self._thinking_budgets.get(item_type, 10000)

    def _generate_with_thinking(
        self,
        item: Item,
        prompt: str,
        debug_mode: bool = False
    ) -> str:
        """Generate content using extended thinking.

        Args:
            item: The item being generated
            prompt: The generation prompt
            debug_mode: Whether to log thinking content

        Returns:
            Generated response content
        """
        client = self._get_client_for_item(item.item_type.lower())

        # Check if client supports thinking
        if not hasattr(client, 'generate_with_thinking'):
            logger.debug(f"Client doesn't support thinking, falling back to regular generation")
            return client.generate(prompt)

        budget = self._get_thinking_budget(item)

        logger.info(f"Using extended thinking for {item.item_type} {item.id} "
                   f"(budget: {budget} tokens)")

        thinking, response = client.generate_with_thinking(
            prompt=prompt,
            thinking_budget=budget
        )

        # Store thinking for later review
        if thinking:
            self._stored_thinking[item.id] = thinking
            self._thinking_stats['items_with_thinking'] += 1

            # Log preview if debug mode
            if debug_mode:
                thinking_preview = thinking[:500] + "..." if len(thinking) > 500 else thinking
                logger.debug(f"Thinking for {item.id}:\n{thinking_preview}")

        return response

    def _build_full_roadmap_context(self, milestones: List[Milestone]) -> str:
        """Build full roadmap context for caching.

        Creates a comprehensive context string that includes the entire
        roadmap structure. This context is designed to be cached and
        reused across multiple generation requests.

        Args:
            milestones: List of milestones in the roadmap

        Returns:
            Full roadmap context string
        """
        lines = ["=== ROADMAP STRUCTURE ==="]

        # Add overview
        total_epics = sum(len(m.get_children_by_type('Epic')) for m in milestones)
        total_stories = sum(
            len(e.get_children_by_type('Story'))
            for m in milestones
            for e in m.get_children_by_type('Epic')
        )
        total_tasks = sum(
            len(s.get_children_by_type('Task'))
            for m in milestones
            for e in m.get_children_by_type('Epic')
            for s in e.get_children_by_type('Story')
        )

        lines.append(f"Total: {len(milestones)} milestones, {total_epics} epics, "
                    f"{total_stories} stories, {total_tasks} tasks")
        lines.append("")

        # Add detailed structure
        for milestone in milestones:
            m_title = self._get_item_title(milestone)
            lines.append(f"## Milestone {milestone.id}: {m_title}")
            if milestone.outline_description:
                lines.append(f"   Purpose: {milestone.outline_description}")

            for epic in milestone.get_children_by_type('Epic'):
                e_title = self._get_item_title(epic)
                lines.append(f"  ### Epic {epic.id}: {e_title}")
                if epic.outline_description:
                    lines.append(f"      Purpose: {epic.outline_description}")

                for story in epic.get_children_by_type('Story'):
                    s_title = self._get_item_title(story)
                    lines.append(f"    #### Story {story.id}: {s_title}")
                    if story.outline_description:
                        lines.append(f"        Purpose: {story.outline_description}")

                    for task in story.get_children_by_type('Task'):
                        t_title = self._get_item_title(task)
                        lines.append(f"      - Task {task.id}: {t_title}")

        return "\n".join(lines)

    def _generate_with_caching(
        self,
        item: Item,
        project_context: str,
        milestones: List[Milestone],
        parent_context: str = "",
        additional_context: str = ""
    ) -> str:
        """Generate content for an item using prompt caching.

        This method uses Claude's prompt caching feature to cache the
        system prompt containing the roadmap context. Subsequent requests
        reuse the cached context, reducing costs by up to 90%.

        Args:
            item: The item to generate content for
            project_context: The project idea/context
            milestones: Full list of milestones for context
            parent_context: Context from parent items
            additional_context: Any additional context to include

        Returns:
            Generated content from the LLM
        """
        client = self._get_client_for_item(item.item_type.lower())

        # Check if client supports caching (only Claude)
        if not hasattr(client, 'generate_with_cached_system'):
            # Fallback to regular generation for non-Claude clients
            prompt = item.generate_prompt(project_context, parent_context, additional_context)
            return client.generate(prompt)

        # Build or reuse cached system prompt
        if self._cached_system_prompt is None:
            roadmap_context = self._build_full_roadmap_context(milestones)
            self._cached_system_prompt = client.create_cacheable_context(roadmap_context)
            self._cache_stats['cache_misses'] += 1
            logger.debug("Built new cacheable system prompt")
        else:
            self._cache_stats['cache_hits'] += 1
            logger.debug("Reusing cached system prompt")

        # Build user prompt (this varies per item)
        user_prompt = self._build_item_user_prompt(
            item, project_context, parent_context, additional_context
        )

        self._cache_stats['requests_with_caching'] += 1

        # Generate with cached system prompt
        return client.generate_with_cached_system(
            system_prompt=self._cached_system_prompt,
            user_prompt=user_prompt,
            cache_system=self._use_prompt_caching
        )

    def _build_item_user_prompt(
        self,
        item: Item,
        project_context: str,
        parent_context: str,
        additional_context: str
    ) -> str:
        """Build the user prompt for an item (varies per request).

        Args:
            item: The item to generate content for
            project_context: The project idea/context
            parent_context: Context from parent items
            additional_context: Any additional context

        Returns:
            User prompt string
        """
        lines = [f"Generate content for {item.item_type} {item.id}: {self._get_item_title(item)}"]

        if project_context:
            lines.append(f"\nProject Context: {project_context}")

        if parent_context:
            lines.append(f"\nParent Context: {parent_context}")

        if additional_context:
            lines.append(f"\nAdditional Context:\n{additional_context}")

        # Add generation status context
        lines.append(f"\nGeneration Status:")
        lines.append(f"- Currently generating: {item.item_type} {item.id}")

        if self.generated_items:
            completed = [f"{i.item_type} {i.id}" for i in self.generated_items[-5:]]
            lines.append(f"- Recently completed: {', '.join(completed)}")

        # Add item-specific instructions
        lines.append(f"\n{item.get_generation_instructions()}")

        return "\n".join(lines)

    def invalidate_cache(self) -> None:
        """Invalidate the cached system prompt.

        Call this when the roadmap structure changes significantly
        and the cached context needs to be rebuilt.
        """
        self._cached_system_prompt = None
        logger.info("Prompt cache invalidated")

    def generate_from_outline(self, outline_content: str, idea_content: str, interactive_mode: bool = False) -> List[Milestone]:
        """Generate complete roadmap from outline by processing each item recursively."""

        # Parse outline into item objects
        self.console.print("\n[cyan]📊 Parsing outline structure...[/cyan]")
        milestones = self.outline_parser.parse_outline(outline_content)

        # Validate structure
        issues = self.outline_parser.validate_structure(milestones)
        if issues:
            self.console.print("[red]❌ Structure validation issues found:[/red]")
            for issue in issues:
                self.console.print(f"[red]  • {issue}[/red]")
            return milestones

        # Show structure summary
        item_counts = self.outline_parser.count_items(milestones)
        self.console.print(f"[green]✅ Parsed {item_counts['milestones']} milestones, "
                          f"{item_counts['epics']} epics, {item_counts['stories']} stories, "
                          f"{item_counts['tasks']} tasks[/green]")

        # Process idea content (simplified processing)
        project_context = f"Project Idea: {idea_content}"

        # Generate content for each item
        self._generate_all_items(milestones, project_context, interactive_mode)

        return milestones

    def generate_all_with_cascading_context(
        self,
        milestones: List[Milestone],
        project_context: str,
        interactive_mode: bool = False
    ) -> None:
        """Generate all items with cascading context injection.

        This method generates items in order, building context from previously
        generated items to maintain consistency across the roadmap.
        """
        # Reset context tracking
        self.generated_items = []
        self.context_summarizer.clear_cache()

        # Build generation order
        generation_order = self._build_generation_order(milestones)
        total_items = len(generation_order)

        self.console.print(f"\n[cyan]🔄 Generating {total_items} items with cascading context...[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False
        ) as progress:

            task = progress.add_task("Generating...", total=total_items)

            for item in generation_order:
                try:
                    self._generate_item_with_cascading_context(
                        item,
                        project_context,
                        milestones,
                        progress,
                        task,
                        interactive_mode
                    )

                    # Track generated item for future context
                    self.generated_items.append(item)

                    progress.advance(task)

                except KeyboardInterrupt:
                    self.console.print("[yellow]⚠️ Generation interrupted by user[/yellow]")
                    break
                except Exception as e:
                    logger.error(f"Error generating {item.item_type} {item.id}: {e}")
                    self.console.print(f"\n[red]❌ Error generating {item.item_type} {item.id}: {str(e)}[/red]")

                    if Confirm.ask(f"[yellow]Skip {item.item_type} {item.id} and continue?[/yellow]"):
                        item.update_generation_status(ItemStatus.SKIPPED)
                        progress.advance(task)
                        continue
                    else:
                        self.console.print("[red]🛑 Generation stopped[/red]")
                        break

    def _build_generation_order(self, milestones: List[Milestone]) -> List[Item]:
        """Build generation order: milestones -> epics -> stories (with tasks)."""
        order = []

        for milestone in milestones:
            order.append(milestone)

            for epic in milestone.get_children_by_type('Epic'):
                order.append(epic)

                for story in epic.get_children_by_type('Story'):
                    order.append(story)
                    # Tasks are generated with their stories

        return order

    def _generate_item_with_cascading_context(
        self,
        item: Item,
        project_context: str,
        milestones: List[Milestone],
        progress: Progress,
        task,
        interactive_mode: bool
    ) -> None:
        """Generate a single item with full cascading context."""
        item_title = self._get_item_title(item)

        progress.update(
            task,
            description=f"Generating {item.item_type} {item.id}: {item_title}"
        )

        item.update_generation_status(ItemStatus.GENERATING)

        # Use two-pass generation for stories
        if isinstance(item, Story):
            self._generate_story_two_pass(
                item,
                project_context,
                milestones,
                progress,
                task,
                interactive_mode
            )
            return

        # Build cascading context from summarizer
        cascading_context = self.context_summarizer.get_full_cascading_context(item)

        # Build parent context with content summaries
        parent_context = self._build_parent_context_with_summaries(item)

        # Build roadmap overview with generation status
        roadmap_overview = self._build_roadmap_overview_with_status(milestones, item)

        # Combine all context layers
        full_context = self._combine_context_layers(
            roadmap_context=roadmap_overview,
            cascading_context=cascading_context,
            semantic_context=self._build_semantic_context(item) if item.has_semantic_context() else ""
        )

        # Generate prompt with enhanced context
        prompt = item.generate_prompt(project_context, parent_context, full_context)

        # Get appropriate client for this item type
        client = self._get_client_for_item(item.item_type.lower())

        # Call LLM with appropriate model
        response = client.generate(prompt)

        # Parse response and update item
        item.parse_content(response)
        item.update_generation_status(ItemStatus.GENERATED)

        # Interactive confirmation with context info
        if interactive_mode:
            self._show_item_confirmation_with_context(item, cascading_context, progress, task)

    def _generate_story_two_pass(
        self,
        story: Story,
        project_context: str,
        milestones: List[Milestone],
        progress: Progress,
        task,
        interactive_mode: bool
    ) -> None:
        """Generate story using two-pass approach.

        Pass 1: Generate story description and acceptance criteria
        Pass 2: Generate tasks with full story context

        This approach allows tasks to be generated with complete knowledge
        of the story's acceptance criteria, ensuring proper coverage.
        """
        story_title = self._get_item_title(story)

        # Build contexts
        cascading_context = self.context_summarizer.get_full_cascading_context(story)
        roadmap_overview = self._build_roadmap_overview_with_status(milestones, story)

        # Get parent epic context
        epic_context = ""
        if story.parent:
            epic = story.parent
            epic_context = f"Epic {epic.id}: {self._get_item_title(epic)}"
            if epic.description:
                epic_context += f"\n{epic.description}"

        # Get semantic context
        semantic_description = ""
        if story.has_semantic_context():
            semantic_description = story.get_semantic_context()

        # === PASS 1: Generate description and acceptance criteria ===
        progress.update(
            task,
            description=f"[Pass 1/2] Story {story.id}: {story_title} - Description"
        )

        pass1_prompt = story.generate_description_prompt(
            project_context=project_context,
            epic_context=epic_context,
            cascading_context=cascading_context,
            roadmap_overview=roadmap_overview,
            semantic_description=semantic_description
        )

        logger.debug(f"Story {story.id} Pass 1 prompt length: {len(pass1_prompt)}")

        # Get client for story description (standard tier)
        story_client = self._get_client_for_item('story_description')

        # Call LLM for Pass 1
        pass1_response = story_client.generate(pass1_prompt)

        # Parse Pass 1 response
        story.parse_description_content(pass1_response)

        logger.info(
            f"Story {story.id} Pass 1 complete: "
            f"{len(story.acceptance_criteria)} AC, "
            f"{len(story.scope_in)} in-scope, "
            f"{len(story.scope_out)} out-of-scope"
        )

        # === PASS 2: Generate tasks with full story context ===
        progress.update(
            task,
            description=f"[Pass 2/2] Story {story.id}: {story_title} - Tasks"
        )

        # Get sibling story context (other stories in same epic)
        sibling_context = self.context_summarizer.get_sibling_context(story)

        pass2_prompt = story.generate_tasks_prompt(
            cascading_context=cascading_context,
            sibling_context=sibling_context,
            roadmap_overview=roadmap_overview
        )

        logger.debug(f"Story {story.id} Pass 2 prompt length: {len(pass2_prompt)}")

        # Get client for task generation (economy tier)
        task_client = self._get_client_for_item('story_tasks')

        # Call LLM for Pass 2
        pass2_response = task_client.generate(pass2_prompt)

        # Parse Pass 2 response (tasks)
        story.parse_tasks_content(pass2_response)

        # Store combined content for export
        story.content = f"{pass1_response}\n\n---\n\n{pass2_response}"

        # Mark story as generated
        story.update_generation_status(ItemStatus.GENERATED)

        # Update task statuses
        for task_item in story.get_children_by_type('Task'):
            if task_item.generation_status == ItemStatus.PENDING:
                task_item.update_generation_status(ItemStatus.GENERATED)

        logger.info(
            f"Story {story.id} two-pass complete: "
            f"{len(story.get_children_by_type('Task'))} tasks generated"
        )

        # Interactive confirmation
        if interactive_mode:
            self._show_story_two_pass_confirmation(story, progress, task)

    def _show_story_two_pass_confirmation(
        self,
        story: Story,
        progress: Progress,
        task
    ) -> None:
        """Show two-pass story generation results for confirmation."""
        progress.update(task, description=f"✅ Generated Story {story.id}")

        self.console.print(
            f"\n[bold green]✅ Story {story.id}: {self._get_item_title(story)}[/bold green]"
        )

        # Show Pass 1 results
        self.console.print(f"\n[cyan]Pass 1 - Description:[/cyan]")
        if story.description:
            desc_preview = story.description[:200] + "..." if len(story.description) > 200 else story.description
            self.console.print(f"[dim]{desc_preview}[/dim]")

        self.console.print(f"\n[cyan]Acceptance Criteria ({len(story.acceptance_criteria)}):[/cyan]")
        for i, ac in enumerate(story.acceptance_criteria[:4], 1):
            self.console.print(f"[dim]  AC{i}: {ac[:80]}...[/dim]" if len(ac) > 80 else f"[dim]  AC{i}: {ac}[/dim]")
        if len(story.acceptance_criteria) > 4:
            self.console.print(f"[dim]  ... and {len(story.acceptance_criteria) - 4} more[/dim]")

        # Show Pass 2 results
        tasks = story.get_children_by_type('Task')
        self.console.print(f"\n[cyan]Pass 2 - Tasks ({len(tasks)}):[/cyan]")
        for task_item in tasks[:4]:
            self.console.print(f"[dim]  • Task {task_item.id}: {self._get_item_title(task_item)}[/dim]")
        if len(tasks) > 4:
            self.console.print(f"[dim]  ... and {len(tasks) - 4} more[/dim]")

        # Confirmation loop
        while True:
            choice = Prompt.ask(
                "[cyan]Action?[/cyan]",
                choices=["continue", "view_full", "quit"],
                default="continue"
            )

            if choice == "continue":
                break
            elif choice == "view_full":
                self.console.print(f"\n[bold]Full Story Content:[/bold]")
                self.console.print(f"[dim]Description: {story.description}[/dim]")
                self.console.print(f"\n[dim]User Value: {story.user_value}[/dim]")
                self.console.print(f"\n[dim]Acceptance Criteria:[/dim]")
                for i, ac in enumerate(story.acceptance_criteria, 1):
                    self.console.print(f"[dim]  AC{i}: {ac}[/dim]")
                self.console.print(f"\n[dim]Scope In: {story.scope_in}[/dim]")
                self.console.print(f"\n[dim]Scope Out: {story.scope_out}[/dim]")
            elif choice == "quit":
                raise KeyboardInterrupt("User quit")

    def _build_parent_context_with_summaries(self, item: Item) -> str:
        """Build parent context including content summaries."""
        lines = []
        current = item.parent
        depth = 0

        while current and depth < 3:
            # Get summary if generated
            if current.generation_status == ItemStatus.GENERATED:
                summary = self.context_summarizer.get_summary(current)
                if summary:
                    lines.append(summary.summary_text)
                else:
                    # Fallback to basic info
                    lines.append(f"{current.item_type} {current.id}: {self._get_item_title(current)}")
            else:
                lines.append(f"{current.item_type} {current.id}: {self._get_item_title(current)} (not yet generated)")

            current = current.parent
            depth += 1

        # Reverse for top-down order
        lines.reverse()

        if lines:
            return "Parent Hierarchy:\n" + "\n".join([f"  {'  ' * i}→ {line}" for i, line in enumerate(lines)])
        return "No parent context"

    def _build_roadmap_overview_with_status(self, milestones: List[Milestone], current_item: Item) -> str:
        """Build a roadmap overview showing what's been generated with key decisions."""
        lines = ["=== ROADMAP GENERATION STATUS ==="]

        for milestone in milestones:
            status = self._get_status_icon(milestone)
            lines.append(f"{status} Milestone {milestone.id}: {self._get_item_title(milestone)}")

            # If generated, include key decision summary
            if milestone.generation_status == ItemStatus.GENERATED:
                summary = self.context_summarizer.get_summary(milestone)
                if summary and summary.key_decisions:
                    lines.append(f"     Key decisions: {'; '.join(summary.key_decisions[:2])}")

            for epic in milestone.get_children_by_type('Epic'):
                status = self._get_status_icon(epic)
                lines.append(f"  {status} Epic {epic.id}: {self._get_item_title(epic)}")

                if epic.generation_status == ItemStatus.GENERATED:
                    summary = self.context_summarizer.get_summary(epic)
                    if summary and summary.technical_choices:
                        lines.append(f"       Tech: {', '.join(summary.technical_choices[:2])}")

                for story in epic.get_children_by_type('Story'):
                    status = self._get_status_icon(story)
                    is_current = " ← CURRENT" if story.id == current_item.id else ""
                    lines.append(f"    {status} Story {story.id}: {self._get_item_title(story)}{is_current}")

        lines.append(f"\nCurrently generating: {current_item.item_type} {current_item.id}")

        return "\n".join(lines)

    def _combine_context_layers(
        self,
        roadmap_context: str,
        cascading_context: str,
        semantic_context: str
    ) -> str:
        """Combine all context layers into a single context block."""
        sections = []

        if roadmap_context:
            sections.append(roadmap_context)

        if cascading_context and cascading_context != "No cascading context available":
            sections.append("\n" + cascading_context)

        if semantic_context:
            sections.append("\n" + semantic_context)

        # Add consistency requirements
        sections.append("""
=== CONSISTENCY REQUIREMENTS ===
Your generation MUST:
- Use technologies mentioned in earlier decisions
- Reference completed work appropriately
- Not duplicate functionality from sibling items
- Build logically on parent item's deliverables
""")

        return "\n".join(sections)

    def _get_status_icon(self, item: Item) -> str:
        """Get status icon for an item."""
        status_icons = {
            ItemStatus.GENERATED: "✅",
            ItemStatus.GENERATING: "🔄",
            ItemStatus.PENDING: "⏳",
            ItemStatus.SKIPPED: "⏭️",
            ItemStatus.FAILED: "❌",
            ItemStatus.NOT_STARTED: "⏳",
        }
        return status_icons.get(item.generation_status, "⏳")

    def _get_item_title(self, item: Item) -> str:
        """Extract clean title from item name."""
        if ': ' in item.name:
            return item.name.split(': ', 1)[-1]
        return item.name

    def _show_item_confirmation_with_context(
        self,
        item: Item,
        context_used: str,
        progress: Progress,
        task
    ) -> None:
        """Show generated item with context information for confirmation."""
        progress.update(task, description=f"✅ Generated {item.item_type} {item.id}")

        self.console.print(f"\n[bold green]✅ Generated {item.item_type} {item.id}: {self._get_item_title(item)}[/bold green]")

        # Show preview
        if item.content:
            preview = item.content[:400] + "..." if len(item.content) > 400 else item.content
            self.console.print(f"[dim]Preview:\n{preview}[/dim]")

        # Show what context was used
        context_preview = context_used[:300] + "..." if len(context_used) > 300 else context_used
        self.console.print(f"\n[cyan]Context used for generation:[/cyan]")
        self.console.print(f"[dim]{context_preview}[/dim]")

        # Confirmation loop
        while True:
            choice = Prompt.ask(
                "[cyan]Action?[/cyan]",
                choices=["continue", "regenerate", "view_full", "quit"],
                default="continue"
            )

            if choice == "continue":
                break
            elif choice == "view_full":
                self.console.print(f"\n[bold]Full Content:[/bold]\n{item.content}")
            elif choice == "regenerate":
                self.console.print("[yellow]🔄 Regenerating...[/yellow]")
                item.update_generation_status(ItemStatus.PENDING)
                # Would need to re-call generation here
                break
            elif choice == "quit":
                raise KeyboardInterrupt("User quit")

    def _generate_all_items(self, milestones: List[Milestone], project_context: str, interactive_mode: bool = False) -> None:
        """Generate content for all items in the roadmap."""

        # Get generation order (milestones, then epics, then stories+tasks)
        generation_items = []
        for milestone in milestones:
            generation_items.append(milestone)
            for epic in milestone.get_children_by_type('Epic'):
                generation_items.append(epic)
                for story in epic.get_children_by_type('Story'):
                    generation_items.append(story)

        total_items = len(generation_items)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False
        ) as progress:

            task = progress.add_task(
                "Generating roadmap content...",
                total=total_items
            )

            for item in generation_items:
                try:
                    self._generate_single_item(item, project_context, progress, task, milestones, interactive_mode)
                    progress.advance(task)

                except Exception as e:
                    self.console.print(f"\n[red]❌ Error generating {item.item_type} {item.id}: {str(e)}[/red]")

                    # Ask user what to do
                    if Confirm.ask(f"[yellow]Skip {item.item_type} {item.id} and continue?[/yellow]"):
                        item.update_generation_status(ItemStatus.SKIPPED)
                        self.console.print(f"[yellow]⏭️  Skipped {item.item_type} {item.id}[/yellow]")
                        progress.advance(task)
                        continue
                    else:
                        self.console.print("[red]🛑 Generation stopped[/red]")
                        break

    def _generate_single_item(self, item: Item, project_context: str, progress: Progress, task, milestones: List[Milestone], interactive_mode: bool = False) -> None:
        """Generate content for a single item with full roadmap context."""

        # Update progress description
        progress.update(task, description=f"Generating {item.item_type} {item.id}: {item.name.split(': ', 1)[-1] if ': ' in item.name else item.name}")

        # Mark as generating
        item.update_generation_status(ItemStatus.GENERATING)

        # Build comprehensive context
        parent_context = None
        if item.parent:
            parent_context = f"{item.parent.item_type} {item.parent.id}: {item.parent.name.split(': ', 1)[-1] if ': ' in item.parent.name else item.parent.name}"

        # Build full roadmap context for better coherence
        roadmap_context = self._build_roadmap_context(milestones, item)

        # Add semantic context if available
        if item.has_semantic_context():
            semantic_context = self._build_semantic_context(item)
            roadmap_context = f"{roadmap_context}\n\n{semantic_context}"

        # Generate prompt with enhanced context
        prompt = item.generate_prompt(project_context, parent_context, roadmap_context)

        # Get appropriate client for this item type
        client = self._get_client_for_item(item.item_type.lower())

        # Call LLM with appropriate model
        response = client.generate(prompt)

        # Parse response and update item
        item.parse_content(response)

        # For stories, also update their tasks from the response
        if isinstance(item, Story):
            # Tasks are automatically updated by the story's parse_content method
            for task_item in item.get_children_by_type('Task'):
                if task_item.generation_status == ItemStatus.PENDING:
                    task_item.update_generation_status(ItemStatus.GENERATED)

        # Show generated content and ask for user confirmation (if interactive mode)
        if interactive_mode:
            self._show_item_confirmation(item, progress, task)

    def get_generation_summary(self, milestones: List[Milestone]) -> Dict[str, Any]:
        """Get summary of generation results."""
        summary = {
            'total_items': 0,
            'generated': 0,
            'failed': 0,
            'skipped': 0,
            'pending': 0,
            'by_type': {
                'Milestone': {'total': 0, 'generated': 0, 'failed': 0, 'skipped': 0},
                'Epic': {'total': 0, 'generated': 0, 'failed': 0, 'skipped': 0},
                'Story': {'total': 0, 'generated': 0, 'failed': 0, 'skipped': 0},
                'Task': {'total': 0, 'generated': 0, 'failed': 0, 'skipped': 0}
            }
        }

        for milestone in milestones:
            self._count_item_status(milestone, summary)
            for epic in milestone.get_children_by_type('Epic'):
                self._count_item_status(epic, summary)
                for story in epic.get_children_by_type('Story'):
                    self._count_item_status(story, summary)
                    for task in story.get_children_by_type('Task'):
                        self._count_item_status(task, summary)

        return summary

    def _count_item_status(self, item: Item, summary: Dict[str, Any]) -> None:
        """Count item status for summary."""
        summary['total_items'] += 1
        summary['by_type'][item.item_type]['total'] += 1

        if item.generation_status == ItemStatus.GENERATED:
            summary['generated'] += 1
            summary['by_type'][item.item_type]['generated'] += 1
        elif item.generation_status == ItemStatus.FAILED:
            summary['failed'] += 1
            summary['by_type'][item.item_type]['failed'] += 1
        elif item.generation_status == ItemStatus.SKIPPED:
            summary['skipped'] += 1
            summary['by_type'][item.item_type]['skipped'] += 1
        else:
            summary['pending'] += 1

    def export_to_markdown(self, milestones: List[Milestone]) -> str:
        """Export generated roadmap to markdown format."""
        lines = []

        for milestone in milestones:
            if milestone.content:
                lines.append(milestone.content)
                lines.append("")

            for epic in milestone.get_children_by_type('Epic'):
                if epic.content:
                    lines.append(epic.content)
                    lines.append("")

                for story in epic.get_children_by_type('Story'):
                    if story.content:
                        lines.append(story.content)
                        lines.append("")

        return "\n".join(lines)

    def save_progress(self, milestones: List[Milestone], filepath: str) -> None:
        """Save current generation progress to file (for future resume functionality)."""
        import json
        from datetime import datetime

        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'milestones': []
        }

        for milestone in milestones:
            milestone_data = {
                'id': milestone.id,
                'name': milestone.name,
                'status': milestone.generation_status.value,
                'content': milestone.content,
                'epics': []
            }

            for epic in milestone.get_children_by_type('Epic'):
                epic_data = {
                    'id': epic.id,
                    'name': epic.name,
                    'status': epic.generation_status.value,
                    'content': epic.content,
                    'stories': []
                }

                for story in epic.get_children_by_type('Story'):
                    story_data = {
                        'id': story.id,
                        'name': story.name,
                        'status': story.generation_status.value,
                        'content': story.content,
                        'tasks': []
                    }

                    for task in story.get_children_by_type('Task'):
                        task_data = {
                            'id': task.id,
                            'name': task.name,
                            'status': task.generation_status.value,
                            'content': task.content
                        }
                        story_data['tasks'].append(task_data)

                    epic_data['stories'].append(story_data)
                milestone_data['epics'].append(epic_data)
            progress_data['milestones'].append(milestone_data)

        with open(filepath, 'w') as f:
            json.dump(progress_data, f, indent=2)

        self.console.print(f"[green]💾 Progress saved to {filepath}[/green]")

    def _build_roadmap_context(self, milestones: List[Milestone], current_item: Item) -> str:
        """Build comprehensive roadmap context for better item generation coherence."""
        context_lines = []

        # Add roadmap overview
        context_lines.append("=== ROADMAP OVERVIEW ===")
        context_lines.append(f"Total Milestones: {len(milestones)}")

        # Count totals for overview
        total_epics = sum(len(m.get_children_by_type('Epic')) for m in milestones)
        total_stories = sum(len(e.get_children_by_type('Story')) for m in milestones for e in m.get_children_by_type('Epic'))
        total_tasks = sum(len(s.get_children_by_type('Task')) for m in milestones for e in m.get_children_by_type('Epic') for s in e.get_children_by_type('Story'))

        context_lines.append(f"Total Epics: {total_epics}")
        context_lines.append(f"Total Stories: {total_stories}")
        context_lines.append(f"Total Tasks: {total_tasks}")
        context_lines.append("")

        # Add milestone structure overview
        context_lines.append("=== MILESTONE STRUCTURE ===")
        for milestone in milestones:
            milestone_title = milestone.name.split(': ', 1)[-1] if ': ' in milestone.name else milestone.name
            context_lines.append(f"## Milestone {milestone.id}: {milestone_title}")
            if milestone.outline_description:
                context_lines.append(f"   → {milestone.outline_description}")

            for epic in milestone.get_children_by_type('Epic'):
                epic_title = epic.name.split(': ', 1)[-1] if ': ' in epic.name else epic.name
                context_lines.append(f"  ### Epic {epic.id}: {epic_title}")
                if epic.outline_description:
                    context_lines.append(f"     → {epic.outline_description}")

                for story in epic.get_children_by_type('Story'):
                    story_title = story.name.split(': ', 1)[-1] if ': ' in story.name else story.name
                    context_lines.append(f"    #### Story {story.id}: {story_title}")
                    if story.outline_description:
                        context_lines.append(f"       → {story.outline_description}")

                    for task_item in story.get_children_by_type('Task'):
                        task_title = task_item.name.split(': ', 1)[-1] if ': ' in task_item.name else task_item.name
                        context_lines.append(f"      ##### Task {task_item.id}: {task_title}")
                        if task_item.outline_description:
                            context_lines.append(f"         → {task_item.outline_description}")

        context_lines.append("")

        # Add context about what's been generated so far
        context_lines.append("=== GENERATION STATUS ===")
        context_lines.append(f"Currently generating: {current_item.item_type} {current_item.id}")

        # List completed items
        completed_items = []
        for milestone in milestones:
            if milestone.generation_status == ItemStatus.GENERATED and milestone != current_item:
                completed_items.append(f"Milestone {milestone.id}")

            for epic in milestone.get_children_by_type('Epic'):
                if epic.generation_status == ItemStatus.GENERATED and epic != current_item:
                    completed_items.append(f"Epic {epic.id}")

                for story in epic.get_children_by_type('Story'):
                    if story.generation_status == ItemStatus.GENERATED and story != current_item:
                        completed_items.append(f"Story {story.id}")

        if completed_items:
            context_lines.append("Previously generated items:")
            for item in completed_items:
                context_lines.append(f"  ✅ {item}")
        else:
            context_lines.append("This is the first item being generated.")

        context_lines.append("")

        return "\n".join(context_lines)

    def _build_semantic_context(self, item: Item) -> str:
        """Build semantic context for an item from outline descriptions and dependencies.

        This method extracts rich contextual information from the semantic outline
        to provide better guidance for content generation.
        """
        context_lines = []

        context_lines.append("=== SEMANTIC CONTEXT ===")

        # Add the item's semantic context (purpose, what, why)
        if item.has_semantic_context():
            context_lines.append(f"Item Purpose: {item.get_semantic_context()}")
            context_lines.append("")

        # Add dependency context
        if item.depends_on_items:
            context_lines.append("=== DEPENDENCIES ===")
            context_lines.append("This item depends on the following completed items:")
            context_lines.append(item.get_dependency_context())
            context_lines.append("")
            context_lines.append("Ensure this item builds upon the outputs of its dependencies.")
        else:
            context_lines.append("This item has no dependencies - it can be implemented independently.")

        # Add context from sibling items if any are completed
        if item.parent:
            siblings = [
                child for child in item.parent.children
                if child != item and child.generation_status == ItemStatus.GENERATED
            ]
            if siblings:
                context_lines.append("")
                context_lines.append("=== SIBLING ITEMS (Already Generated) ===")
                for sibling in siblings:
                    ctx = f"{sibling.item_type} {sibling.id}: {sibling.name}"
                    if hasattr(sibling, 'outline_description') and sibling.outline_description:
                        ctx += f"\n  → {sibling.outline_description}"
                    context_lines.append(ctx)
                context_lines.append("Ensure consistency with the above sibling items.")

        return "\n".join(context_lines)

    def _show_item_confirmation(self, item: Item, progress: Progress, task) -> None:
        """Show generated item and ask for user confirmation."""
        # Pause progress display temporarily
        progress.update(task, description=f"✅ Generated {item.item_type} {item.id}")

        self.console.print(f"\n[bold green]✅ Generated {item.item_type} {item.id}: {item.name.split(': ', 1)[-1] if ': ' in item.name else item.name}[/bold green]")

        # Show a preview of the generated content
        if item.content:
            preview = item.content[:300] + "..." if len(item.content) > 300 else item.content
            self.console.print(f"[dim]Preview: {preview}[/dim]")

        # Ask user for confirmation
        while True:
            choice = Prompt.ask(
                "[cyan]What would you like to do?[/cyan]",
                choices=["continue", "quit", "regenerate"],
                default="continue"
            )

            if choice == "continue":
                break
            elif choice == "quit":
                self.console.print("[yellow]🛑 Generation stopped by user[/yellow]")
                raise KeyboardInterrupt("User chose to quit generation")
            elif choice == "regenerate":
                self.console.print(f"[yellow]🔄 Regenerating {item.item_type} {item.id}...[/yellow]")
                # Mark as pending and regenerate
                item.update_generation_status(ItemStatus.PENDING)
                progress.update(task, description=f"Regenerating {item.item_type} {item.id}")

                # Regenerate the item
                parent_context = None
                if item.parent:
                    parent_context = f"{item.parent.item_type} {item.parent.id}: {item.parent.name.split(': ', 1)[-1] if ': ' in item.parent.name else item.parent.name}"

                # Get milestones from the current context (we need to pass this properly)
                roadmap_context = ""  # For now, skip roadmap context in regeneration
                prompt = item.generate_prompt("", parent_context, roadmap_context)
                # Get appropriate client for regeneration
                client = self._get_client_for_item(item.item_type.lower())
                response = client.generate(prompt)
                item.parse_content(response)

                self.console.print(f"[green]✅ Regenerated {item.item_type} {item.id}[/green]")

                # Show the new content
                if item.content:
                    preview = item.content[:300] + "..." if len(item.content) > 300 else item.content
                    self.console.print(f"[dim]New Preview: {preview}[/dim]")

                # Continue the loop to ask again