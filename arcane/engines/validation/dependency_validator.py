"""Dependency validation for roadmap items."""

from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
from arcane.items.milestone import Milestone
from arcane.items.base import Item
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class IssueSeverity(Enum):
    """Severity level for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class DependencyIssue:
    """A dependency-related issue."""
    severity: IssueSeverity
    item_id: str
    issue_type: str
    message: str
    suggested_fix: Optional[str] = None
    related_items: List[str] = field(default_factory=list)


class DependencyValidator:
    """Validates roadmap dependencies and suggests missing items."""

    # Required components for common project types
    REQUIRED_FOUNDATIONS = {
        'authentication': ['database', 'user_model'],
        'api': ['authentication', 'database'],
        'payments': ['authentication', 'user_management', 'api'],
        'notifications': ['user_management', 'authentication'],
        'analytics': ['database', 'logging'],
        'admin_dashboard': ['authentication', 'authorization', 'database'],
        'file_upload': ['storage', 'authentication'],
        'search': ['database', 'indexing'],
    }

    # Common items often forgotten
    COMMONLY_FORGOTTEN = {
        'security': ['security_audit', 'penetration_testing', 'input_validation', 'rate_limiting'],
        'monitoring': ['logging', 'error_tracking', 'performance_monitoring', 'alerting'],
        'documentation': ['api_documentation', 'user_guide', 'developer_docs', 'deployment_guide'],
        'testing': ['unit_tests', 'integration_tests', 'e2e_tests', 'load_testing'],
        'devops': ['ci_cd_pipeline', 'infrastructure_as_code', 'backup_strategy', 'disaster_recovery'],
        'compliance': ['data_privacy', 'gdpr', 'accessibility', 'terms_of_service'],
    }

    # Keywords that indicate features
    FEATURE_KEYWORDS = {
        'authentication': ['login', 'auth', 'signin', 'signup', 'password', 'oauth', 'sso', 'jwt'],
        'database': ['database', 'db', 'schema', 'migration', 'postgresql', 'mysql', 'mongodb'],
        'api': ['api', 'endpoint', 'rest', 'graphql', 'websocket'],
        'payments': ['payment', 'stripe', 'billing', 'subscription', 'checkout', 'invoice'],
        'user_management': ['user', 'profile', 'account', 'registration', 'onboarding'],
        'notifications': ['notification', 'email', 'sms', 'push', 'alert'],
        'file_upload': ['upload', 'file', 'image', 'attachment', 's3', 'storage'],
        'search': ['search', 'filter', 'elasticsearch', 'algolia'],
        'logging': ['logging', 'log', 'monitor', 'trace'],
        'storage': ['storage', 's3', 'blob', 'cdn'],
        'indexing': ['index', 'search index', 'elasticsearch'],
        'authorization': ['authorization', 'permission', 'role', 'access control', 'rbac'],
        'user_model': ['user model', 'user schema', 'user table', 'user entity'],
    }

    def __init__(self):
        self.issues: List[DependencyIssue] = []
        self.item_lookup: Dict[str, Item] = {}
        self.detected_features: Set[str] = set()

    def validate(self, milestones: List[Milestone]) -> List[DependencyIssue]:
        """Run all dependency validations.

        Args:
            milestones: List of milestone objects to validate

        Returns:
            List of dependency issues found
        """
        self.issues = []
        self._build_item_lookup(milestones)
        self._detect_features(milestones)

        # Run validations
        self._validate_required_foundations()
        self._validate_dependency_references()
        self._validate_dependency_ordering()
        self._check_commonly_forgotten()
        self._validate_no_circular_dependencies()

        return self.issues

    def _build_item_lookup(self, milestones: List[Milestone]) -> None:
        """Build lookup dictionary of all items."""
        self.item_lookup = {}

        for milestone in milestones:
            self.item_lookup[milestone.id] = milestone

            for epic in milestone.get_children_by_type('Epic'):
                self.item_lookup[epic.id] = epic

                for story in epic.get_children_by_type('Story'):
                    self.item_lookup[story.id] = story

                    for task in story.get_children_by_type('Task'):
                        self.item_lookup[task.id] = task

    def _detect_features(self, milestones: List[Milestone]) -> None:
        """Detect what features are in the roadmap."""
        self.detected_features = set()

        # Collect all text for keyword matching
        all_text = ""
        for item_id, item in self.item_lookup.items():
            all_text += f" {item.name.lower()} "
            if item.description:
                all_text += f" {item.description.lower()} "

        # Match keywords to features
        for feature, keywords in self.FEATURE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in all_text:
                    self.detected_features.add(feature)
                    break

    def _validate_required_foundations(self) -> None:
        """Check that required foundational items exist."""
        for feature in self.detected_features:
            if feature in self.REQUIRED_FOUNDATIONS:
                required = self.REQUIRED_FOUNDATIONS[feature]

                for req in required:
                    if req not in self.detected_features:
                        self.issues.append(DependencyIssue(
                            severity=IssueSeverity.ERROR,
                            item_id="roadmap",
                            issue_type="missing_foundation",
                            message=f"Feature '{feature}' requires '{req}' but it's not in the roadmap",
                            suggested_fix=f"Add {req} epic/story before implementing {feature}",
                            related_items=[feature]
                        ))

    def _validate_dependency_references(self) -> None:
        """Check that all dependency references point to existing items."""
        for item_id, item in self.item_lookup.items():
            # Check depends_on_items list (linked Item objects)
            depends_on = getattr(item, 'depends_on_items', [])
            for dep_item in depends_on:
                dep_id = dep_item.id if hasattr(dep_item, 'id') else str(dep_item)
                if dep_id not in self.item_lookup:
                    self.issues.append(DependencyIssue(
                        severity=IssueSeverity.ERROR,
                        item_id=item_id,
                        issue_type="invalid_dependency",
                        message=f"References non-existent dependency: {dep_id}",
                        suggested_fix="Remove or correct the dependency reference",
                        related_items=[dep_id]
                    ))

            # Also check dependency_ids if present (string IDs)
            dep_ids = getattr(item, 'dependency_ids', [])
            for dep_id in dep_ids:
                if dep_id not in self.item_lookup:
                    self.issues.append(DependencyIssue(
                        severity=IssueSeverity.ERROR,
                        item_id=item_id,
                        issue_type="invalid_dependency",
                        message=f"References non-existent dependency: {dep_id}",
                        suggested_fix="Remove or correct the dependency reference",
                        related_items=[dep_id]
                    ))

    def _validate_dependency_ordering(self) -> None:
        """Check that dependencies come before dependents in the roadmap."""
        # Get item order from roadmap structure
        item_order = list(self.item_lookup.keys())
        item_positions = {id: pos for pos, id in enumerate(item_order)}

        for item_id, item in self.item_lookup.items():
            item_pos = item_positions.get(item_id, 0)

            # Check depends_on_items
            depends_on = getattr(item, 'depends_on_items', [])
            for dep_item in depends_on:
                dep_id = dep_item.id if hasattr(dep_item, 'id') else str(dep_item)
                dep_pos = item_positions.get(dep_id, -1)

                if dep_pos > item_pos:
                    self.issues.append(DependencyIssue(
                        severity=IssueSeverity.WARNING,
                        item_id=item_id,
                        issue_type="incorrect_ordering",
                        message=f"Depends on {dep_id} which appears later in the roadmap",
                        suggested_fix=f"Reorder items so {dep_id} comes before {item_id}",
                        related_items=[dep_id]
                    ))

            # Also check dependency_ids
            dep_ids = getattr(item, 'dependency_ids', [])
            for dep_id in dep_ids:
                dep_pos = item_positions.get(dep_id, -1)

                if dep_pos > item_pos:
                    self.issues.append(DependencyIssue(
                        severity=IssueSeverity.WARNING,
                        item_id=item_id,
                        issue_type="incorrect_ordering",
                        message=f"Depends on {dep_id} which appears later in the roadmap",
                        suggested_fix=f"Reorder items so {dep_id} comes before {item_id}",
                        related_items=[dep_id]
                    ))

    def _check_commonly_forgotten(self) -> None:
        """Check for commonly forgotten items."""
        all_text = " ".join([
            f"{item.name.lower()} {(item.description or '').lower()}"
            for item in self.item_lookup.values()
        ])

        for category, items in self.COMMONLY_FORGOTTEN.items():
            has_any = any(
                item.replace('_', ' ') in all_text or item.replace('_', '') in all_text
                for item in items
            )

            if not has_any:
                self.issues.append(DependencyIssue(
                    severity=IssueSeverity.INFO,
                    item_id="roadmap",
                    issue_type="missing_category",
                    message=f"No {category} items found in roadmap",
                    suggested_fix=f"Consider adding: {', '.join(items[:3])}",
                    related_items=items
                ))

    def _validate_no_circular_dependencies(self) -> None:
        """Check for circular dependency chains."""

        def get_dependency_ids(item: Item) -> List[str]:
            """Get all dependency IDs for an item."""
            ids = []
            # From depends_on_items
            depends_on = getattr(item, 'depends_on_items', [])
            for dep_item in depends_on:
                if hasattr(dep_item, 'id'):
                    ids.append(dep_item.id)
            # From dependency_ids
            dep_ids = getattr(item, 'dependency_ids', [])
            ids.extend(dep_ids)
            return ids

        def has_cycle(item_id: str, visited: Set[str], path: Set[str]) -> Optional[List[str]]:
            if item_id in path:
                return [item_id]  # Start of cycle
            if item_id in visited:
                return None

            visited.add(item_id)
            path.add(item_id)

            item = self.item_lookup.get(item_id)
            if item:
                dep_ids = get_dependency_ids(item)
                for dep_id in dep_ids:
                    cycle = has_cycle(dep_id, visited, path)
                    if cycle is not None:
                        cycle.append(item_id)
                        return cycle

            path.remove(item_id)
            return None

        checked = set()
        for item_id in self.item_lookup:
            if item_id in checked:
                continue
            cycle = has_cycle(item_id, set(), set())
            if cycle:
                cycle_str = " → ".join(reversed(cycle))
                self.issues.append(DependencyIssue(
                    severity=IssueSeverity.ERROR,
                    item_id=item_id,
                    issue_type="circular_dependency",
                    message=f"Circular dependency detected: {cycle_str}",
                    suggested_fix="Remove one of the dependencies in the cycle",
                    related_items=cycle
                ))
                # Mark all items in cycle as checked
                checked.update(cycle)

    def get_summary(self) -> Dict[str, int]:
        """Get summary of validation results."""
        return {
            'total_issues': len(self.issues),
            'errors': len([i for i in self.issues if i.severity == IssueSeverity.ERROR]),
            'warnings': len([i for i in self.issues if i.severity == IssueSeverity.WARNING]),
            'info': len([i for i in self.issues if i.severity == IssueSeverity.INFO]),
            'detected_features': len(self.detected_features),
            'total_items': len(self.item_lookup)
        }

    def format_report(self) -> str:
        """Format validation results as a report."""
        lines = ["Dependency Validation Report", "=" * 40]

        summary = self.get_summary()
        lines.append(f"\nItems validated: {summary['total_items']}")
        lines.append(f"Features detected: {', '.join(sorted(self.detected_features))}")
        lines.append(f"\nTotal issues: {summary['total_issues']}")
        lines.append(f"  Errors: {summary['errors']}")
        lines.append(f"  Warnings: {summary['warnings']}")
        lines.append(f"  Info: {summary['info']}")

        if self.issues:
            lines.append("\n" + "-" * 40)

            for severity in [IssueSeverity.ERROR, IssueSeverity.WARNING, IssueSeverity.INFO]:
                severity_issues = [i for i in self.issues if i.severity == severity]
                if severity_issues:
                    icon = {"error": "ERROR", "warning": "WARNING", "info": "INFO"}[severity.value]
                    lines.append(f"\n{icon}S:")

                    for issue in severity_issues:
                        lines.append(f"  [{issue.item_id}] {issue.issue_type}")
                        lines.append(f"    {issue.message}")
                        if issue.suggested_fix:
                            lines.append(f"    -> Fix: {issue.suggested_fix}")
        else:
            lines.append("\nNo issues found!")

        return "\n".join(lines)
