#!/usr/bin/env python3
"""Comprehensive Roadmap Parser.

Parses roadmap.txt and generates a complete CSV file with all hierarchy levels:
- Project (root)
- Milestones
- Epics
- Stories
- Tasks
"""

import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RoadmapParser:
    def __init__(self):
        self.items = []
        self.current_milestone = None
        self.current_epic = None
        self.current_story = None
        self.milestones = {}
        self.epics = {}
        self.stories = {}

    def parse_file(self, filepath: str) -> List[Dict]:
        """Parse the roadmap.txt file and extract all hierarchy levels."""
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_item = None
        current_description = []
        current_benefits = []
        current_prerequisites = []
        current_tech_reqs = []
        current_prompt = []
        current_section = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for different item types and parse them
            item_patterns = [
                (r'^(Milestone|MILESTONE) \d+:', self._parse_milestone, 'milestone'),
                (r'^Epic \d+\.\d+:', self._parse_epic, 'epic'),
                (r'^(### \*\*Story |Story )', self._parse_story, 'story'),
                (r'^(### \*\*Task |Task )', self._parse_task, 'task')
            ]

            for pattern, parser_func, item_type in item_patterns:
                if re.match(pattern, line, re.IGNORECASE if 'MILESTONE' in pattern else 0):
                    if current_item:
                        self._save_current_item(current_item, current_description, current_benefits,
                                              current_prerequisites, current_tech_reqs, current_prompt)

                    current_item = parser_func(line)
                    self._update_current_context(item_type, current_item)
                    current_description, current_benefits, current_prerequisites, current_tech_reqs, current_prompt = [], [], [], [], []
                    current_section = None
                    break

            # Parse metadata fields
            elif line.startswith('**Duration:'):
                if current_item:
                    duration = line.replace('**Duration:**', '').strip()
                    current_item['Duration'] = self._parse_duration(duration)

            elif line.startswith('**Priority:'):
                if current_item:
                    priority = line.replace('**Priority:**', '').strip()
                    current_item['Priority'] = priority

            elif line.startswith('**Status:'):
                if current_item:
                    status = line.replace('**Status:**', '').strip()
                    current_item['Status'] = status

            elif line.startswith('**Goal:'):
                current_section = 'description'

            elif '**What it is and why we need it:**' in line:
                current_section = 'description'

            elif '**Benefits:**' in line:
                current_section = 'benefits'

            elif '**Prerequisites:**' in line:
                current_section = 'prerequisites'

            elif '**Technical Requirements:**' in line:
                current_section = 'tech_reqs'

            elif '**Claude Code Prompt:**' in line:
                current_section = 'prompt'

            # Collect content for current section
            elif current_section and line and not line.startswith('#'):
                if current_section == 'description':
                    current_description.append(line)
                elif current_section == 'benefits':
                    if line.startswith('- '):
                        current_benefits.append(line[2:])
                    elif line:
                        current_benefits.append(line)
                elif current_section == 'prerequisites':
                    if line.startswith('- '):
                        current_prerequisites.append(line[2:])
                    elif line:
                        current_prerequisites.append(line)
                elif current_section == 'tech_reqs':
                    if line.startswith('- '):
                        current_tech_reqs.append(line[2:])
                    elif line:
                        current_tech_reqs.append(line)
                elif current_section == 'prompt':
                    current_prompt.append(line)

            # Reset section on new headers
            if line.startswith('#') and not line.startswith('###'):
                current_section = None

            i += 1

        # Save the last item
        if current_item:
            self._save_current_item(current_item, current_description, current_benefits,
                                  current_prerequisites, current_tech_reqs, current_prompt)

        # Add project root if not exists
        self._ensure_project_root()

        return self.items

    def _update_current_context(self, item_type: str, current_item):
        """Update the current context based on item type."""
        if item_type == 'milestone':
            self.current_milestone = current_item
            self.current_epic = None
            self.current_story = None
        elif item_type == 'epic':
            self.current_epic = current_item
            self.current_story = None
        elif item_type == 'story':
            self.current_story = current_item

    def _save_current_item(self, item, description, benefits, prerequisites, tech_reqs, prompt):
        """Save the current item with its collected content."""
        content_mapping = {
            'Goal/Description': ' '.join(description).strip() if description else '',
            'Benefits': '; '.join(benefits).strip() if benefits else '',
            'Prerequisites': '; '.join(prerequisites).strip() if prerequisites else '',
            'Technical Requirements': '; '.join(tech_reqs).strip() if tech_reqs else '',
            'Claude Code Prompt': '\n'.join(prompt).strip() if prompt else ''
        }

        for key, value in content_mapping.items():
            if value:
                item[key] = value

        self.items.append(item)

    def _parse_milestone(self, line: str) -> Optional[Dict]:
        """Parse a milestone line (handles both Milestone and MILESTONE)."""
        match = re.match(r'^(?:Milestone|MILESTONE) (\d+): (.+?)(?:\s*\((.+?)\))?$', line, re.IGNORECASE)
        if match:
            number = match.group(1)
            title = match.group(2).strip()
            duration = match.group(3) if match.group(3) else ""

            item = {
                'Name': f"Milestone {number}: {title}",
                'Type': 'Milestone',
                'Parent': 'ServicePro Roadmap',  # Milestones parent to project root
                'Duration': self._parse_duration(duration),
                'Priority': 'Critical',
                'Status': 'Not Started',
                'Goal/Description': '',
                'Benefits': '',
                'Prerequisites': '',
                'Technical Requirements': '',
                'Claude Code Prompt': ''
            }
            self.milestones[number] = item
            return item
        return None

    def _parse_epic(self, line: str) -> Optional[Dict]:
        """Parse an epic line."""
        match = re.match(r'^Epic ([\d.]+): (.+?)(?:\s*\((.+?)\))?$', line)
        if match:
            number = match.group(1)
            title = match.group(2).strip()
            duration = match.group(3) if match.group(3) else ""

            # Determine parent based on epic number
            parent = ''
            if self.current_milestone:
                parent = self.current_milestone['Name']
            elif '.' in number:
                # Extract milestone number from epic number (e.g., 2.0 -> 2)
                milestone_num = number.split('.')[0]
                if milestone_num in self.milestones:
                    parent = self.milestones[milestone_num]['Name']
                else:
                    # Default to milestone based on number
                    parent = f"Milestone {milestone_num}: Unknown"

            item = {
                'Name': f"Epic {number}: {title}",
                'Type': 'Epic',
                'Parent': parent,
                'Duration': self._parse_duration(duration),
                'Priority': 'Critical',
                'Status': 'Not Started',
                'Goal/Description': '',
                'Benefits': '',
                'Prerequisites': '',
                'Technical Requirements': '',
                'Claude Code Prompt': ''
            }
            self.epics[number] = item
            return item
        return None

    def _parse_story(self, line: str) -> Optional[Dict]:
        """Parse a story line (handles markdown and plain format)."""
        # Remove markdown formatting if present
        clean_line = line.replace('### **', '').replace('**', '').strip()
        match = re.match(r'^Story ([\d.]+): (.+?)(?:\s*\((.+?)\))?$', clean_line)
        if match:
            number = match.group(1)
            title = match.group(2).strip()
            duration = match.group(3) if match.group(3) else ""

            # Determine parent based on story number
            parent = ''
            if self.current_epic:
                parent = self.current_epic['Name']
            elif '.' in number:
                # Try to find parent epic (e.g., 2.0.1 -> 2.0)
                parts = number.split('.')
                if len(parts) >= 2:
                    epic_num = f"{parts[0]}.{parts[1]}"
                    if epic_num in self.epics:
                        parent = self.epics[epic_num]['Name']
                    elif parts[0] in self.milestones:
                        parent = self.milestones[parts[0]]['Name']

            item = {
                'Name': f"Story {number}: {title}",
                'Type': 'Story',
                'Parent': parent,
                'Duration': self._parse_duration(duration),
                'Priority': 'High',
                'Status': 'Not Started',
                'Goal/Description': '',
                'Benefits': '',
                'Prerequisites': '',
                'Technical Requirements': '',
                'Claude Code Prompt': ''
            }
            self.stories[number] = item
            return item
        return None

    def _parse_task(self, line: str) -> Optional[Dict]:
        """Parse a task line (handles markdown and plain format)."""
        # Remove markdown formatting if present
        clean_line = line.replace('### **', '').replace('**', '').strip()
        match = re.match(r'^Task ([\d.]+): (.+?)(?:\s*\((.+?)\))?$', clean_line)
        if match:
            number = match.group(1)
            title = match.group(2).strip()
            duration = match.group(3) if match.group(3) else ""

            # Determine parent based on task number
            parent = ''
            if self.current_story:
                parent = self.current_story['Name']
            elif '.' in number:
                # Try to find parent story (e.g., 2.0.1.1 -> 2.0.1)
                parts = number.split('.')
                if len(parts) >= 3:
                    story_num = f"{parts[0]}.{parts[1]}.{parts[2]}"
                    if story_num in self.stories:
                        parent = self.stories[story_num]['Name']

            item = {
                'Name': f"Task {number}: {title}",
                'Type': 'Task',
                'Parent': parent,
                'Duration': self._parse_duration(duration),
                'Priority': 'Medium',
                'Status': 'Not Started',
                'Goal/Description': '',
                'Benefits': '',
                'Prerequisites': '',
                'Technical Requirements': '',
                'Claude Code Prompt': ''
            }
            return item
        return None

    def _parse_duration(self, duration_str: str) -> str:
        """Parse duration string and extract hours."""
        if not duration_str:
            return ''

        duration_patterns = [
            (r'(\d+)\s*hours?', 1),
            (r'(\d+)\s*days?', 8),
            (r'(\d+)\s*weeks?', 40),
            (r'(\d+)\s*months?', 160)
        ]

        for pattern, multiplier in duration_patterns:
            match = re.search(pattern, duration_str, re.IGNORECASE)
            if match:
                return str(int(match.group(1)) * multiplier)

        return ''

    def _ensure_project_root(self):
        """Ensure there's a project root item."""
        has_root = any(item['Type'] == 'Project' for item in self.items)
        if not has_root:
            root_item = {
                'Name': 'ServicePro Roadmap',
                'Type': 'Project',
                'Parent': '',
                'Duration': '',
                'Priority': 'Critical',
                'Status': 'Not Started',
                'Goal/Description': 'Complete roadmap for ServicePro field service management SaaS application',
                'Benefits': '',
                'Prerequisites': '',
                'Technical Requirements': '',
                'Claude Code Prompt': ''
            }
            self.items.insert(0, root_item)

    def save_to_csv(self, output_path: str):
        """Save parsed items to CSV file."""
        if not self.items:
            print("❌ No items to save!")
            return

        fieldnames = [
            'Name', 'Type', 'Parent', 'Duration', 'Priority', 'Status',
            'Goal/Description', 'Benefits', 'Prerequisites',
            'Technical Requirements', 'Claude Code Prompt'
        ]

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.items)

        self._print_summary(output_path)

    def _print_summary(self, output_path: str):
        """Print parsing summary."""
        print(f"\n✅ Successfully created {output_path}")
        print(f"\n📊 Summary of items extracted:")

        type_counts = {}
        for item in self.items:
            item_type = item['Type']
            type_counts[item_type] = type_counts.get(item_type, 0) + 1

        item_types = ['Project', 'Milestone', 'Epic', 'Story', 'Task']
        for item_type in item_types:
            if item_type in type_counts:
                print(f"  - {item_type}: {type_counts[item_type]}")

        print(f"\n📁 Total items: {len(self.items)}")


def parse_roadmap(file_path: str, output_path: str = None) -> List[Dict]:
    """
    Parse a roadmap text file and optionally save to CSV.

    Args:
        file_path: Path to the roadmap.txt file
        output_path: Optional path to save CSV file

    Returns:
        List of parsed roadmap items
    """
    parser = RoadmapParser()
    items = parser.parse_file(file_path)

    if output_path:
        parser.save_to_csv(output_path)

    return items


def main():
    """Main function to run the parser."""
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'roadmap.txt'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'complete_roadmap.csv'

    if not Path(input_file).exists():
        print(f"❌ Error: Input file '{input_file}' not found!")
        print("\nUsage: python parser.py [input_file] [output_file]")
        print("  Default: python parser.py roadmap.txt complete_roadmap.csv")
        sys.exit(1)

    print(f"📖 Parsing {input_file}...")
    parse_roadmap(input_file, output_file)
    print(f"\n✨ Done! You can now import {output_file} into Notion.")


if __name__ == "__main__":
    main()