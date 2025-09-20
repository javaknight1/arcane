#!/usr/bin/env python3
"""Deployment environment question."""

import inquirer
from ..base_question import BaseQuestion


class DeploymentEnvironmentQuestion(BaseQuestion):
    """Question for deployment environment."""

    @property
    def question_key(self) -> str:
        return "deployment_environment"

    @property
    def cli_flag_name(self) -> str:
        return "--deployment-environment"

    @property
    def question_text(self) -> str:
        return "Deployment Environment"

    @property
    def section_title(self) -> str:
        return "Deployment Assessment"

    def _get_emoji(self) -> str:
        return "☁️"

    def _prompt_user(self):
        """Prompt user for deployment environment."""
        self.console.print("[dim]What is your primary deployment environment?[/dim]")

        choices = [
            ('Cloud-native (AWS/GCP/Azure)', 'cloud'),
            ('Serverless-first (Lambda/Functions)', 'serverless'),
            ('Container orchestration (Kubernetes)', 'kubernetes'),
            ('Traditional VPS/dedicated servers', 'traditional'),
            ('On-premise requirements', 'on-premise'),
            ('Hybrid cloud/on-premise', 'hybrid'),
            ('Edge computing/IoT devices', 'edge'),
            ('❌ Cancel', 'cancel')
        ]

        question = inquirer.List(
            'deployment_environment',
            message="Primary deployment environment",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])
        if not answer or answer.get('deployment_environment') == 'cancel':
            return 'cancel'

        return answer.get('deployment_environment')

    def _format_value_for_display(self, value):
        """Format the deployment environment for display."""
        env_map = {
            'cloud': 'Cloud-native (AWS/GCP/Azure)',
            'serverless': 'Serverless-first (Lambda/Functions)',
            'kubernetes': 'Container orchestration (Kubernetes)',
            'traditional': 'Traditional VPS/dedicated servers',
            'on-premise': 'On-premise requirements',
            'hybrid': 'Hybrid cloud/on-premise',
            'edge': 'Edge computing/IoT devices'
        }
        return env_map.get(value, str(value))