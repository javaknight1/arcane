"""Preference validation and consistency checking system."""

from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue with preferences."""
    severity: ValidationSeverity
    message: str
    affected_preferences: List[str]
    recommendation: Optional[str] = None
    auto_fix_available: bool = False


class PreferenceValidator:
    """Validates preference combinations for consistency and feasibility."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_preferences(self, preferences: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Validate all preferences for consistency and feasibility.

        Args:
            preferences: Dictionary of all collected preferences

        Returns:
            List of validation issues found
        """
        issues = []

        # Run all validation checks
        issues.extend(self._validate_budget_alignment(preferences))
        issues.extend(self._validate_timeline_feasibility(preferences))
        issues.extend(self._validate_team_capacity(preferences))
        issues.extend(self._validate_technical_complexity(preferences))
        issues.extend(self._validate_regulatory_compliance(preferences))
        issues.extend(self._validate_integration_consistency(preferences))
        issues.extend(self._validate_scaling_alignment(preferences))
        issues.extend(self._validate_success_metrics(preferences))

        # Sort by severity (critical first)
        severity_order = {
            ValidationSeverity.CRITICAL: 0,
            ValidationSeverity.ERROR: 1,
            ValidationSeverity.WARNING: 2,
            ValidationSeverity.INFO: 3
        }
        issues.sort(key=lambda x: severity_order[x.severity])

        self.logger.info(f"Validation completed: {len(issues)} issues found")
        return issues

    def _validate_budget_alignment(self, preferences: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate budget vs complexity and feature alignment."""
        issues = []

        budget_range = preferences.get('budget_range')
        complexity = preferences.get('complexity')
        team_size = preferences.get('team_size')
        timeline = preferences.get('timeline')
        technical_challenges = preferences.get('technical_challenges', [])

        # Budget vs Complexity conflicts
        if budget_range == 'bootstrap' and complexity == 'complex':
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Bootstrap budget may not support complex technical implementation",
                affected_preferences=['budget_range', 'complexity'],
                recommendation="Consider reducing complexity or securing additional funding"
            ))

        # Budget vs Team Size conflicts
        if budget_range in ['bootstrap', 'seed'] and team_size == '8+':
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Large team size incompatible with limited budget",
                affected_preferences=['budget_range', 'team_size'],
                recommendation="Reduce team size or increase budget allocation"
            ))

        # Budget vs Technical Challenges
        expensive_challenges = ['ml-ai', 'blockchain', 'high-concurrency', 'microservices']
        if budget_range == 'bootstrap' and any(challenge in expensive_challenges for challenge in technical_challenges):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Technical challenges may require more budget than available",
                affected_preferences=['budget_range', 'technical_challenges'],
                recommendation="Consider simpler alternatives or additional funding"
            ))

        # Infrastructure budget alignment
        infra_budget = preferences.get('infra_budget')
        deployment_env = preferences.get('deployment_environment')

        if infra_budget == 'minimal' and deployment_env in ['kubernetes', 'hybrid']:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Complex deployment environments require substantial infrastructure budget",
                affected_preferences=['infra_budget', 'deployment_environment'],
                recommendation="Increase infrastructure budget or choose simpler deployment"
            ))

        return issues

    def _validate_timeline_feasibility(self, preferences: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate timeline vs scope and complexity."""
        issues = []

        timeline = preferences.get('timeline')
        complexity = preferences.get('complexity')
        team_size = preferences.get('team_size')
        focus = preferences.get('focus')
        technical_challenges = preferences.get('technical_challenges', [])
        regulatory = preferences.get('regulatory', [])

        # Timeline vs Complexity
        if timeline == '3-months' and complexity == 'complex':
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="3-month timeline insufficient for complex technical implementation",
                affected_preferences=['timeline', 'complexity'],
                recommendation="Extend timeline to 6+ months or reduce complexity"
            ))

        # Timeline vs Team Size (small team, big scope)
        if timeline == '3-months' and team_size == '1' and focus != 'mvp':
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Solo developer with short timeline should focus on MVP",
                affected_preferences=['timeline', 'team_size', 'focus'],
                recommendation="Consider MVP focus or extend timeline"
            ))

        # Timeline vs Regulatory Requirements
        compliance_heavy = ['hipaa', 'pci-dss', 'soc2', 'iso27001', 'fedramp']
        if timeline == '3-months' and any(reg in compliance_heavy for reg in regulatory):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Compliance requirements typically require 6+ months implementation",
                affected_preferences=['timeline', 'regulatory'],
                recommendation="Extend timeline or phase compliance implementation"
            ))

        # Timeline vs Technical Challenges
        time_intensive_challenges = ['ml-ai', 'blockchain', 'data-migrations', 'microservices']
        if timeline == '3-months' and len([c for c in technical_challenges if c in time_intensive_challenges]) > 1:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Multiple complex technical challenges require more development time",
                affected_preferences=['timeline', 'technical_challenges'],
                recommendation="Prioritize challenges or extend timeline"
            ))

        return issues

    def _validate_team_capacity(self, preferences: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate team size vs scope and expertise requirements."""
        issues = []

        team_size = preferences.get('team_size')
        complexity = preferences.get('complexity')
        team_expertise = preferences.get('team_expertise')
        technical_challenges = preferences.get('technical_challenges', [])
        focus = preferences.get('focus')

        # Team expertise vs complexity
        if team_expertise == 'learning' and complexity == 'complex':
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Learning team may struggle with complex technical requirements",
                affected_preferences=['team_expertise', 'complexity'],
                recommendation="Consider mentorship, training, or reduced complexity"
            ))

        # Solo developer limitations
        if team_size == '1':
            specialized_challenges = ['ml-ai', 'blockchain', 'microservices', 'high-concurrency']
            solo_challenges = [c for c in technical_challenges if c in specialized_challenges]

            if len(solo_challenges) > 1:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Solo developer handling multiple specialized technical areas",
                    affected_preferences=['team_size', 'technical_challenges'],
                    recommendation="Consider team expansion or focusing on single specialty"
                ))

        # Large team coordination
        if team_size == '8+':
            team_distribution = preferences.get('team_distribution')
            dev_methodology = preferences.get('dev_methodology')

            if team_distribution == 'remote-async' and dev_methodology == 'adhoc':
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Large async teams require structured development methodology",
                    affected_preferences=['team_size', 'team_distribution', 'dev_methodology'],
                    recommendation="Implement agile or kanban methodology for large distributed teams"
                ))

        return issues

    def _validate_technical_complexity(self, preferences: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate technical challenge combinations."""
        issues = []

        technical_challenges = preferences.get('technical_challenges', [])
        complexity = preferences.get('complexity')
        team_expertise = preferences.get('team_expertise')

        # Conflicting technical approaches
        if 'microservices' in technical_challenges and 'simple' == complexity:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Microservices architecture conflicts with simple complexity level",
                affected_preferences=['technical_challenges', 'complexity'],
                recommendation="Use monolithic architecture for simple projects"
            ))

        # Technology stack conflicts
        if 'offline-first' in technical_challenges and 'realtime-data' in technical_challenges:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Offline-first and real-time data patterns require careful sync design",
                affected_preferences=['technical_challenges'],
                recommendation="Plan robust data synchronization strategy"
            ))

        # Expertise requirements
        advanced_challenges = ['ml-ai', 'blockchain', 'microservices', 'high-concurrency']
        if team_expertise in ['learning', 'intermediate'] and len([c for c in technical_challenges if c in advanced_challenges]) > 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Advanced technical challenges may exceed current team expertise",
                affected_preferences=['technical_challenges', 'team_expertise'],
                recommendation="Plan for learning time or expert consultation"
            ))

        return issues

    def _validate_regulatory_compliance(self, preferences: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate regulatory requirements consistency."""
        issues = []

        regulatory = preferences.get('regulatory', [])
        industry = preferences.get('industry')
        target_market = preferences.get('target_market')
        deployment_environment = preferences.get('deployment_environment')

        # Industry-specific compliance requirements
        required_compliance = {
            'healthcare': ['hipaa'],
            'finance': ['pci-dss'],
            'education': ['ferpa'],
            'government': ['fedramp']
        }

        if industry in required_compliance:
            required = required_compliance[industry]
            missing = [req for req in required if req not in regulatory]

            if missing:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"{industry.title()} industry requires {', '.join(missing).upper()} compliance",
                    affected_preferences=['industry', 'regulatory'],
                    recommendation=f"Add {', '.join(missing).upper()} to regulatory requirements"
                ))

        # Global market GDPR requirement
        if target_market in ['global', 'multi-region'] and 'gdpr' not in regulatory:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Global market typically requires GDPR compliance",
                affected_preferences=['target_market', 'regulatory'],
                recommendation="Consider adding GDPR compliance for global markets"
            ))

        # On-premise deployment with cloud compliance
        cloud_compliance = ['fedramp', 'soc2']
        if deployment_environment == 'on-premise' and any(comp in cloud_compliance for comp in regulatory):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Cloud compliance standards with on-premise deployment",
                affected_preferences=['deployment_environment', 'regulatory'],
                recommendation="Verify compliance requirements for on-premise deployment"
            ))

        return issues

    def _validate_integration_consistency(self, preferences: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate integration requirements consistency."""
        issues = []

        payment_integrations = preferences.get('payment_integrations', [])
        business_integrations = preferences.get('business_integrations', [])
        industry = preferences.get('industry')
        regulatory = preferences.get('regulatory', [])

        # Payment integrations with compliance
        if 'stripe' in payment_integrations or 'paypal' in payment_integrations:
            if 'pci-dss' not in regulatory:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Payment processing typically requires PCI-DSS compliance",
                    affected_preferences=['payment_integrations', 'regulatory'],
                    recommendation="Consider adding PCI-DSS compliance for payment processing"
                ))

        # Industry-specific integration expectations
        if industry == 'ecommerce':
            expected_integrations = ['accounting', 'analytics']
            missing = [integration for integration in expected_integrations if integration not in business_integrations]

            if missing:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message=f"E-commerce typically benefits from {', '.join(missing)} integrations",
                    affected_preferences=['industry', 'business_integrations'],
                    recommendation=f"Consider adding {', '.join(missing)} integrations"
                ))

        return issues

    def _validate_scaling_alignment(self, preferences: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate scaling expectations with architecture choices."""
        issues = []

        scaling_expectations = preferences.get('scaling_expectations')
        deployment_environment = preferences.get('deployment_environment')
        infra_budget = preferences.get('infra_budget')
        technical_challenges = preferences.get('technical_challenges', [])

        # Viral scaling requirements
        if scaling_expectations == 'viral':
            if deployment_environment not in ['cloud', 'serverless', 'kubernetes']:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message="Viral scaling requires cloud-native deployment environment",
                    affected_preferences=['scaling_expectations', 'deployment_environment'],
                    recommendation="Choose cloud, serverless, or Kubernetes deployment"
                ))

            if infra_budget == 'minimal':
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="Viral scaling typically requires substantial infrastructure budget",
                    affected_preferences=['scaling_expectations', 'infra_budget'],
                    recommendation="Plan for scaling infrastructure costs"
                ))

            if 'high-concurrency' not in technical_challenges:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message="Viral scaling should consider high-concurrency challenges",
                    affected_preferences=['scaling_expectations', 'technical_challenges'],
                    recommendation="Add high-concurrency to technical challenges"
                ))

        return issues

    def _validate_success_metrics(self, preferences: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate success metrics alignment with project type."""
        issues = []

        success_metric = preferences.get('success_metric')
        focus = preferences.get('focus')
        industry = preferences.get('industry')
        budget_range = preferences.get('budget_range')

        # MVP focus should prioritize adoption/validation
        if focus == 'mvp' and success_metric in ['revenue', 'cost-saving']:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="MVP projects typically focus on adoption/validation before revenue",
                affected_preferences=['focus', 'success_metric'],
                recommendation="Consider adoption or satisfaction metrics for MVP"
            ))

        # Bootstrap budget with revenue focus
        if budget_range == 'bootstrap' and success_metric == 'cost-saving':
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Bootstrap projects typically focus on growth rather than cost-saving",
                affected_preferences=['budget_range', 'success_metric'],
                recommendation="Consider adoption or revenue metrics for bootstrap projects"
            ))

        # Industry-specific metric expectations
        metric_expectations = {
            'healthcare': ['satisfaction', 'performance'],
            'finance': ['performance', 'revenue'],
            'education': ['satisfaction', 'adoption'],
            'government': ['performance', 'cost-saving']
        }

        if industry in metric_expectations:
            expected = metric_expectations[industry]
            if success_metric not in expected:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    message=f"{industry.title()} projects often focus on {' or '.join(expected)} metrics",
                    affected_preferences=['industry', 'success_metric'],
                    recommendation=f"Consider {' or '.join(expected)} metrics for {industry} projects"
                ))

        return issues

    def get_validation_summary(self, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Generate a summary of validation results."""
        summary = {
            'total_issues': len(issues),
            'by_severity': {
                'critical': len([i for i in issues if i.severity == ValidationSeverity.CRITICAL]),
                'error': len([i for i in issues if i.severity == ValidationSeverity.ERROR]),
                'warning': len([i for i in issues if i.severity == ValidationSeverity.WARNING]),
                'info': len([i for i in issues if i.severity == ValidationSeverity.INFO])
            },
            'blocking_issues': len([i for i in issues if i.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]]),
            'recommendations_available': len([i for i in issues if i.recommendation]),
            'auto_fixes_available': len([i for i in issues if i.auto_fix_available])
        }

        return summary

    def should_proceed(self, issues: List[ValidationIssue]) -> Tuple[bool, str]:
        """
        Determine if roadmap generation should proceed based on validation issues.

        Returns:
            Tuple of (should_proceed, reason)
        """
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        error_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR]

        if critical_issues:
            return False, f"Critical validation issues must be resolved: {len(critical_issues)} found"

        if len(error_issues) > 3:
            return False, f"Too many error-level issues: {len(error_issues)} found, maximum 3 allowed"

        if error_issues:
            return True, f"Proceeding with {len(error_issues)} error-level warnings"

        return True, "All validations passed"