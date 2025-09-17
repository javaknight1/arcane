"""File export engine for generating various output formats."""

import csv
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

from arcane.items import Roadmap
from arcane.constants import CSV_FIELDNAMES, EXPORT_FORMATS


class FileExportEngine:
    """Engine for exporting roadmap data to various file formats."""

    def __init__(self):
        self.supported_formats = EXPORT_FORMATS

    def export(
        self,
        roadmap: Roadmap,
        output_path: str,
        format: str = 'csv'
    ) -> str:
        """Export roadmap to specified format."""
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.supported_formats}")

        output_path = Path(output_path)

        if format == 'csv':
            return self._export_csv(roadmap, output_path)
        elif format == 'json':
            return self._export_json(roadmap, output_path)
        elif format == 'yaml':
            return self._export_yaml(roadmap, output_path)

    def _export_csv(self, roadmap: Roadmap, output_path: Path) -> str:
        """Export roadmap to CSV format."""
        items = roadmap.to_dict_list()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(items)

        self._print_export_summary('CSV', output_path, roadmap)
        return str(output_path)

    def _export_json(self, roadmap: Roadmap, output_path: Path) -> str:
        """Export roadmap to JSON format."""
        data = {
            'project': {
                'name': roadmap.project.name,
                'description': roadmap.project.description,
                'statistics': roadmap.get_statistics()
            },
            'hierarchy': self._build_hierarchy_json(roadmap.project),
            'flat_items': roadmap.to_dict_list()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._print_export_summary('JSON', output_path, roadmap)
        return str(output_path)

    def _export_yaml(self, roadmap: Roadmap, output_path: Path) -> str:
        """Export roadmap to YAML format."""
        data = {
            'project': {
                'name': roadmap.project.name,
                'description': roadmap.project.description,
                'statistics': roadmap.get_statistics()
            },
            'hierarchy': self._build_hierarchy_dict(roadmap.project),
            'items': roadmap.to_dict_list()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        self._print_export_summary('YAML', output_path, roadmap)
        return str(output_path)

    def _build_hierarchy_json(self, item: Any) -> Dict[str, Any]:
        """Build hierarchical JSON representation of items."""
        result = {
            'name': item.name,
            'type': item.item_type,
            'status': item.status,
            'priority': item.priority,
            'duration': item.duration,
            'description': item.description,
            'benefits': item.benefits,
            'prerequisites': item.prerequisites,
            'technical_requirements': item.technical_requirements,
            'claude_code_prompt': item.claude_code_prompt,
            'children': []
        }

        for child in item.children:
            result['children'].append(self._build_hierarchy_json(child))

        return result

    def _build_hierarchy_dict(self, item: Any) -> Dict[str, Any]:
        """Build hierarchical dictionary representation for YAML."""
        result = {
            'name': item.name,
            'type': item.item_type,
            'metadata': {
                'status': item.status,
                'priority': item.priority,
                'duration': item.duration if item.duration else None
            }
        }

        if item.description:
            result['description'] = item.description
        if item.benefits:
            result['benefits'] = item.benefits
        if item.prerequisites:
            result['prerequisites'] = item.prerequisites
        if item.technical_requirements:
            result['technical_requirements'] = item.technical_requirements
        if item.claude_code_prompt:
            result['claude_code_prompt'] = item.claude_code_prompt

        if item.children:
            result['children'] = [self._build_hierarchy_dict(child) for child in item.children]

        return result

    def _print_export_summary(self, format: str, output_path: Path, roadmap: Roadmap) -> None:
        """Print export summary."""
        stats = roadmap.get_statistics()
        print(f"\n✅ Successfully exported to {format}: {output_path}")
        print(f"\n📊 Roadmap Summary:")
        print(f"  - Project: {roadmap.project.name}")
        print(f"  - Milestones: {stats['milestones']}")
        print(f"  - Epics: {stats['epics']}")
        print(f"  - Stories: {stats['stories']}")
        print(f"  - Tasks: {stats['tasks']}")
        print(f"  - Total Items: {stats['total_items']}")
        if stats['total_duration_hours']:
            print(f"  - Estimated Duration: {stats['total_duration_hours']} hours")

    def export_multiple(
        self,
        roadmap: Roadmap,
        base_path: str,
        formats: List[str] = None
    ) -> List[str]:
        """Export roadmap to multiple formats."""
        formats = formats or self.supported_formats
        exported_files = []

        base_path = Path(base_path)
        base_name = base_path.stem

        for format in formats:
            output_path = base_path.parent / f"{base_name}.{format}"
            exported_file = self.export(roadmap, str(output_path), format)
            exported_files.append(exported_file)

        return exported_files