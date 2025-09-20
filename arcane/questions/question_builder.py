#!/usr/bin/env python3
"""QuestionBuilder orchestrator for collecting all user preferences."""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from .base_question import BaseQuestion

# System Configuration
from .system.llm_provider_question import LLMProviderQuestion
from .system.idea_file_question import IdeaFileQuestion
from .system.output_directory_question import OutputDirectoryQuestion

# Project Configuration
from .project.timeline_question import TimelineQuestion
from .project.focus_question import FocusQuestion
from .project.team_size_question import TeamSizeQuestion
from .project.industry_question import IndustryQuestion
from .project.regulatory_question import RegulatoryQuestion

# Technical Assessment
from .technical.technical_challenges_question import TechnicalChallengesQuestion

# Team Assessment
from .team.team_expertise_question import TeamExpertiseQuestion
from .team.team_distribution_question import TeamDistributionQuestion
from .team.dev_methodology_question import DevMethodologyQuestion

# Budget Assessment
from .budget.budget_range_question import BudgetRangeQuestion
from .budget.infra_budget_question import InfraBudgetQuestion
from .budget.services_budget_question import ServicesBudgetQuestion

# Deployment Assessment
from .deployment.deployment_environment_question import DeploymentEnvironmentQuestion
from .deployment.geographic_distribution_question import GeographicDistributionQuestion
from .deployment.scaling_expectations_question import ScalingExpectationsQuestion

# Integration Requirements
from .integration.payment_integrations_question import PaymentIntegrationsQuestion
from .integration.communication_integrations_question import CommunicationIntegrationsQuestion
from .integration.business_integrations_question import BusinessIntegrationsQuestion
from .integration.developer_integrations_question import DeveloperIntegrationsQuestion
from .integration.data_integrations_question import DataIntegrationsQuestion

# Success Definition
from .success.success_metric_question import SuccessMetricQuestion
from .success.success_timeline_question import SuccessTimelineQuestion
from .success.measurement_approach_question import MeasurementApproachQuestion
from .success.failure_tolerance_question import FailureToleranceQuestion


class QuestionBuilder:
    """Orchestrates the collection of all user preferences."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.questions: List[BaseQuestion] = []
        self.answers: Dict[str, Any] = {}
        self._initialize_questions()

    def _initialize_questions(self) -> None:
        """Initialize all question instances."""
        self.questions = [
            # System Configuration (asked first)
            LLMProviderQuestion(self.console),
            IdeaFileQuestion(self.console),
            OutputDirectoryQuestion(self.console),

            # Basic Project Configuration
            TimelineQuestion(self.console),
            FocusQuestion(self.console),
            TeamSizeQuestion(self.console),
            IndustryQuestion(self.console),
            RegulatoryQuestion(self.console),

            # Technical Assessment
            TechnicalChallengesQuestion(self.console),

            # Enhanced Team Assessment
            TeamExpertiseQuestion(self.console),
            TeamDistributionQuestion(self.console),
            DevMethodologyQuestion(self.console),

            # Budget Assessment
            BudgetRangeQuestion(self.console),
            InfraBudgetQuestion(self.console),
            ServicesBudgetQuestion(self.console),

            # Deployment Assessment
            DeploymentEnvironmentQuestion(self.console),
            GeographicDistributionQuestion(self.console),
            ScalingExpectationsQuestion(self.console),

            # Integration Requirements
            PaymentIntegrationsQuestion(self.console),
            CommunicationIntegrationsQuestion(self.console),
            BusinessIntegrationsQuestion(self.console),
            DeveloperIntegrationsQuestion(self.console),
            DataIntegrationsQuestion(self.console),

            # Success Definition
            SuccessMetricQuestion(self.console),
            SuccessTimelineQuestion(self.console),
            MeasurementApproachQuestion(self.console),
            FailureToleranceQuestion(self.console),
        ]

    def collect_all_preferences(self, cli_flags: Dict[str, Any]) -> Dict[str, Any]:
        """Collect all preferences with CLI flag override support.

        Args:
            cli_flags: Dictionary of CLI flag values

        Returns:
            Dictionary of all collected preferences
        """
        try:
            self.console.print("\n[bold]📋 Collecting Project Preferences[/bold]")

            # Step 1: Set values from CLI flags
            self._apply_cli_flags(cli_flags)

            # Step 2: Ask remaining questions by section
            self._ask_questions_by_section()

            # Step 3: Collect all answers
            self._collect_answers()

            # Step 4: Show summary and confirm
            if self._show_summary_and_confirm():
                return self.answers
            else:
                # User cancelled
                return {}

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Preference collection cancelled[/yellow]")
            return {}

    def _apply_cli_flags(self, cli_flags: Dict[str, Any]) -> None:
        """Apply CLI flag values to questions."""
        flags_applied = 0

        for question in self.questions:
            # Map CLI flag names to question keys
            flag_key = question.cli_flag_name.lstrip('-').replace('-', '_')
            if flag_key in cli_flags and cli_flags[flag_key] is not None:
                question.set_value_from_flag(cli_flags[flag_key])
                flags_applied += 1

        if flags_applied > 0:
            self.console.print(f"[cyan]💡 Applied {flags_applied} values from CLI flags[/cyan]")

    def _ask_questions_by_section(self) -> None:
        """Ask questions grouped by section."""
        sections = self._group_questions_by_section()

        for section_title, section_questions in sections.items():
            unanswered_questions = [q for q in section_questions if not q.is_answered]

            if not unanswered_questions:
                continue

            # Display section header
            self.console.print(f"\n[bold]{section_title}[/bold]")
            self.console.print("[dim]Press Ctrl+C at any time to cancel[/dim]")

            # Ask each unanswered question in the section
            for question in unanswered_questions:
                try:
                    question.ask_user()
                except KeyboardInterrupt:
                    # Re-raise to be caught by the main method
                    raise

    def _group_questions_by_section(self) -> Dict[str, List[BaseQuestion]]:
        """Group questions by their section titles."""
        sections: Dict[str, List[BaseQuestion]] = {}

        for question in self.questions:
            section = question.section_title
            if section not in sections:
                sections[section] = []
            sections[section].append(question)

        return sections

    def _collect_answers(self) -> None:
        """Collect all answers from questions into the answers dictionary."""
        self.answers = {}

        for question in self.questions:
            if question.is_answered:
                question_dict = question.to_dict()
                self.answers.update(question_dict)

        # Add any validation or processing here
        self._validate_and_process_answers()

    def _validate_and_process_answers(self) -> None:
        """Validate answers and add any derived values."""
        # Check for validation errors
        validation_errors = []
        for question in self.questions:
            if question.is_answered:
                error = question.get_validation_error()
                if error:
                    validation_errors.append(f"{question.question_text}: {error}")

        if validation_errors:
            self.console.print("[red]❌ Validation errors:[/red]")
            for error in validation_errors:
                self.console.print(f"  • {error}")
            raise ValueError("Validation failed")

        # Add calculated fields
        self._add_calculated_fields()

    def _add_calculated_fields(self) -> None:
        """Add calculated fields based on answers."""
        # Example: Calculate complexity from technical challenges
        # if 'technical_challenges' in self.answers:
        #     challenges = self.answers['technical_challenges']
        #     if isinstance(challenges, list):
        #         challenge_count = len([c for c in challenges if c != 'none'])
        #         if challenge_count <= 2:
        #             self.answers['calculated_complexity'] = 'simple'
        #         elif challenge_count <= 5:
        #             self.answers['calculated_complexity'] = 'moderate'
        #         else:
        #             self.answers['calculated_complexity'] = 'complex'

        # Add risk assessment
        self._calculate_risk_levels()

    def _calculate_risk_levels(self) -> None:
        """Calculate basic risk levels."""
        # Basic risk assessment - will be enhanced as more questions are added
        risks = []

        # Timeline vs Team Size risk
        timeline = self.answers.get('timeline', '')
        team_size = self.answers.get('team_size', '')

        if timeline == '3-months' and team_size == '1':
            risks.append('aggressive-timeline')

        # Add basic risk fields
        self.answers['technical_risk'] = 'medium'  # Default, will be calculated from technical challenges
        self.answers['budget_risk'] = 'medium'     # Default, will be calculated from budget questions
        self.answers['team_risk'] = 'high' if 'aggressive-timeline' in risks else 'low'
        self.answers['overall_risk_score'] = len(risks) / 10.0  # Normalized

    def _show_summary_and_confirm(self) -> bool:
        """Show preference summary and get user confirmation."""
        self.console.print("\n[bold]📋 Preference Summary[/bold]")

        table = Table(title="Collected Preferences")
        table.add_column("Question", style="cyan")
        table.add_column("Answer", style="green")

        # Show key preferences (most important ones)
        key_preferences = [
            ('LLM Provider', 'llm_provider'),
            ('Timeline', 'timeline'),
            ('Focus', 'focus'),
            ('Team Size', 'team_size'),
            ('Industry', 'industry'),
            ('Budget Range', 'budget_range'),
            ('Deployment', 'deployment_environment'),
            ('Success Metric', 'success_metric'),
        ]

        for display_name, key in key_preferences:
            value = self.answers.get(key, 'Not specified')
            table.add_row(display_name, str(value))

        self.console.print(table)

        return Confirm.ask("\nProceed with roadmap generation using these preferences?", default=True)

    def get_answered_questions(self) -> List[BaseQuestion]:
        """Get list of questions that have been answered."""
        return [q for q in self.questions if q.is_answered]

    def get_unanswered_questions(self) -> List[BaseQuestion]:
        """Get list of questions that have not been answered."""
        return [q for q in self.questions if not q.is_answered]

    def reset_all_questions(self) -> None:
        """Reset all questions to unanswered state."""
        for question in self.questions:
            question.reset()
        self.answers = {}

    def get_completion_percentage(self) -> float:
        """Get percentage of questions completed."""
        if not self.questions:
            return 0.0
        answered = len(self.get_answered_questions())
        total = len(self.questions)
        return (answered / total) * 100.0