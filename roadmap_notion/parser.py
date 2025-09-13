#!/usr/bin/env python3
"""
Parse roadmap.txt and create structured CSV for Notion import
"""
import re
import csv
from typing import List, Dict, Optional, Tuple

class RoadmapParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.items = []
        self.current_milestone = None
        self.current_epic = None
        self.current_story = None
        
    def extract_duration(self, text: str) -> Optional[str]:
        """Extract duration hours from text"""
        duration_match = re.search(r'\*\*Duration:\*\*\s*(\d+)\s*hours?', text)
        if duration_match:
            return duration_match.group(1)
        return None
        
    def extract_priority(self, text: str) -> Optional[str]:
        """Extract priority from text"""
        priority_match = re.search(r'\*\*Priority:\*\*\s*(\w+)', text)
        if priority_match:
            return priority_match.group(1)
        return None
        
    def extract_goal(self, text: str) -> Optional[str]:
        """Extract goal/description from text"""
        goal_match = re.search(r'\*\*Goal:\*\*\s*(.+?)(?=\n|$)', text)
        if goal_match:
            return goal_match.group(1).strip()
        return None
        
    def extract_section_content(self, lines: List[str], start_idx: int) -> Tuple[str, List[str]]:
        """Extract content for a section until next section or end"""
        content_lines = []
        i = start_idx + 1
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Stop at next major section
            if (line.startswith('## **MILESTONE') or 
                line.startswith('## **Epic') or 
                line.startswith('### **Story') or 
                line.startswith('#### **Task')):
                break
                
            content_lines.append(lines[i])
            i += 1
            
        content = '\n'.join(content_lines)
        return content, content_lines
        
    def extract_benefits(self, content: str) -> Optional[str]:
        """Extract benefits section"""
        benefits_match = re.search(r'### \*\*Benefits:\*\*(.*?)(?=### |\n---|\Z)', content, re.DOTALL)
        if benefits_match:
            benefits = benefits_match.group(1).strip()
            # Clean up bullet points
            benefits = re.sub(r'^\s*-\s*', '', benefits, flags=re.MULTILINE)
            benefits = benefits.replace('\n', '; ')
            return benefits
        return None
        
    def extract_prerequisites(self, content: str) -> Optional[str]:
        """Extract prerequisites section"""
        prereq_match = re.search(r'### \*\*Prerequisites:\*\*(.*?)(?=### |\n---|\Z)', content, re.DOTALL)
        if prereq_match:
            prereqs = prereq_match.group(1).strip()
            prereqs = re.sub(r'^\s*-\s*', '', prereqs, flags=re.MULTILINE)
            prereqs = prereqs.replace('\n', '; ')
            return prereqs
        return None
        
    def extract_technical_requirements(self, content: str) -> Optional[str]:
        """Extract technical requirements section"""
        tech_match = re.search(r'### \*\*Technical Requirements:\*\*(.*?)(?=### |\n---|\Z)', content, re.DOTALL)
        if tech_match:
            tech = tech_match.group(1).strip()
            tech = re.sub(r'^\s*-\s*', '', tech, flags=re.MULTILINE)
            tech = tech.replace('\n', '; ')
            return tech
        return None
        
    def extract_claude_prompt(self, content: str) -> Optional[str]:
        """Extract Claude Code Prompt section"""
        prompt_match = re.search(r'\*\*Claude Code Prompt:\*\*\s*```(.*?)```', content, re.DOTALL)
        if prompt_match:
            return prompt_match.group(1).strip()
        return None
        
    def parse_file(self):
        """Parse the entire roadmap file"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Add project root
        self.items.append({
            'Name': 'Project Root',
            'Type': 'Project',
            'Parent': '',
            'Duration': '',
            'Priority': 'Critical',
            'Status': 'Not Started',
            'Goal/Description': 'Main project container',
            'Benefits': '',
            'Prerequisites': '',
            'Technical Requirements': '',
            'Claude Code Prompt': ''
        })
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Parse Milestones
            if line.startswith('## **MILESTONE'):
                milestone_match = re.match(r'## \*\*MILESTONE (\d+): ([^*]+)\*\*', line)
                if milestone_match:
                    milestone_num = milestone_match.group(1)
                    milestone_name = milestone_match.group(2).strip()
                    
                    content, _ = self.extract_section_content(lines, i)
                    
                    self.current_milestone = f"Milestone {milestone_num}: {milestone_name}"
                    
                    self.items.append({
                        'Name': self.current_milestone,
                        'Type': 'Milestone',
                        'Parent': 'Project Root',
                        'Duration': self.extract_duration(content) or '',
                        'Priority': self.extract_priority(content) or '',
                        'Status': 'Not Started',
                        'Goal/Description': self.extract_goal(content) or milestone_name,
                        'Benefits': self.extract_benefits(content) or '',
                        'Prerequisites': self.extract_prerequisites(content) or '',
                        'Technical Requirements': self.extract_technical_requirements(content) or '',
                        'Claude Code Prompt': self.extract_claude_prompt(content) or ''
                    })
                    
            # Parse Epics
            elif line.startswith('## **Epic'):
                epic_match = re.match(r'## \*\*Epic ([^*]+)\*\*', line)
                if epic_match:
                    epic_name = epic_match.group(1).strip()
                    
                    content, _ = self.extract_section_content(lines, i)
                    
                    self.current_epic = f"Epic {epic_name}"
                    
                    self.items.append({
                        'Name': self.current_epic,
                        'Type': 'Epic',
                        'Parent': self.current_milestone or '',
                        'Duration': self.extract_duration(content) or '',
                        'Priority': self.extract_priority(content) or '',
                        'Status': 'Not Started',
                        'Goal/Description': self.extract_goal(content) or epic_name,
                        'Benefits': self.extract_benefits(content) or '',
                        'Prerequisites': self.extract_prerequisites(content) or '',
                        'Technical Requirements': self.extract_technical_requirements(content) or '',
                        'Claude Code Prompt': self.extract_claude_prompt(content) or ''
                    })
                    
            # Parse Stories
            elif line.startswith('### **Story'):
                story_match = re.match(r'### \*\*Story ([^*]+)\*\*', line)
                if story_match:
                    story_name = story_match.group(1).strip()
                    
                    content, _ = self.extract_section_content(lines, i)
                    
                    self.current_story = f"Story {story_name}"
                    
                    # Extract "What it is" description
                    what_it_is_match = re.search(r'\*\*What it is:\*\*\s*(.+?)(?=\*\*|\n\n)', content)
                    description = what_it_is_match.group(1).strip() if what_it_is_match else story_name
                    
                    self.items.append({
                        'Name': self.current_story,
                        'Type': 'Story',
                        'Parent': self.current_epic or '',
                        'Duration': self.extract_duration(content) or '',
                        'Priority': self.extract_priority(content) or '',
                        'Status': 'Not Started',
                        'Goal/Description': description,
                        'Benefits': self.extract_benefits(content) or '',
                        'Prerequisites': self.extract_prerequisites(content) or '',
                        'Technical Requirements': self.extract_technical_requirements(content) or '',
                        'Claude Code Prompt': self.extract_claude_prompt(content) or ''
                    })
                    
            # Parse Tasks
            elif line.startswith('#### **Task'):
                task_match = re.match(r'#### \*\*Task ([^*]+)\*\*', line)
                if task_match:
                    task_name = task_match.group(1).strip()
                    
                    content, _ = self.extract_section_content(lines, i)
                    
                    current_task = f"Task {task_name}"
                    
                    # Extract "What to do" description
                    what_to_do_match = re.search(r'\*\*What to do:\*\*(.*?)(?=\*\*|$)', content, re.DOTALL)
                    description = what_to_do_match.group(1).strip() if what_to_do_match else task_name
                    
                    self.items.append({
                        'Name': current_task,
                        'Type': 'Task',
                        'Parent': self.current_story or '',
                        'Duration': self.extract_duration(content) or '',
                        'Priority': self.extract_priority(content) or '',
                        'Status': 'Not Started',
                        'Goal/Description': description,
                        'Benefits': self.extract_benefits(content) or '',
                        'Prerequisites': self.extract_prerequisites(content) or '',
                        'Technical Requirements': self.extract_technical_requirements(content) or '',
                        'Claude Code Prompt': self.extract_claude_prompt(content) or ''
                    })
            
            i += 1
    
    def write_csv(self, output_path: str):
        """Write parsed items to CSV"""
        fieldnames = [
            'Name', 'Type', 'Parent', 'Duration', 'Priority', 'Status',
            'Goal/Description', 'Benefits', 'Prerequisites', 
            'Technical Requirements', 'Claude Code Prompt'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.items)
    
    def get_item_count(self) -> Dict[str, int]:
        """Get count of items by type"""
        counts = {}
        for item in self.items:
            item_type = item['Type']
            counts[item_type] = counts.get(item_type, 0) + 1
        return counts

def parse_roadmap(input_file: str, output_file: str):
    """Main function to parse roadmap file and generate CSV"""
    print("Parsing roadmap file...")
    parser = RoadmapParser(input_file)
    parser.parse_file()
    
    print("Writing CSV file...")
    parser.write_csv(output_file)
    
    counts = parser.get_item_count()
    total_items = sum(counts.values())
    
    print(f"\nParsing completed successfully!")
    print(f"Total items parsed: {total_items}")
    print("\nBreakdown by type:")
    for item_type, count in counts.items():
        print(f"  {item_type}: {count}")
    
    print(f"\nCSV file created: {output_file}")
    return parser.items

def main():
    """CLI entry point"""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m roadmap_notion.parser <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'roadmap_output.csv'
    
    parse_roadmap(input_file, output_file)

if __name__ == "__main__":
    main()