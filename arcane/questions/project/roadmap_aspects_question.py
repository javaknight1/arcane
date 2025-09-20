#!/usr/bin/env python3
"""Non-technical roadmap aspects question."""

import inquirer
from ..base_question import BaseQuestion


class RoadmapAspectsQuestion(BaseQuestion):
    """Question for selecting non-technical aspects to include in roadmap."""

    @property
    def question_key(self) -> str:
        return "roadmap_aspects"

    @property
    def cli_flag_name(self) -> str:
        return "--roadmap-aspects"

    @property
    def question_text(self) -> str:
        return "Roadmap Aspects"

    @property
    def section_title(self) -> str:
        return "Project Scope & Planning"

    def _get_emoji(self) -> str:
        return "🎯"

    def _prompt_user(self):
        """Prompt user for non-technical aspects to include in roadmap."""
        self.console.print("[dim]Select all non-technical aspects to include in your roadmap[/dim]")
        self.console.print("[dim]By default, roadmaps focus on technical implementation. Select additional aspects for a comprehensive plan.[/dim]")

        choices = [
            ('Business Strategy & Planning', 'business-strategy'),
            ('Marketing & Sales', 'marketing-sales'),
            ('Legal & Compliance', 'legal-compliance'),
            ('Operations & Process Management', 'operations'),
            ('Customer Support & Success', 'customer-support'),
            ('Finance & Accounting', 'finance-accounting'),
            ('HR & Team Building', 'hr-team'),
            ('Product Management', 'product-management'),
            ('Quality Assurance & Testing', 'qa-testing'),
            ('Risk Management', 'risk-management'),
            ('Technical only (default)', 'technical-only')
        ]

        question = inquirer.Checkbox(
            'roadmap_aspects',
            message="Select aspects to include (use SPACE to select, ENTER to confirm)",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer:
            return 'cancel'

        selected = answer.get('roadmap_aspects', [])

        # If 'technical-only' is selected with other options, keep only 'technical-only'
        if 'technical-only' in selected and len(selected) > 1:
            selected = ['technical-only']

        # If nothing selected, default to technical-only
        if not selected:
            selected = ['technical-only']

        return selected

    def _format_value_for_display(self, value):
        """Format the roadmap aspects for display."""
        if not value or value == ['technical-only']:
            return "Technical implementation only"
        if isinstance(value, list):
            # Map internal values to display names
            display_map = {
                'business-strategy': 'Business Strategy',
                'marketing-sales': 'Marketing & Sales',
                'legal-compliance': 'Legal & Compliance',
                'operations': 'Operations',
                'customer-support': 'Customer Support',
                'finance-accounting': 'Finance & Accounting',
                'hr-team': 'HR & Team Building',
                'product-management': 'Product Management',
                'qa-testing': 'Quality Assurance',
                'risk-management': 'Risk Management',
                'technical-only': 'Technical Only'
            }
            display_values = [display_map.get(v, v) for v in value]
            return ", ".join(display_values)
        return str(value)