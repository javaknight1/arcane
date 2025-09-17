"""Metadata extraction from LLM-generated roadmap content."""

import re
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ProjectMetadata:
    """Container for extracted project metadata."""
    project_name: str
    project_type: str = "Unknown"
    tech_stack: str = "To be determined"
    estimated_duration: str = "Unknown"
    team_size: str = "Unknown"
    description: str = "No description provided"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {
            'project_name': self.project_name,
            'project_type': self.project_type,
            'tech_stack': self.tech_stack,
            'estimated_duration': self.estimated_duration,
            'team_size': self.team_size,
            'description': self.description
        }

    def get_safe_filename_base(self) -> str:
        """Get a safe filename base from project name."""
        # Clean the project name for use in filenames
        safe_name = re.sub(r'[<>:"/\\|?*#\[\]{}]', '', self.project_name)
        safe_name = re.sub(r'\s+', '_', safe_name)
        safe_name = re.sub(r'_+', '_', safe_name)
        safe_name = safe_name.strip('_')

        # Limit length
        if len(safe_name) > 50:
            safe_name = safe_name[:50].strip('_')

        return safe_name or "roadmap_project"


class MetadataExtractor:
    """Extracts structured metadata from LLM output."""

    def extract_metadata(self, llm_output: str) -> tuple[ProjectMetadata, str]:
        """
        Extract metadata from LLM output and return clean roadmap content.

        Returns:
            tuple: (ProjectMetadata object, cleaned roadmap content)
        """
        # Look for metadata section
        metadata_pattern = r'===PROJECT_METADATA===(.*?)===END_METADATA==='
        metadata_match = re.search(metadata_pattern, llm_output, re.DOTALL)

        if metadata_match:
            metadata_text = metadata_match.group(1).strip()
            metadata = self._parse_metadata_text(metadata_text)

            # Remove metadata section from output
            cleaned_output = re.sub(metadata_pattern, '', llm_output, flags=re.DOTALL).strip()
        else:
            # Fallback: try to extract project name from markdown header
            project_name = self._extract_project_name_fallback(llm_output)
            metadata = ProjectMetadata(project_name=project_name)
            cleaned_output = llm_output

        return metadata, cleaned_output

    def _parse_metadata_text(self, metadata_text: str) -> ProjectMetadata:
        """Parse the metadata text section."""
        metadata = {}

        # Define field patterns
        field_patterns = {
            'PROJECT_NAME': r'PROJECT_NAME:\s*(.+)',
            'PROJECT_TYPE': r'PROJECT_TYPE:\s*(.+)',
            'TECH_STACK': r'TECH_STACK:\s*(.+)',
            'ESTIMATED_DURATION': r'ESTIMATED_DURATION:\s*(.+)',
            'TEAM_SIZE': r'TEAM_SIZE:\s*(.+)',
            'DESCRIPTION': r'DESCRIPTION:\s*(.+)'
        }

        # Extract each field
        for field, pattern in field_patterns.items():
            match = re.search(pattern, metadata_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip().strip('[]')  # Remove brackets if present
                metadata[field.lower()] = value

        # Create ProjectMetadata object with extracted values
        return ProjectMetadata(
            project_name=metadata.get('project_name', 'Unknown Project'),
            project_type=metadata.get('project_type', 'Unknown'),
            tech_stack=metadata.get('tech_stack', 'To be determined'),
            estimated_duration=metadata.get('estimated_duration', 'Unknown'),
            team_size=metadata.get('team_size', 'Unknown'),
            description=metadata.get('description', 'No description provided')
        )

    def _extract_project_name_fallback(self, text: str) -> str:
        """Fallback method to extract project name from markdown header."""
        # Look for first-level markdown header
        header_pattern = r'^#\s+([^#\n]+)'
        match = re.search(header_pattern, text, re.MULTILINE)

        if match:
            name = match.group(1).strip()
            # Clean the name
            name = re.sub(r'[^\w\s-]', '', name)
            name = re.sub(r'\s+', ' ', name)
            if len(name) > 50:
                name = name[:50].strip()
            return name or "Unknown Project"

        return "Unknown Project"

    def save_metadata(self, metadata: ProjectMetadata, filepath: str) -> None:
        """Save metadata to a JSON file."""
        import json
        from pathlib import Path

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Warning: Could not save metadata: {e}")