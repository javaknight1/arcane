"""Idea processing module for structuring raw project ideas into comprehensive templates."""

import re
from typing import Dict, Any, Optional, List


class IdeaProcessor:
    """Processes raw project ideas and structures them into comprehensive templates."""

    def __init__(self):
        self.idea_template = self._load_idea_template()

    def process_idea(self, raw_idea: str) -> Dict[str, Any]:
        """Process raw idea text into structured template data."""
        # Extract key components from the idea
        project_name = self._extract_project_name(raw_idea)
        problem_statement = self._extract_problem_statement(raw_idea)
        solution_overview = self._extract_solution_overview(raw_idea)
        key_features = self._extract_key_features(raw_idea)
        target_users = self._extract_target_users(raw_idea)
        technical_details = self._extract_technical_details(raw_idea)
        constraints = self._extract_constraints(raw_idea)

        return {
            'project_name': project_name,
            'problem_statement': problem_statement,
            'solution_overview': solution_overview,
            'key_features': key_features,
            'target_users': target_users,
            'technical_details': technical_details,
            'constraints': constraints,
            'raw_idea': raw_idea
        }

    def build_structured_prompt(self, processed_idea: Dict[str, Any]) -> str:
        """Build a structured prompt from processed idea data."""
        return self.idea_template.format(**processed_idea)

    def _extract_project_name(self, text: str) -> str:
        """Extract a concise project name from the idea text."""
        # Clean text first to remove problematic content
        clean_text = re.sub(r'```[^`]*```', '', text)  # Remove code blocks
        clean_text = re.sub(r'`+', '', clean_text)  # Remove backticks

        # Look for explicit project name patterns
        patterns = [
            r'(?:Project|App|Tool|Platform|System|Service):\s*([^\n.!?]+)',
            r'I want (?:to create|to build|to develop)\s+(?:a|an)\s+([^.!?]+?)(?:\s+(?:app|tool|platform|system|service))',
            r'(?:Building|Creating|Developing)\s+(?:a|an)\s+([^.!?]+?)(?:\s+(?:app|tool|platform|system|service))',
            r'^#\s*([^#\n-]+?)(?:\s*-|\n|$)',  # Markdown header (first level only)
            r'fullstack\s+version\s+of\s+([^.!?\n]+)',
            r'(?:website|web\s+app|platform)\s+(?:should|that|to)\s+([^.!?\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Clean and validate the name
                name = re.sub(r'\s+', ' ', name)
                name = re.sub(r'[^\w\s-]', '', name)  # Keep only alphanumeric, spaces, hyphens

                # Skip if too generic or problematic
                generic_terms = ['this', 'that', 'the', 'a', 'an', 'and', 'or', 'but', 'it', 'they']
                if name.lower() not in generic_terms and len(name.strip()) > 3:
                    if len(name) > 80:
                        name = name[:77] + "..."
                    return name

        # Fallback: Look for key concepts in the text
        key_concepts = []
        concept_patterns = [
            r'\b(roadmap|CLI|tool|platform|app|website|system|service)\b',
            r'\b(fullstack|web|mobile|desktop)\b',
            r'\b(management|tracking|generation|automation)\b'
        ]

        for pattern in concept_patterns:
            matches = re.findall(pattern, clean_text, re.IGNORECASE)
            key_concepts.extend([m.title() for m in matches[:2]])  # Limit to 2 per pattern

        if key_concepts:
            # Create a name from key concepts
            unique_concepts = list(dict.fromkeys(key_concepts))  # Remove duplicates, preserve order
            name = ' '.join(unique_concepts[:3])  # Use up to 3 concepts
            if name:
                return f"{name} Project"

        return "Roadmap Generation Platform"

    def _extract_problem_statement(self, text: str) -> str:
        """Extract the problem statement from the idea."""
        patterns = [
            r'(?:Problem|Issue|Challenge):\s*([^#\n]+(?:\n[^#\n]+)*)',
            r'(?:solves?|addresses?|tackles?)\s+(?:the\s+)?([^.]+)',
            r'(?:struggle with|difficult to|hard to|problem with)\s+([^.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        # Fallback: use first paragraph if it seems like a problem statement
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 1 and len(paragraphs[0]) > 50:
            return paragraphs[0].strip()

        return "No specific problem statement identified."

    def _extract_solution_overview(self, text: str) -> str:
        """Extract solution overview from the idea."""
        patterns = [
            r'(?:Solution|Approach|Strategy):\s*([^#\n]+(?:\n[^#\n]+)*)',
            r'(?:will|would|should)\s+(?:create|build|develop|provide)\s+([^.]+)',
            r'(?:app|tool|platform|system|service)\s+(?:that|which)\s+([^.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return "Comprehensive solution to be developed."

    def _extract_key_features(self, text: str) -> List[str]:
        """Extract key features from the idea."""
        features = []

        # Look for explicit feature lists
        feature_section = re.search(
            r'(?:Features?|Functionality|Capabilities?):\s*\n((?:[-*]\s*.+\n?)+)',
            text, re.IGNORECASE | re.MULTILINE
        )

        if feature_section:
            feature_text = feature_section.group(1)
            features = re.findall(r'[-*]\s*(.+)', feature_text)
        else:
            # Look for bullet points anywhere in text
            features = re.findall(r'[-*]\s*(.+)', text)

        # Clean and filter features
        cleaned_features = []
        for feature in features:
            feature = feature.strip()
            if len(feature) > 10 and len(feature) < 200:
                cleaned_features.append(feature)

        return cleaned_features[:10]  # Limit to 10 features

    def _extract_target_users(self, text: str) -> str:
        """Extract target user information."""
        patterns = [
            r'(?:Target\s+)?(?:Users?|Audience|Customers?):\s*([^#\n]+)',
            r'(?:for|targeting|aimed at)\s+([^.]+?)(?:\s+who|\s+that|\.)',
            r'(?:businesses|companies|organizations|teams|individuals)\s+([^.]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "General users requiring this solution."

    def _extract_technical_details(self, text: str) -> str:
        """Extract technical requirements and details."""
        tech_keywords = [
            'web', 'mobile', 'api', 'database', 'cloud', 'frontend', 'backend',
            'react', 'python', 'node', 'sql', 'nosql', 'microservices',
            'authentication', 'real-time', 'scalable', 'responsive'
        ]

        technical_sentences = []
        sentences = text.split('.')

        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in tech_keywords):
                technical_sentences.append(sentence.strip())

        if technical_sentences:
            return '. '.join(technical_sentences[:5])

        return "Technical requirements to be determined based on project scope."

    def _extract_constraints(self, text: str) -> str:
        """Extract project constraints and limitations."""
        constraint_patterns = [
            r'(?:Constraints?|Limitations?|Budget|Timeline|Resources?):\s*([^#\n]+)',
            r'(?:must|should|need to)\s+(?:be|have|support)\s+([^.]+)',
            r'(?:within|under|by)\s+([^.]+?)(?:\s+(?:budget|timeline|deadline))',
        ]

        constraints = []
        for pattern in constraint_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            constraints.extend(matches)

        if constraints:
            return '. '.join(constraint.strip() for constraint in constraints[:3])

        return "Standard project constraints apply."

    def _load_idea_template(self) -> str:
        """Load the comprehensive idea template."""
        return """# Comprehensive Project Analysis for Roadmap Generation

## Executive Summary
**Project Name**: {project_name}
**Problem Statement**: {problem_statement}
**Solution Overview**: {solution_overview}

## Detailed Project Scope

### Core Features and Functionality
{key_features_formatted}

### Target Users and Market
{target_users}

### Technical Architecture Requirements
{technical_details}

### Project Constraints and Considerations
{constraints}

## Complete Original Idea Context
{raw_idea}

---

## Critical Roadmap Generation Instructions

**SCOPE REQUIREMENT**: This project requires a COMPLETE, COMPREHENSIVE roadmap covering:

1. **Full Development Lifecycle**: From initial setup through deployment and maintenance
2. **All Feature Areas**: Every feature mentioned must have dedicated epics, stories, and tasks
3. **Complete Technical Stack**: Frontend, backend, database, deployment, testing, security
4. **Project Management**: Setup, CI/CD, documentation, team processes
5. **Quality Assurance**: Testing strategies, code quality, performance optimization
6. **Business Requirements**: User experience, analytics, monitoring, support

**COMPLETENESS MANDATE**: You MUST generate ALL items for EVERY milestone, epic, and story. Do not summarize, skip, or abbreviate. Every story needs its full complement of tasks (typically 4-8 tasks per story). Every epic needs its full complement of stories (typically 3-6 stories per epic).

**DETAIL REQUIREMENT**: Each item MUST include comprehensive, actionable content for:
- Goal/Description: Detailed explanation of what needs to be accomplished
- Benefits: Clear business and technical value proposition
- Prerequisites: Specific dependencies and requirements
- Technical Requirements: Detailed implementation specifications
- Claude Code Prompt: Specific, actionable implementation guidance

Generate a roadmap that is production-ready and implementation-focused, suitable for immediate development use."""

    def format_features(self, features: List[str]) -> str:
        """Format features list for the template."""
        if not features:
            return "• Core functionality to be defined during planning phase"

        formatted = []
        for feature in features:
            if not feature.startswith(('•', '-', '*')):
                feature = f"• {feature}"
            formatted.append(feature)

        return '\n'.join(formatted)