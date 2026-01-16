#!/usr/bin/env python3
"""Export platform selection question."""

from typing import Any, Dict, List, Optional, Tuple
import inquirer
from ..base_question import BaseQuestion

from arcane.engines.export.base_exporter import (
    ExportPlatform,
    PlatformConfig,
    PLATFORM_CONFIGS,
)


class ExportPlatformQuestion(BaseQuestion):
    """Question for selecting the export platform.

    Displays available export platforms grouped by configuration status,
    showing which are ready to use and which require setup.
    """

    # Special values for non-platform options
    FILE_ONLY = "file_only"
    SKIP = "skip"

    @property
    def question_key(self) -> str:
        return "export_platform"

    @property
    def cli_flag_name(self) -> str:
        return "--export-to"

    @property
    def question_text(self) -> str:
        return "Export Platform"

    @property
    def section_title(self) -> str:
        return "Export Configuration"

    def _get_emoji(self) -> str:
        return "📤"

    def _prompt_user(self) -> Any:
        """Prompt user to select an export platform."""
        self.console.print("\n[bold cyan]📤 Select Export Platform[/bold cyan]")
        self.console.print("[dim]Press Ctrl+C at any time to cancel[/dim]\n")

        # Group platforms by configuration status
        configured, unconfigured = self._group_platforms_by_status()

        # Build choices
        choices = self._build_choices(configured, unconfigured)

        question = inquirer.List(
            'export_platform',
            message="Where would you like to export your roadmap?",
            choices=choices,
            carousel=True
        )

        answer = inquirer.prompt([question])

        if not answer:
            return self.SKIP

        selected = answer.get('export_platform')

        if selected == 'cancel':
            return 'cancel'

        # If unconfigured platform selected, show setup instructions
        if selected not in [self.FILE_ONLY, self.SKIP, 'cancel']:
            try:
                platform = ExportPlatform(selected)
                config = PLATFORM_CONFIGS[platform]
                if not config.is_configured():
                    self._show_setup_instructions(config)
                    # Re-prompt after showing instructions
                    return self._prompt_user()
            except ValueError:
                pass  # Not a valid platform, might be a special value

        return selected

    def _group_platforms_by_status(self) -> Tuple[List[Tuple[ExportPlatform, PlatformConfig]],
                                                   List[Tuple[ExportPlatform, PlatformConfig]]]:
        """Group platforms by configuration status.

        Returns:
            Tuple of (configured_platforms, unconfigured_platforms)
        """
        configured = []
        unconfigured = []

        for platform in ExportPlatform:
            config = PLATFORM_CONFIGS[platform]
            if config.is_configured():
                configured.append((platform, config))
            else:
                unconfigured.append((platform, config))

        return configured, unconfigured

    def _build_choices(
        self,
        configured: List[Tuple[ExportPlatform, PlatformConfig]],
        unconfigured: List[Tuple[ExportPlatform, PlatformConfig]]
    ) -> List:
        """Build the list of choices for the prompt.

        Args:
            configured: List of configured (platform, config) tuples
            unconfigured: List of unconfigured (platform, config) tuples

        Returns:
            List of choices for inquirer
        """
        choices = []

        # Configured platforms section
        if configured:
            choices.append(("═══ Configured Platforms (Ready to use) ═══", ""))
            for platform, config in configured:
                features_preview = ', '.join(config.features[:3])
                if len(config.features) > 3:
                    features_preview += '...'
                label = f"✅ {config.display_name} - {features_preview}"
                choices.append((label, platform.value))

        # Unconfigured platforms section
        if unconfigured:
            choices.append(("═══ Available Platforms (Requires setup) ═══", ""))
            for platform, config in unconfigured:
                missing = config.get_missing_vars()
                missing_preview = ', '.join(missing[:2])
                if len(missing) > 2:
                    missing_preview += f' (+{len(missing) - 2} more)'
                label = f"⚠️  {config.display_name} - Missing: {missing_preview}"
                choices.append((label, platform.value))

        # Other options section
        choices.append(("═══ Other Options ═══", ""))
        choices.append(("📁 File Export Only (CSV, JSON, YAML)", self.FILE_ONLY))
        choices.append(("❌ Skip Export", self.SKIP))
        choices.append(("🚫 Cancel", "cancel"))

        return choices

    def _show_setup_instructions(self, config: PlatformConfig) -> None:
        """Show setup instructions for an unconfigured platform.

        Args:
            config: Platform configuration
        """
        self.console.print(f"\n[yellow]{'=' * 60}[/yellow]")
        self.console.print(f"[yellow]⚠️  {config.display_name} requires configuration[/yellow]")
        self.console.print(f"[yellow]{'=' * 60}[/yellow]")

        self.console.print(f"\n[bold]Required environment variables:[/bold]")
        for var in config.required_env_vars:
            self.console.print(f"  [red]•[/red] {var}")

        if config.optional_env_vars:
            self.console.print(f"\n[bold]Optional environment variables:[/bold]")
            for var in config.optional_env_vars:
                self.console.print(f"  [dim]•[/dim] {var}")

        if config.setup_url:
            self.console.print(f"\n[bold]Setup guide:[/bold]")
            self.console.print(f"  [cyan]{config.setup_url}[/cyan]")

        self.console.print(f"\n[dim]Add these variables to your .env file and restart.[/dim]")
        self.console.print()

        input("Press Enter to select a different platform...")

    def _process_flag_value(self, flag_value: Any) -> Any:
        """Process the value from CLI flag.

        Args:
            flag_value: The CLI flag value

        Returns:
            Processed value
        """
        if flag_value is None:
            return None

        flag_value = str(flag_value).lower().strip()

        # Validate the value
        valid_values = [p.value for p in ExportPlatform] + [self.FILE_ONLY, self.SKIP]
        if flag_value not in valid_values:
            self.console.print(
                f"[yellow]⚠️  Unknown export platform '{flag_value}'. "
                f"Valid options: {', '.join(valid_values)}[/yellow]"
            )
            return None

        # Check if platform is configured
        if flag_value not in [self.FILE_ONLY, self.SKIP]:
            try:
                platform = ExportPlatform(flag_value)
                config = PLATFORM_CONFIGS[platform]
                if not config.is_configured():
                    missing = ', '.join(config.get_missing_vars())
                    self.console.print(
                        f"[yellow]⚠️  {config.display_name} is not configured. "
                        f"Missing: {missing}[/yellow]"
                    )
                    self.console.print(
                        f"[yellow]Setup guide: {config.setup_url}[/yellow]"
                    )
                    return None
            except ValueError:
                pass

        return flag_value

    def _format_value_for_display(self, value: Any) -> str:
        """Format value for display.

        Args:
            value: The value to format

        Returns:
            Formatted string
        """
        if value == self.FILE_ONLY:
            return "File Export Only"
        if value == self.SKIP:
            return "Skip Export"

        try:
            platform = ExportPlatform(value)
            config = PLATFORM_CONFIGS[platform]
            return config.display_name
        except (ValueError, KeyError):
            return str(value)

    def get_validation_error(self) -> Optional[str]:
        """Validate current value.

        Returns:
            Error message if invalid, None otherwise
        """
        if self._value is None:
            return None

        valid_values = [p.value for p in ExportPlatform] + [self.FILE_ONLY, self.SKIP]
        if self._value not in valid_values:
            return f"Invalid export platform: {self._value}"

        return None

    @staticmethod
    def get_available_platforms() -> List[str]:
        """Get list of all available platform values.

        Returns:
            List of platform string values
        """
        return [p.value for p in ExportPlatform]

    @staticmethod
    def get_configured_platforms() -> List[str]:
        """Get list of configured platform values.

        Returns:
            List of configured platform string values
        """
        return [
            p.value for p in ExportPlatform
            if PLATFORM_CONFIGS[p].is_configured()
        ]

    @staticmethod
    def get_platform_info(platform_value: str) -> Optional[Dict[str, Any]]:
        """Get information about a platform.

        Args:
            platform_value: Platform string value

        Returns:
            Platform info dict or None if not found
        """
        try:
            platform = ExportPlatform(platform_value)
            config = PLATFORM_CONFIGS[platform]
            return {
                'value': platform.value,
                'display_name': config.display_name,
                'is_configured': config.is_configured(),
                'missing_vars': config.get_missing_vars(),
                'features': config.features,
                'setup_url': config.setup_url,
            }
        except (ValueError, KeyError):
            return None

    def is_platform_value(self, value: Any) -> bool:
        """Check if a value is a platform (not file_only or skip).

        Args:
            value: Value to check

        Returns:
            True if value is a platform
        """
        if value in [self.FILE_ONLY, self.SKIP, None]:
            return False
        try:
            ExportPlatform(value)
            return True
        except ValueError:
            return False

    def get_selected_platform_config(self) -> Optional[PlatformConfig]:
        """Get the config for the selected platform.

        Returns:
            PlatformConfig if a platform is selected, None otherwise
        """
        if not self.is_platform_value(self._value):
            return None

        try:
            platform = ExportPlatform(self._value)
            return PLATFORM_CONFIGS[platform]
        except (ValueError, KeyError):
            return None
