"""New guided roadmap generator using individual item generation approach."""

from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.prompt import Prompt, Confirm

from arcane.clients import LLMClientFactory
from arcane.engines.generation.metadata_extractor import MetadataExtractor
from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator
from arcane.engines.generation.semantic_converter import SemanticToItemConverter
from arcane.engines.parsing.outline_parser import OutlineParser
from arcane.engines.validation import (
    DependencyValidator,
    DependencyIssue,
    IssueSeverity,
    CompletenessChecker,
    CompletenessSeverity,
    CrossReferenceValidator,
    CoherenceAutoFixer,
)
from arcane.items import Roadmap
from arcane.items.milestone import Milestone
from arcane.items.story import Story
from arcane.models.outline_item import SemanticOutline
from arcane.protocols.llm_protocols import LLMClientProtocol
from arcane.protocols.display_protocols import ConsoleDisplayProtocol
from arcane.protocols.roadmap_protocols import RoadmapProtocol
from arcane.config import get_config
from .helpers import CostEstimationHelper, OutlineProcessor, GenerationSummaryReporter, FileManager


class RoadmapGenerator:
    """Primary roadmap generation engine that orchestrates the complete generation workflow.

    This engine handles the entire roadmap generation process from user preferences
    to fully detailed roadmap structures, including cost estimation, outline generation,
    and individual item content generation.
    """

    def __init__(self, llm_provider: str = 'claude', output_directory: Optional[str] = None):
        self.config = get_config()
        self.llm_provider = llm_provider or self.config.get('llm.default_provider', 'claude')
        self.llm_client: LLMClientProtocol = LLMClientFactory.create(self.llm_provider)
        self.metadata_extractor = MetadataExtractor()
        self.recursive_generator = RecursiveRoadmapGenerator(self.llm_client)
        self.outline_parser = OutlineParser()
        self.semantic_converter = SemanticToItemConverter()
        self.console: ConsoleDisplayProtocol = Console()

        # Initialize helper classes
        self.cost_helper = CostEstimationHelper(self.console)
        self.outline_processor = OutlineProcessor(self.console)
        self.summary_reporter = GenerationSummaryReporter(self.console)
        self.file_manager = FileManager(self.console, output_directory)

    def generate_roadmap(self, idea: str, preferences: Dict[str, Any]) -> Optional[RoadmapProtocol]:
        """Generate roadmap using the new individual item approach."""

        # Step 1: Ask user for generation mode preference first
        interactive_mode = self._ask_generation_mode() if self.config.get('generation.interactive_mode', True) else False

        # Step 2: Generate outline
        outline = self.outline_processor.generate_and_confirm_outline(
            self.llm_client, idea, preferences,
            self.file_manager.save_outline if self.file_manager.save_outputs else None,
            self.file_manager.save_outline_prompt if self.file_manager.save_outputs else None
        )
        if not outline:
            return None

        # Step 3: Parse outline into item objects
        self.console.print("\n[cyan]📊 Parsing outline into item objects...[/cyan]")
        milestones = self.outline_parser.parse_outline(outline)

        # Validate structure
        issues = self.outline_parser.validate_structure(milestones)
        if issues:
            self.console.print("[red]❌ Structure validation issues:[/red]")
            for issue in issues:
                self.console.print(f"[red]  • {issue}[/red]")
            return None

        # Step 3.5: Validate dependencies before content generation
        if not self._validate_dependencies(milestones):
            return None

        # Step 4: Show cost estimates for individual item generation
        item_counts = self.outline_parser.count_items(milestones)
        if not self.cost_helper.show_and_confirm_individual_costs(self.llm_provider, idea, item_counts):
            self.console.print("[yellow]⚠️ Generation cancelled - cost not approved[/yellow]")
            return None

        # Step 5: Create roadmap object with proper Project structure
        from arcane.items.project import Project
        metadata, _ = self.metadata_extractor.extract_metadata(outline)

        # Create project from metadata
        project = Project(
            name=metadata.project_name,
            description=metadata.description,
            project_type=metadata.project_type,
            tech_stack=metadata.tech_stack,
            estimated_duration=metadata.estimated_duration,
            team_size=metadata.team_size
        )

        # Add milestones to project
        for milestone in milestones:
            project.add_milestone(milestone)

        roadmap = Roadmap(project)

        # Step 6: Generate all content using object-oriented approach
        self.console.print(f"\n[bold green]🚀 Starting roadmap generation[/bold green]")
        roadmap.generate_all_content(self.llm_client, idea, interactive_mode, self.console)

        # Step 6.5: Post-generation completeness check
        validation_report = self._check_completeness(milestones)

        # Step 6.6: Cross-reference validation with auto-fix option
        cross_ref_report = self._cross_reference_validation(roadmap)
        if cross_ref_report:
            validation_report = (validation_report or "") + "\n\n" + cross_ref_report

        # Step 7: Show generation summary
        summary = self.recursive_generator.get_generation_summary(milestones)
        self.summary_reporter.show_generation_summary(summary)

        # Step 8: Export to markdown and save outputs
        markdown_content = self.recursive_generator.export_to_markdown(milestones)

        # Append validation report if there were issues
        if validation_report:
            markdown_content += f"\n\n---\n\n{validation_report}"

        if self.file_manager.save_outputs:
            project_name = self.file_manager.extract_project_name(outline)
            self.file_manager.save_complete_roadmap(markdown_content, project_name)

            # Save progress for potential resume
            progress_file = self.file_manager.get_progress_filepath(project_name)
            self.recursive_generator.save_progress(milestones, progress_file)

        return roadmap

    def _ask_generation_mode(self) -> bool:
        """Ask user whether they want interactive confirmations or automatic generation."""
        choices = self.config.get('generation.mode_choices', ["automatic", "interactive"])
        default_mode = self.config.get('generation.default_mode', "automatic")

        self.console.print("\n[bold cyan]🤖 Generation Mode Selection[/bold cyan]")
        self.console.print("How would you like to generate the roadmap items?")
        self.console.print("")
        self.console.print("[green]automatic[/green] - Generate all items without stopping for confirmation")
        self.console.print("[cyan]interactive[/cyan] - Prompt for confirmation after each item (continue/quit/regenerate)")

        choice = Prompt.ask(
            "\n[cyan]Choose generation mode[/cyan]",
            choices=choices,
            default=default_mode
        )

        if choice == "interactive":
            self.console.print("[cyan]✅ Interactive mode: You'll be prompted after each item[/cyan]")
            return True
        else:
            self.console.print("[green]✅ Automatic mode: All items will be generated continuously[/green]")
            return False

    def generate_semantic_roadmap(self, idea: str, preferences: Dict[str, Any]) -> Optional[RoadmapProtocol]:
        """Generate roadmap using semantic outlines with descriptions and dependencies.

        This method uses the enhanced semantic outline format which includes:
        - Descriptions for each item (what it does, why it's needed)
        - Explicit dependencies between items
        - Topological ordering for generation

        Args:
            idea: The project idea content
            preferences: User preferences for generation

        Returns:
            Generated Roadmap or None if cancelled
        """
        # Step 1: Ask user for generation mode preference first
        interactive_mode = self._ask_generation_mode() if self.config.get('generation.interactive_mode', True) else False

        # Step 2: Generate semantic outline
        outline_text, semantic_outline = self.outline_processor.generate_semantic_outline(
            self.llm_client, idea, preferences,
            self.file_manager.save_outline if self.file_manager.save_outputs else None,
            self.file_manager.save_outline_prompt if self.file_manager.save_outputs else None
        )
        if not outline_text or not semantic_outline:
            return None

        # Step 3: Convert semantic outline to Item objects
        self.console.print("\n[cyan]📊 Converting semantic outline to items...[/cyan]")
        milestones = self.semantic_converter.convert_outline(semantic_outline)

        # Show conversion statistics
        stats = self.semantic_converter.get_statistics()
        self.console.print(f"  [green]✓ Created {stats['milestones']} milestones[/green]")
        self.console.print(f"  [green]✓ Created {stats['epics']} epics[/green]")
        self.console.print(f"  [green]✓ Created {stats['stories']} stories[/green]")
        self.console.print(f"  [green]✓ Created {stats['tasks']} tasks[/green]")
        self.console.print(f"  [cyan]✓ {stats['items_with_semantic_context']} items with semantic context[/cyan]")
        self.console.print(f"  [cyan]✓ {stats['items_with_dependencies']} items with dependencies[/cyan]")

        # Step 3.5: Validate dependencies before content generation
        if not self._validate_dependencies(milestones):
            return None

        # Step 4: Show cost estimates for individual item generation
        item_counts = {
            'milestones': stats['milestones'],
            'epics': stats['epics'],
            'stories': stats['stories'],
            'tasks': stats['tasks']
        }
        if not self.cost_helper.show_and_confirm_individual_costs(self.llm_provider, idea, item_counts):
            self.console.print("[yellow]⚠️ Generation cancelled - cost not approved[/yellow]")
            return None

        # Step 5: Create roadmap object with proper Project structure
        from arcane.items.project import Project

        # Create project from semantic outline metadata
        project = Project(
            name=semantic_outline.project_name or "Roadmap",
            description=semantic_outline.project_description or "",
            project_type=semantic_outline.project_type or "",
            tech_stack=semantic_outline.tech_stack or "",
            estimated_duration=semantic_outline.estimated_duration or "",
            team_size=semantic_outline.team_size or ""
        )

        # Add milestones to project
        for milestone in milestones:
            project.add_milestone(milestone)

        roadmap = Roadmap(project)

        # Step 6: Generate all content using semantic context
        self.console.print(f"\n[bold green]🚀 Starting semantic roadmap generation[/bold green]")

        # Get dependency-ordered items for generation
        generation_order = self.semantic_converter.get_generation_order()
        self.console.print(f"  [dim]Generating {len(generation_order)} items in dependency order[/dim]")

        # Generate content with semantic context
        roadmap.generate_all_content(self.llm_client, idea, interactive_mode, self.console)

        # Step 6.5: Post-generation completeness check
        validation_report = self._check_completeness(milestones)

        # Step 6.6: Cross-reference validation with auto-fix option
        cross_ref_report = self._cross_reference_validation(roadmap)
        if cross_ref_report:
            validation_report = (validation_report or "") + "\n\n" + cross_ref_report

        # Step 7: Show generation summary
        summary = self.recursive_generator.get_generation_summary(milestones)
        self.summary_reporter.show_generation_summary(summary)

        # Step 8: Export to markdown and save outputs
        markdown_content = self.recursive_generator.export_to_markdown(milestones)

        # Append validation report if there were issues
        if validation_report:
            markdown_content += f"\n\n---\n\n{validation_report}"

        if self.file_manager.save_outputs:
            project_name = semantic_outline.project_name or "roadmap"
            self.file_manager.save_complete_roadmap(markdown_content, project_name)

            # Save progress for potential resume
            progress_file = self.file_manager.get_progress_filepath(project_name)
            self.recursive_generator.save_progress(milestones, progress_file)

        return roadmap

    def _validate_dependencies(self, milestones: List[Milestone]) -> bool:
        """Validate dependencies before content generation.

        Args:
            milestones: List of milestone objects to validate

        Returns:
            True if validation passes or user chooses to continue, False to abort
        """
        self.console.print("\n[cyan]🔍 Validating dependencies...[/cyan]")

        validator = DependencyValidator()
        issues = validator.validate(milestones)

        if not issues:
            self.console.print("[green]✅ No dependency issues found[/green]")
            return True

        # Show validation report
        summary = validator.get_summary()
        self.console.print(f"\n[yellow]⚠️ Dependency validation found {summary['total_issues']} issues:[/yellow]")
        self.console.print(f"  [red]❌ Errors: {summary['errors']}[/red]")
        self.console.print(f"  [yellow]⚠️ Warnings: {summary['warnings']}[/yellow]")
        self.console.print(f"  [cyan]ℹ️ Info: {summary['info']}[/cyan]")

        # Show detected features
        if validator.detected_features:
            self.console.print(f"\n[dim]Detected features: {', '.join(sorted(validator.detected_features))}[/dim]")

        # Show errors in detail
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
        if errors:
            self.console.print("\n[red]Critical Issues:[/red]")
            for issue in errors[:5]:  # Show first 5 errors
                self.console.print(f"  [red]• [{issue.item_id}] {issue.message}[/red]")
                if issue.suggested_fix:
                    self.console.print(f"    [dim]→ Fix: {issue.suggested_fix}[/dim]")

            if len(errors) > 5:
                self.console.print(f"  [dim]... and {len(errors) - 5} more errors[/dim]")

        # Show warnings
        warnings = [i for i in issues if i.severity == IssueSeverity.WARNING]
        if warnings:
            self.console.print("\n[yellow]Warnings:[/yellow]")
            for issue in warnings[:3]:  # Show first 3 warnings
                self.console.print(f"  [yellow]• [{issue.item_id}] {issue.message}[/yellow]")

            if len(warnings) > 3:
                self.console.print(f"  [dim]... and {len(warnings) - 3} more warnings[/dim]")

        # If there are errors, ask user whether to continue
        if errors:
            self.console.print("\n[red]⚠️ Critical dependency issues found.[/red]")
            if not Confirm.ask("[yellow]Continue with generation anyway?[/yellow]", default=False):
                self.console.print("[red]🛑 Generation cancelled due to dependency issues[/red]")
                return False

        return True

    def _check_completeness(self, milestones: List[Milestone]) -> Optional[str]:
        """Run post-generation completeness check.

        Args:
            milestones: List of milestone objects to check

        Returns:
            Validation report string if issues found, None otherwise
        """
        self.console.print("\n[cyan]🔍 Checking completeness...[/cyan]")

        checker = CompletenessChecker()
        issues = checker.check_all(milestones)

        if not issues:
            self.console.print("[green]✅ All items pass completeness check[/green]")
            return None

        summary = checker.get_summary()
        self.console.print(f"\n[yellow]⚠️ Completeness check found {summary['total_issues']} issues:[/yellow]")
        self.console.print(f"  [red]❌ Errors: {summary['errors']}[/red]")
        self.console.print(f"  [yellow]⚠️ Warnings: {summary['warnings']}[/yellow]")
        self.console.print(f"  [cyan]ℹ️ Info: {summary['info']}[/cyan]")

        # Show coverage issues for stories
        coverage_issues = [i for i in issues if i.issue_type in ['uncovered_criterion', 'low_coverage']]
        if coverage_issues:
            self.console.print("\n[yellow]Coverage Issues:[/yellow]")
            for issue in coverage_issues[:5]:
                coverage_str = f" ({issue.coverage_percentage:.0f}%)" if issue.coverage_percentage is not None else ""
                self.console.print(f"  [yellow]• [{issue.item_id}]{coverage_str} {issue.description}[/yellow]")

            if len(coverage_issues) > 5:
                self.console.print(f"  [dim]... and {len(coverage_issues) - 5} more coverage issues[/dim]")

        # Show empty item errors
        empty_issues = [i for i in issues if i.issue_type in ['empty_milestone', 'empty_epic', 'empty_story']]
        if empty_issues:
            self.console.print("\n[red]Empty Items:[/red]")
            for issue in empty_issues:
                self.console.print(f"  [red]• [{issue.item_id}] {issue.description}[/red]")

        # Offer to show detailed coverage for specific stories
        stories_with_issues = set(i.item_id for i in coverage_issues if i.item_id != "roadmap")
        if stories_with_issues and len(stories_with_issues) <= 3:
            for story in self._get_all_stories(milestones):
                if story.id in stories_with_issues:
                    self._show_story_coverage_details(checker, story)

        # Return formatted report for export
        return self._format_validation_report(checker, issues)

    def _get_all_stories(self, milestones: List[Milestone]) -> List[Story]:
        """Get all stories from milestones."""
        stories = []
        for milestone in milestones:
            for epic in milestone.get_children_by_type('Epic'):
                stories.extend(epic.get_children_by_type('Story'))
        return stories

    def _show_story_coverage_details(self, checker: CompletenessChecker, story: Story) -> None:
        """Show detailed coverage information for a story."""
        mapping = checker.map_tasks_to_criteria(story)

        if mapping.coverage_percentage < 100:
            self.console.print(f"\n[dim]Coverage details for Story {story.id}:[/dim]")

            criteria = getattr(story, 'acceptance_criteria', [])
            if not criteria:
                criteria = getattr(story, 'success_criteria', [])

            for i, criterion in enumerate(criteria):
                task_ids = mapping.coverage.get(i, [])
                if task_ids:
                    self.console.print(f"  [green]✓ AC{i+1}: Covered by {', '.join(task_ids)}[/green]")
                else:
                    criterion_preview = criterion[:40] + "..." if len(criterion) > 40 else criterion
                    self.console.print(f"  [red]✗ AC{i+1}: {criterion_preview}[/red]")

    def _format_validation_report(self, checker: CompletenessChecker, issues: List) -> str:
        """Format validation report for export."""
        lines = ["## Validation Report", ""]

        summary = checker.get_summary()
        lines.append(f"**Total Issues:** {summary['total_issues']}")
        lines.append(f"- Errors: {summary['errors']}")
        lines.append(f"- Warnings: {summary['warnings']}")
        lines.append(f"- Info: {summary['info']}")
        lines.append("")

        if summary['errors'] > 0:
            lines.append("### Errors")
            for issue in [i for i in issues if i.severity == CompletenessSeverity.ERROR]:
                lines.append(f"- **[{issue.item_id}]** {issue.description}")
            lines.append("")

        if summary['warnings'] > 0:
            lines.append("### Warnings")
            for issue in [i for i in issues if i.severity == CompletenessSeverity.WARNING]:
                coverage_str = f" ({issue.coverage_percentage:.0f}% coverage)" if issue.coverage_percentage else ""
                lines.append(f"- **[{issue.item_id}]**{coverage_str} {issue.description}")
            lines.append("")

        return "\n".join(lines)

    def _cross_reference_validation(self, roadmap: Roadmap) -> Optional[str]:
        """Run post-generation cross-reference validation with auto-fix option.

        Args:
            roadmap: The generated roadmap to validate

        Returns:
            Validation report string if issues found, None otherwise
        """
        self.console.print("\n[cyan]🔗 Running cross-reference validation...[/cyan]")

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        if not issues:
            self.console.print("[green]✅ No coherence issues found[/green]")
            return None

        # Show validation summary
        summary = validator.get_summary()
        self.console.print(f"\n[yellow]⚠️ Cross-reference validation found {summary['total_issues']} issues:[/yellow]")
        self.console.print(f"  [red]❌ Critical: {summary['by_severity']['critical']}[/red]")
        self.console.print(f"  [yellow]⚠️ Warnings: {summary['by_severity']['warning']}[/yellow]")
        self.console.print(f"  [cyan]ℹ️ Info: {summary['by_severity']['info']}[/cyan]")

        # Show critical issues in detail
        critical_issues = validator.get_critical_issues()
        if critical_issues:
            self.console.print("\n[red]Critical Issues:[/red]")
            for issue in critical_issues[:5]:
                self.console.print(f"  [red]• [{issue.item_id}] {issue.description}[/red]")
                if issue.suggestion:
                    self.console.print(f"    [dim]→ {issue.suggestion}[/dim]")

            if len(critical_issues) > 5:
                self.console.print(f"  [dim]... and {len(critical_issues) - 5} more critical issues[/dim]")

        # Check for auto-fixable issues
        auto_fixable = validator.get_auto_fixable_issues()
        if auto_fixable:
            self.console.print(f"\n[cyan]🔧 {len(auto_fixable)} issues can be automatically fixed[/cyan]")

            if Confirm.ask("[yellow]Would you like to auto-fix these issues?[/yellow]", default=True):
                fixer = CoherenceAutoFixer(self.llm_client)
                results = fixer.fix_issues(roadmap, auto_fixable)

                self.console.print(f"\n[green]✅ Fixed {results['fixed']} issues[/green]")
                if results['failed'] > 0:
                    self.console.print(f"[red]❌ Failed to fix {results['failed']} issues[/red]")

                # Re-validate after fixes
                if results['fixed'] > 0:
                    self.console.print("\n[cyan]🔍 Re-validating after fixes...[/cyan]")
                    remaining_issues = validator.validate_roadmap(roadmap)
                    if remaining_issues:
                        self.console.print(f"[yellow]⚠️ {len(remaining_issues)} issues remaining[/yellow]")
                    else:
                        self.console.print("[green]✅ All issues resolved![/green]")
                    issues = remaining_issues

        # Return formatted report for export
        return self._format_cross_reference_report(validator, issues)

    def _format_cross_reference_report(self, validator: CrossReferenceValidator, issues: List) -> str:
        """Format cross-reference validation report for export.

        Args:
            validator: The validator that was used
            issues: List of remaining issues

        Returns:
            Formatted report string
        """
        if not issues:
            return ""

        lines = ["## Cross-Reference Validation Report", ""]

        summary = validator.get_summary()
        lines.append(f"**Total Issues:** {summary['total_issues']}")
        lines.append(f"- Critical: {summary['by_severity']['critical']}")
        lines.append(f"- Warnings: {summary['by_severity']['warning']}")
        lines.append(f"- Info: {summary['by_severity']['info']}")
        lines.append("")

        # Group issues by type
        from arcane.engines.validation import CoherenceSeverity

        for severity_name, severity_enum in [
            ("Critical", CoherenceSeverity.CRITICAL),
            ("Warnings", CoherenceSeverity.WARNING),
            ("Info", CoherenceSeverity.INFO)
        ]:
            severity_issues = [i for i in issues if i.severity == severity_enum]
            if severity_issues:
                lines.append(f"### {severity_name}")
                for issue in severity_issues:
                    lines.append(f"- **[{issue.item_id}]** {issue.issue_type}: {issue.description}")
                lines.append("")

        return "\n".join(lines)