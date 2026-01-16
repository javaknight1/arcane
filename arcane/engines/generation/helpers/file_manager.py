"""File management helper for roadmap generation."""

from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console

from arcane.protocols.display_protocols import ConsoleDisplayProtocol
from arcane.protocols.file_protocols import FileOperationsProtocol
from arcane.utils.logging_config import get_logger
from arcane.config import get_config

logger = get_logger(__name__)


class FileManager(FileOperationsProtocol):
    """Handles file operations for roadmap generation."""

    def __init__(self, console: ConsoleDisplayProtocol, output_directory: Optional[str] = None, project_name: Optional[str] = None):
        self.console = console
        self.config = get_config()

        # Set up base output directory
        if output_directory:
            base_output_dir = Path(output_directory)
        else:
            default_dir = self.config.get('files.default_output_dir', './output')
            base_output_dir = Path(default_dir)

        # Create subdirectory for this run
        timestamp_format = self.config.get('files.timestamp_format', '%Y%m%d_%H%M%S')
        timestamp = datetime.now().strftime(timestamp_format)

        # Option to include project name in directory if known upfront
        if project_name:
            run_dir_name = f"{project_name}_{timestamp}"
        else:
            run_dir_name = timestamp

        self._output_dir = base_output_dir / run_dir_name

        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._save_outputs = self.config.get('generation.save_outputs', True)

        if self._save_outputs:
            self.console.print(f"[dim]📁 Output directory: {self._output_dir}[/dim]")

    @property
    def output_dir(self) -> Optional[Path]:
        """Output directory for saving files."""
        return self._output_dir

    @property
    def save_outputs(self) -> bool:
        """Whether file outputs should be saved."""
        return self._save_outputs

    def extract_project_name(self, content: str) -> str:
        """Extract project name from content."""
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('PROJECT_NAME:'):
                return line.split(':', 1)[1].strip()
            elif line.strip().startswith('# ') and not line.strip().startswith('## '):
                return line.strip('# ').strip()
        return self.config.get('files.default_project_name', 'roadmap')

    def save_outline(self, outline: str, project_name: str) -> str:
        """Save outline to file."""
        if not self.save_outputs:
            raise ValueError("Output directory not configured")

        # Use simple filename without timestamp (timestamp is in directory)
        filename = f"{project_name}_outline.md"
        filepath = self._output_dir / filename

        with open(filepath, 'w') as f:
            f.write(outline)

        return str(filepath)

    def save_outline_prompt(self, prompt: str, project_name: str) -> str:
        """Save outline generation prompt to file."""
        if not self.save_outputs:
            raise ValueError("Output directory not configured")

        # Use simple filename without timestamp (timestamp is in directory)
        filename = f"{project_name}_outline_prompt.txt"
        filepath = self._output_dir / filename

        with open(filepath, 'w') as f:
            f.write(prompt)

        return str(filepath)

    def save_complete_roadmap(self, content: str, project_name: str) -> str:
        """Save complete roadmap to file."""
        if not self.save_outputs:
            raise ValueError("Output directory not configured")

        # Use simple filename without timestamp (timestamp is in directory)
        filename = f"{project_name}_complete.md"
        filepath = self._output_dir / filename

        with open(filepath, 'w') as f:
            f.write(content)

        self.console.print(f"[green]💾 Complete roadmap saved to: {filepath}[/green]")
        return str(filepath)

    def get_progress_filepath(self, project_name: str) -> str:
        """Get filepath for saving progress."""
        if not self.save_outputs:
            raise ValueError("Output directory not configured")

        # Use simple filename without timestamp (timestamp is in directory)
        filename = f"{project_name}_progress.json"
        return str(self._output_dir / filename)