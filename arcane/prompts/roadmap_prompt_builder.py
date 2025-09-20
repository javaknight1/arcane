#!/usr/bin/env python3
"""Roadmap generation prompt builder."""

from pathlib import Path
from typing import Dict, Any, Optional
from .base_prompt_builder import BasePromptBuilder
from ..constants.templates import PROMPT_TEMPLATES


class RoadmapPromptBuilder(BasePromptBuilder):
    """Builds comprehensive prompts for roadmap generation."""

    def build_prompt(self, idea_content: str, preferences: Dict[str, Any],
                    idea_file_path: Optional[str] = None) -> str:
        """Build roadmap generation prompt.

        Args:
            idea_content: The project idea description
            preferences: Dictionary of user preferences
            idea_file_path: Optional path to idea file for additional context

        Returns:
            Complete formatted prompt for LLM
        """
        # Prepare all variables
        variables = self._prepare_all_variables(idea_content, preferences)

        # Add contextual analysis
        variables.update(self._generate_contextual_analysis(preferences))

        # Format the template
        return self._format_template(self.template, variables)

    def build_outline_prompt(self, idea_content: str, preferences: Dict[str, Any]) -> str:
        """Build outline generation prompt specifically.

        Args:
            idea_content: The project idea description
            preferences: Dictionary of user preferences

        Returns:
            Complete formatted outline prompt for LLM
        """
        # Use the outline_generation template
        outline_template = PROMPT_TEMPLATES['outline_generation']

        # Prepare variables for outline template
        variables = {
            'idea_content': idea_content,
            'timeline': preferences.get('timeline', '6-months'),
            'complexity': preferences.get('complexity') or preferences.get('calculated_complexity', 'moderate'),
            'team_size': preferences.get('team_size', '2-3'),
            'focus': preferences.get('focus', 'mvp')
        }

        # Format the outline template
        return self._format_template(outline_template, variables)

    def _prepare_all_variables(self, idea_content: str, preferences: Dict[str, Any]) -> Dict[str, str]:
        """Prepare all variables for the template."""
        # Start with the idea content
        variables = {'idea_content': idea_content}

        # Add basic preferences (direct mapping)
        formatted_prefs = self._prepare_variables(preferences)
        variables.update(formatted_prefs)

        # Add mapped variables (fix naming mismatches)
        variables.update(self._map_question_responses_to_template_variables(preferences))

        # Add computed/derived variables
        variables.update(self._compute_derived_variables(preferences))

        # Add contextual analysis
        variables.update(self._generate_contextual_analysis(preferences))

        return variables

    def _map_question_responses_to_template_variables(self, preferences: Dict[str, Any]) -> Dict[str, str]:
        """Map question responses to template variable names."""
        mappings = {}

        # Fix naming mismatches
        if 'regulatory' in preferences:
            mappings['regulatory_requirements'] = preferences['regulatory']

        # Process roadmap aspects
        roadmap_aspects = preferences.get('roadmap_aspects', ['technical-only'])
        mappings['roadmap_aspects'] = self._format_roadmap_aspects(roadmap_aspects)
        mappings['non_technical_focus_areas'] = self._format_non_technical_focus_areas(roadmap_aspects)
        mappings['roadmap_coverage_description'] = self._generate_roadmap_coverage_description(roadmap_aspects)

        # Set defaults for missing basic variables that template expects
        mappings.update({
            'target_market': preferences.get('target_market', 'Not specified'),
            'market_maturity': preferences.get('market_maturity', 'Not specified'),
            'complexity': preferences.get('complexity', preferences.get('calculated_complexity', 'moderate')),
        })

        return self._prepare_variables(mappings)

    def _compute_derived_variables(self, preferences: Dict[str, Any]) -> Dict[str, str]:
        """Compute derived variables from question responses."""
        derived = {}

        # Calculate complexity if not explicitly set
        complexity_factors = []
        if preferences.get('technical_challenges'):
            complexity_factors.extend(preferences['technical_challenges'])
        if preferences.get('scaling_expectations') == 'viral':
            complexity_factors.append('high_scaling')
        if preferences.get('regulatory') and 'gdpr' in str(preferences['regulatory']).lower():
            complexity_factors.append('regulatory_compliance')

        derived['calculated_complexity'] = 'complex' if len(complexity_factors) >= 3 else 'moderate' if len(complexity_factors) >= 1 else 'simple'

        # Count integrations
        integration_count = 0
        integration_types = ['payment_integrations', 'communication_integrations', 'business_integrations', 'developer_integrations', 'data_integrations']
        for integration_type in integration_types:
            if preferences.get(integration_type):
                integration_list = preferences[integration_type]
                if isinstance(integration_list, list):
                    integration_count += len(integration_list)
                elif integration_list != 'none':
                    integration_count += 1

        derived['integration_count'] = str(integration_count)
        derived['integration_complexity'] = 'high' if integration_count >= 5 else 'moderate' if integration_count >= 2 else 'low'

        # Calculate velocity multiplier based on team expertise and methodology
        velocity = 1.0
        if preferences.get('team_expertise') == 'expert':
            velocity *= 1.3
        elif preferences.get('team_expertise') == 'beginner':
            velocity *= 0.7

        if preferences.get('dev_methodology') == 'agile':
            velocity *= 1.2
        elif preferences.get('dev_methodology') == 'waterfall':
            velocity *= 0.9

        derived['velocity_multiplier'] = f"{velocity:.1f}x"

        # Assess risks
        derived['technical_risk'] = 'high' if derived['calculated_complexity'] == 'complex' else 'moderate' if derived['calculated_complexity'] == 'moderate' else 'low'
        derived['budget_risk'] = 'high' if preferences.get('budget_range') == 'bootstrap' else 'moderate' if preferences.get('budget_range') == 'startup' else 'low'
        derived['team_risk'] = 'high' if preferences.get('team_size') == '1' else 'moderate' if preferences.get('team_expertise') == 'beginner' else 'low'

        # Overall risk score
        risk_factors = [derived['technical_risk'], derived['budget_risk'], derived['team_risk']]
        high_risks = risk_factors.count('high')
        derived['overall_risk_score'] = 'high' if high_risks >= 2 else 'moderate' if high_risks >= 1 else 'low'

        # Architecture constraints
        constraints = []
        if preferences.get('budget_range') == 'bootstrap':
            constraints.append('cost-optimized')
        if preferences.get('regulatory') and any(req in str(preferences['regulatory']).lower() for req in ['hipaa', 'gdpr']):
            constraints.append('compliance-required')
        if preferences.get('deployment_environment') == 'on-premise':
            constraints.append('on-premise-only')

        derived['architecture_constraints'] = ', '.join(constraints) if constraints else 'flexible'

        # Generate recommended KPIs based on success metric
        success_metric = preferences.get('success_metric', 'user_adoption')
        kpi_map = {
            'user_adoption': 'Monthly Active Users, User Retention Rate, Feature Adoption Rate',
            'revenue': 'Monthly Recurring Revenue, Customer Acquisition Cost, Lifetime Value',
            'engagement': 'Session Duration, Page Views, Daily Active Users',
            'performance': 'Response Time, Uptime, Error Rate'
        }
        derived['recommended_kpis'] = kpi_map.get(success_metric, 'Custom metrics based on project goals')

        return self._prepare_variables(derived)

    def _generate_contextual_analysis(self, preferences: Dict[str, Any]) -> Dict[str, str]:
        """Generate contextual analysis based on preferences."""
        analysis = {}

        # Architecture recommendation
        analysis['recommended_architecture'] = self._recommend_architecture(preferences)

        # Technology stack suggestions
        analysis['tech_stack_recommendations'] = self._suggest_tech_stack(preferences)

        # Risk assessment summary
        analysis['risk_assessment'] = self._assess_risks(preferences)

        # Timeline feasibility
        analysis['timeline_feasibility'] = self._assess_timeline_feasibility(preferences)

        # Key constraints
        analysis['key_constraints'] = self._identify_constraints(preferences)

        return analysis

    def _recommend_architecture(self, preferences: Dict[str, Any]) -> str:
        """Recommend architecture based on preferences."""
        factors = []

        # Budget considerations
        if preferences.get('budget_range') == 'bootstrap':
            factors.append("Budget-conscious architecture recommended")

        # Scaling considerations
        if preferences.get('scaling_expectations') == 'viral':
            factors.append("Highly scalable architecture required")

        # Team size considerations
        if preferences.get('team_size') == '1':
            factors.append("Simple, maintainable architecture for solo developer")

        # Complexity considerations
        complexity = preferences.get('calculated_complexity') or preferences.get('complexity')
        if complexity == 'complex':
            factors.append("Modular architecture to handle complexity")

        return "; ".join(factors) if factors else "Standard web application architecture"

    def _suggest_tech_stack(self, preferences: Dict[str, Any]) -> str:
        """Suggest technology stack based on preferences."""
        suggestions = []

        # Industry-specific suggestions
        industry = preferences.get('industry', '')
        if industry == 'healthcare':
            suggestions.append("HIPAA-compliant technologies")
        elif industry == 'finance':
            suggestions.append("Security-first tech stack")

        # Budget-based suggestions
        if preferences.get('budget_range') == 'bootstrap':
            suggestions.append("Open-source solutions preferred")

        # Deployment-based suggestions
        if preferences.get('deployment_environment') == 'serverless':
            suggestions.append("Serverless-compatible technologies")

        return "; ".join(suggestions) if suggestions else "Standard modern tech stack"

    def _assess_risks(self, preferences: Dict[str, Any]) -> str:
        """Assess project risks based on preferences."""
        risks = []

        if preferences.get('technical_risk') == 'high':
            risks.append("High technical complexity risk")

        if preferences.get('budget_risk') == 'high':
            risks.append("Budget constraint risk")

        if preferences.get('team_risk') == 'high':
            risks.append("Team capacity risk")

        timeline = preferences.get('timeline', '')
        team_size = preferences.get('team_size', '')
        if team_size == '1' and timeline == '3-months':
            risks.append("Aggressive timeline for solo developer")

        return "; ".join(risks) if risks else "Low to moderate risk profile"

    def _assess_timeline_feasibility(self, preferences: Dict[str, Any]) -> str:
        """Assess timeline feasibility."""
        timeline = preferences.get('timeline', '')
        complexity = preferences.get('calculated_complexity') or preferences.get('complexity', '')
        team_size = preferences.get('team_size', '')

        if timeline == '3-months' and complexity == 'complex':
            return "Aggressive timeline - recommend MVP approach"
        elif timeline == '12-months' and complexity == 'simple':
            return "Conservative timeline - opportunity for additional features"
        else:
            return "Timeline appears reasonable for scope"

    def _identify_constraints(self, preferences: Dict[str, Any]) -> str:
        """Identify key project constraints."""
        constraints = []

        # Regulatory constraints
        regulatory = preferences.get('regulatory_requirements', '')
        if 'hipaa' in regulatory.lower():
            constraints.append("HIPAA compliance required")
        if 'gdpr' in regulatory.lower():
            constraints.append("GDPR compliance required")

        # Budget constraints
        if preferences.get('budget_range') == 'bootstrap':
            constraints.append("Minimal budget constraints")

        # Technical constraints
        if preferences.get('deployment_environment') == 'on-premise':
            constraints.append("On-premise deployment requirement")

        return "; ".join(constraints) if constraints else "No major constraints identified"

    def build_custom_prompt(self, template_name: str, **kwargs) -> str:
        """Build a prompt using a specific template from the constants."""
        from ..constants.templates import PROMPT_TEMPLATES

        if template_name not in PROMPT_TEMPLATES:
            raise ValueError(f"Template '{template_name}' not found in PROMPT_TEMPLATES")

        template = PROMPT_TEMPLATES[template_name]
        return self._format_template(template, kwargs)

    def _get_template(self) -> str:
        """Get the comprehensive roadmap generation template."""
        return """# AI Roadmap Generation Request

## Project Overview
{idea_content}

## Project Preferences

### Timeline & Scope
- **Timeline:** {timeline}
- **Primary Focus:** {focus}
- **Complexity Level:** {complexity}

### Industry & Market Context
- **Industry/Domain:** {industry}
- **Target Market:** {target_market}
- **Market Maturity:** {market_maturity}
- **Regulatory Requirements:** {regulatory_requirements}

### Technical Architecture
- **Technical Challenges:** {technical_challenges}
- **Calculated Complexity:** {calculated_complexity}
- **Deployment Environment:** {deployment_environment}
- **Geographic Distribution:** {geographic_distribution}
- **Scaling Pattern:** {scaling_expectations}

### Team & Resources
- **Team Size:** {team_size}
- **Team Expertise:** {team_expertise}
- **Team Distribution:** {team_distribution}
- **Development Methodology:** {dev_methodology}
- **Velocity Multiplier:** {velocity_multiplier}

### Financial Constraints
- **Overall Budget:** {budget_range}
- **Infrastructure Budget:** {infra_budget}
- **Services Budget:** {services_budget}
- **Architecture Constraints:** {architecture_constraints}

### Integration Requirements
- **Payment Systems:** {payment_integrations}
- **Communication Services:** {communication_integrations}
- **Business Tools:** {business_integrations}
- **Developer Tools:** {developer_integrations}
- **Data Sources:** {data_integrations}
- **Integration Count:** {integration_count}
- **Integration Complexity:** {integration_complexity}

### Success Definition
- **Primary Success Metric:** {success_metric}
- **Success Timeline:** {success_timeline}
- **Measurement Approach:** {measurement_approach}
- **Acceptable Failure Rate:** {failure_tolerance}
- **Recommended KPIs:** {recommended_kpis}

## Contextual Analysis

### Architecture Recommendation
{recommended_architecture}

### Technology Stack Suggestions
{tech_stack_recommendations}

### Risk Assessment
{risk_assessment}

### Timeline Feasibility
{timeline_feasibility}

### Key Constraints
{key_constraints}

### Risk Levels
- **Technical Risk:** {technical_risk}
- **Budget Risk:** {budget_risk}
- **Team Risk:** {team_risk}
- **Overall Risk Score:** {overall_risk_score}

## Requirements

Please generate a comprehensive, detailed roadmap that:

1. **Addresses all specified preferences and constraints**
2. **Provides specific, actionable milestones with clear deliverables**
3. **Includes time estimates that account for team size and expertise**
4. **Considers all regulatory and compliance requirements**
5. **Incorporates the specified integrations and technical challenges**
6. **Aligns with the budget constraints and deployment preferences**
7. **Provides clear success metrics and KPIs for each milestone**
8. **Identifies potential risks and mitigation strategies**
9. **Suggests specific technologies and tools appropriate for the context**
10. **Includes detailed acceptance criteria for each milestone**

## Output Format

Structure the roadmap with:
- **Executive Summary:** High-level overview and key recommendations
- **Milestones:** Detailed breakdown with timelines, deliverables, and acceptance criteria
- **Technical Architecture:** Recommended tech stack and infrastructure
- **Risk Management:** Identified risks and mitigation strategies
- **Success Metrics:** KPIs and measurement methods for each phase
- **Implementation Notes:** Specific guidance for the team and methodology

Ensure the roadmap is practical, achievable within the specified constraints, and provides clear value progression toward the defined success metrics.
"""

    def _format_roadmap_aspects(self, roadmap_aspects: list) -> str:
        """Format roadmap aspects for display in the template."""
        if not roadmap_aspects or roadmap_aspects == ['technical-only']:
            return "Technical implementation only"

        # Map internal values to display names
        display_map = {
            'business-strategy': 'Business Strategy & Planning',
            'marketing-sales': 'Marketing & Sales',
            'legal-compliance': 'Legal & Compliance',
            'operations': 'Operations & Process Management',
            'customer-support': 'Customer Support & Success',
            'finance-accounting': 'Finance & Accounting',
            'hr-team': 'HR & Team Building',
            'product-management': 'Product Management',
            'qa-testing': 'Quality Assurance & Testing',
            'risk-management': 'Risk Management',
            'technical-only': 'Technical Implementation Only'
        }

        display_values = [display_map.get(aspect, aspect) for aspect in roadmap_aspects]
        return ", ".join(display_values)

    def _format_non_technical_focus_areas(self, roadmap_aspects: list) -> str:
        """Extract and format non-technical focus areas."""
        if not roadmap_aspects or roadmap_aspects == ['technical-only']:
            return "None - Technical implementation focus only"

        non_technical_aspects = [aspect for aspect in roadmap_aspects if aspect != 'technical-only']

        if not non_technical_aspects:
            return "None - Technical implementation focus only"

        # Group aspects by category for better readability
        business_aspects = []
        operational_aspects = []

        business_focused = ['business-strategy', 'marketing-sales', 'finance-accounting', 'product-management']
        operational_focused = ['legal-compliance', 'operations', 'customer-support', 'hr-team', 'qa-testing', 'risk-management']

        for aspect in non_technical_aspects:
            if aspect in business_focused:
                business_aspects.append(aspect)
            elif aspect in operational_focused:
                operational_aspects.append(aspect)

        result_parts = []
        if business_aspects:
            result_parts.append(f"Business: {', '.join(business_aspects)}")
        if operational_aspects:
            result_parts.append(f"Operational: {', '.join(operational_aspects)}")

        return "; ".join(result_parts) if result_parts else "None specified"

    def _generate_roadmap_coverage_description(self, roadmap_aspects: list) -> str:
        """Generate a description of what the roadmap will cover."""
        if not roadmap_aspects or roadmap_aspects == ['technical-only']:
            return "This roadmap focuses exclusively on technical implementation, including architecture, development, testing, and deployment. Business and operational aspects are not included."

        non_technical_count = len([aspect for aspect in roadmap_aspects if aspect != 'technical-only'])

        if non_technical_count == 0:
            return "This roadmap focuses exclusively on technical implementation, including architecture, development, testing, and deployment. Business and operational aspects are not included."

        coverage_parts = ["This roadmap provides comprehensive coverage including technical implementation"]

        # Add descriptions based on selected aspects
        aspect_descriptions = {
            'business-strategy': 'strategic business planning and market analysis',
            'marketing-sales': 'marketing strategy and sales process development',
            'legal-compliance': 'legal framework and compliance requirements',
            'operations': 'operational processes and workflow optimization',
            'customer-support': 'customer service and support systems',
            'finance-accounting': 'financial planning and accounting processes',
            'hr-team': 'team building and human resources management',
            'product-management': 'product strategy and management processes',
            'qa-testing': 'quality assurance and testing frameworks',
            'risk-management': 'risk assessment and mitigation strategies'
        }

        selected_descriptions = []
        for aspect in roadmap_aspects:
            if aspect in aspect_descriptions:
                selected_descriptions.append(aspect_descriptions[aspect])

        if selected_descriptions:
            if len(selected_descriptions) == 1:
                coverage_parts.append(f"as well as {selected_descriptions[0]}")
            elif len(selected_descriptions) == 2:
                coverage_parts.append(f"as well as {selected_descriptions[0]} and {selected_descriptions[1]}")
            else:
                coverage_parts.append(f"as well as {', '.join(selected_descriptions[:-1])}, and {selected_descriptions[-1]}")

        coverage_parts.append("to ensure holistic project success.")

        return " ".join(coverage_parts)