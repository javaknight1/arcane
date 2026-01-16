"""Tests for Story, Epic, and Milestone parsing functionality."""

import pytest
from arcane.items.story import Story
from arcane.items.epic import Epic
from arcane.items.milestone import Milestone
from arcane.items.task import Task


class TestStoryStructuredParsing:
    """Tests for the new structured story parsing format."""

    def test_story_field_extraction_complete(self):
        """Test that all story fields are properly extracted."""
        sample_response = '''
:::STORY_DESCRIPTION:::
This story implements user authentication with secure login and registration. It provides the foundation for all user-related features and enables personalized experiences throughout the application.

:::USER_VALUE:::
As a new user, I want to create an account and securely log in so that I can access personalized features and save my preferences.

:::ACCEPTANCE_CRITERIA:::
- [ ] Criterion 1: Users can register with email and password
- [ ] Criterion 2: Users can log in with valid credentials
- [ ] Criterion 3: Invalid login attempts show appropriate error messages
- [ ] Criterion 4: Session persists across page refreshes

:::TECHNICAL_REQUIREMENTS:::
- JWT-based authentication with refresh tokens
- Password hashing using bcrypt
- Rate limiting on auth endpoints
- Secure cookie handling

:::PREREQUISITES:::
- Story 1.0.0: Database setup must be complete
- Epic 1.0: Core infrastructure needs to be in place

:::BENEFITS:::
- Enables personalized user experience
- Provides security foundation for the application
- Allows user data persistence
- Required for all authenticated features

:::WORK_TYPE:::
implementation

:::COMPLEXITY:::
moderate

:::PRIORITY:::
Critical

:::DURATION_HOURS:::
24

:::TAGS:::
core-scope, backend, authentication, security
'''

        story = Story(name="User Authentication", number="1.0.1")
        story.parse_content(sample_response)

        # Verify Story Description
        assert "user authentication" in story.description.lower()
        assert "secure login" in story.description.lower()

        # Verify User Value
        assert "As a new user" in story.user_value

        # Verify Acceptance Criteria
        assert len(story.acceptance_criteria) >= 4
        assert any("register" in ac.lower() for ac in story.acceptance_criteria)

        # Verify Technical Requirements
        assert "JWT" in story.technical_requirements
        assert "bcrypt" in story.technical_requirements

        # Verify Prerequisites
        assert "1.0.0" in story.prerequisites

        # Verify Benefits
        assert "personalized" in story.benefits.lower()

        # Verify Work Type
        assert story.work_type == "implementation"

        # Verify Complexity
        assert story.complexity == "moderate"

        # Verify Priority
        assert story.priority == "Critical"

        # Verify Duration
        assert story.duration == 24

        # Verify Tags
        assert "core-scope" in story.tags
        assert "backend" in story.tags
        assert "authentication" in story.tags

    def test_story_with_tasks_parsing(self):
        """Test that story with embedded tasks parses correctly."""
        # Create a story with a task child first
        story = Story(name="User Registration", number="1.0.1")
        task = Task(name="Create registration form", number="1.0.1.1", parent=story)

        sample_response = '''
:::STORY_DESCRIPTION:::
Implement user registration functionality.

:::USER_VALUE:::
As a visitor, I want to register so that I can become a user.

:::ACCEPTANCE_CRITERIA:::
- [ ] Users can fill out registration form
- [ ] Form validation works correctly

:::TECHNICAL_REQUIREMENTS:::
- React form components
- API endpoint integration

:::PREREQUISITES:::
None

:::BENEFITS:::
- Enables new user onboarding
- Required for authentication flow

:::WORK_TYPE:::
implementation

:::COMPLEXITY:::
simple

:::PRIORITY:::
High

:::DURATION_HOURS:::
8

:::TAGS:::
core-scope, frontend

###TASK_START### 1.0.1.1
:::TASK_TITLE:::
Create registration form component

:::TASK_GOAL:::
Build a React component for user registration with proper form validation and error handling.

:::TASK_BENEFITS:::
- Provides user-friendly registration experience
- Enables form validation

:::TASK_TECHNICAL_REQUIREMENTS:::
- React Hook Form for form state
- Zod for validation

:::TASK_PREREQUISITES:::
None

:::TASK_CLAUDE_CODE_PROMPT:::
Create a registration form component at src/components/RegistrationForm.tsx with email, password, and confirm password fields.

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
simple

:::TASK_DURATION_HOURS:::
4

:::TASK_PRIORITY:::
High

:::TASK_TAGS:::
frontend, authentication
###TASK_END###
'''

        story.parse_content(sample_response)

        # Verify story fields
        assert "registration" in story.description.lower()
        assert story.work_type == "implementation"
        assert story.complexity == "simple"
        assert story.duration == 8

        # Verify task was updated
        assert task.description == "Build a React component for user registration with proper form validation and error handling."
        assert task.work_type == "implementation"
        assert task.complexity == "simple"
        assert task.duration == 4
        assert "RegistrationForm.tsx" in task.claude_code_prompt

    def test_acceptance_criteria_parsing(self):
        """Test that acceptance criteria are parsed into a proper list."""
        story = Story(name="Test Story", number="1.0.1")

        # Test with checkbox format
        story.acceptance_criteria = []
        raw_criteria = """
- [ ] Criterion 1: Users can log in
- [ ] Criterion 2: Error messages display
- [x] Criterion 3: Session persists
- Users can log out
"""
        criteria = story._parse_criteria_list(raw_criteria)
        assert len(criteria) == 4
        assert "Users can log in" in criteria[0]


class TestEpicStructuredParsing:
    """Tests for the new structured epic parsing format."""

    def test_epic_field_extraction_complete(self):
        """Test that all epic fields are properly extracted."""
        sample_response = '''
:::EPIC_DESCRIPTION:::
This epic covers the core authentication and user management functionality. It establishes the foundation for user identity, permissions, and secure access to the application. This is critical for all user-facing features.

:::EPIC_GOALS:::
- Goal 1: Implement secure user authentication
- Goal 2: Build comprehensive user profile management
- Goal 3: Establish role-based access control
- Goal 4: Create password recovery flow

:::BENEFITS:::
- Enables secure application access
- Provides foundation for user personalization
- Supports compliance requirements
- Reduces security risks

:::TECHNICAL_REQUIREMENTS:::
- OAuth 2.0 integration
- PostgreSQL for user data
- Redis for session management
- HTTPS enforcement

:::PREREQUISITES:::
- Milestone 1: Infrastructure setup complete
- Database schema defined

:::SUCCESS_METRICS:::
- Metric 1: 100% of users can authenticate within 2 seconds
- Metric 2: Zero security vulnerabilities in auth flow
- Metric 3: Password recovery completes in under 5 minutes

:::RISKS_AND_MITIGATIONS:::
- Risk 1: OAuth provider downtime → Mitigation: Implement fallback local auth
- Risk 2: Data breach concerns → Mitigation: Encrypt all PII at rest

:::WORK_TYPE:::
implementation

:::COMPLEXITY:::
complex

:::PRIORITY:::
Critical

:::DURATION_HOURS:::
120

:::TAGS:::
core-scope, backend, authentication, security
'''

        epic = Epic(name="User Authentication & Management", number="1.0")
        epic.parse_content(sample_response)

        # Verify Description
        assert "authentication" in epic.description.lower()
        assert "user management" in epic.description.lower()

        # Verify Goals
        assert len(epic.goals) >= 4
        assert any("secure" in g.lower() for g in epic.goals)

        # Verify Benefits
        assert "secure" in epic.benefits.lower()

        # Verify Technical Requirements
        assert "OAuth" in epic.technical_requirements
        assert "PostgreSQL" in epic.technical_requirements

        # Verify Prerequisites
        assert "Milestone 1" in epic.prerequisites

        # Verify Success Metrics
        assert len(epic.success_metrics) >= 3

        # Verify Risks
        assert "OAuth" in epic.risks_and_mitigations

        # Verify select fields
        assert epic.work_type == "implementation"
        assert epic.complexity == "complex"
        assert epic.priority == "Critical"
        assert epic.duration == 120

        # Verify Tags
        assert "core-scope" in epic.tags
        assert "authentication" in epic.tags


class TestMilestoneStructuredParsing:
    """Tests for the new structured milestone parsing format."""

    def test_milestone_field_extraction_complete(self):
        """Test that all milestone fields are properly extracted."""
        sample_response = '''
:::MILESTONE_DESCRIPTION:::
This milestone establishes the foundational infrastructure and core features of the application. It includes setting up the development environment, implementing the authentication system, and creating the basic user interface. This phase is critical as all subsequent development depends on these foundations.

:::MILESTONE_GOAL:::
Deliver a working prototype with user authentication and basic UI that can be demonstrated to stakeholders.

:::KEY_DELIVERABLES:::
- Deliverable 1: Complete development environment setup
- Deliverable 2: Working user authentication system
- Deliverable 3: Basic responsive UI framework
- Deliverable 4: CI/CD pipeline configuration
- Deliverable 5: Initial database schema

:::BENEFITS:::
- Establishes technical foundation for all future work
- Enables early stakeholder feedback
- Reduces technical risk through early validation
- Creates development standards and patterns

:::PREREQUISITES:::
None - This is the first milestone

:::SUCCESS_CRITERIA:::
- Criterion 1: All team members can run application locally
- Criterion 2: Users can register and log in successfully
- Criterion 3: CI/CD pipeline deploys to staging automatically
- Criterion 4: Page load time under 3 seconds

:::RISKS_IF_DELAYED:::
- Risk 1: All subsequent milestones will be delayed
- Risk 2: Technical debt may accumulate from workarounds

:::TECHNICAL_REQUIREMENTS:::
- Node.js 18+ runtime
- PostgreSQL database
- Docker containers
- GitHub Actions

:::WORK_TYPE:::
implementation

:::COMPLEXITY:::
complex

:::PRIORITY:::
Critical

:::DURATION_HOURS:::
320

:::TAGS:::
phase-1, mvp, infrastructure, core-scope
'''

        milestone = Milestone(name="Foundation & Core Setup", number="1")
        milestone.parse_content(sample_response)

        # Verify Description
        assert "foundational" in milestone.description.lower()
        assert "infrastructure" in milestone.description.lower()

        # Verify Goal
        assert "prototype" in milestone.goal.lower()

        # Verify Key Deliverables
        assert len(milestone.key_deliverables) >= 5
        assert any("development environment" in d.lower() for d in milestone.key_deliverables)

        # Verify Benefits
        assert "foundation" in milestone.benefits.lower()

        # Verify Prerequisites
        assert "first milestone" in milestone.prerequisites.lower()

        # Verify Success Criteria
        assert len(milestone.success_criteria) >= 4

        # Verify Risks
        assert "delayed" in milestone.risks_if_delayed.lower()

        # Verify Technical Requirements
        assert "Node.js" in milestone.technical_requirements
        assert "PostgreSQL" in milestone.technical_requirements

        # Verify select fields
        assert milestone.work_type == "implementation"
        assert milestone.complexity == "complex"
        assert milestone.priority == "Critical"
        assert milestone.duration == 320

        # Verify Tags
        assert "phase-1" in milestone.tags
        assert "mvp" in milestone.tags


class TestLegacyParsing:
    """Tests for backward compatibility with legacy format."""

    def test_story_legacy_format(self):
        """Test that legacy story format is still parsed."""
        legacy_response = (
            "##### Story 1.0.1: User Login\n\n"
            "**Duration:** 16 hours\n"
            "**Priority:** High\n"
            "**What it is:** Implement login functionality\n\n"
            "**Benefits:**\n"
            "- Secure access\n"
            "- User tracking\n\n"
            "**Work Type:** implementation\n"
            "**Complexity:** moderate\n"
            "**Tags:** backend, auth\n"
        )

        story = Story(name="User Login", number="1.0.1")
        story.parse_content(legacy_response)

        assert story.duration == 16
        assert story.priority == "High"
        assert "login" in story.description.lower()
        assert "Secure access" in story.benefits
        assert story.work_type == "implementation"
        assert "backend" in story.tags

    def test_epic_legacy_format(self):
        """Test that legacy epic format is still parsed."""
        legacy_response = (
            "### Epic 1.0: Auth System\n\n"
            "**Duration:** 80 hours\n"
            "**Priority:** Critical\n\n"
            "#### **What it is and why we need it:**\n"
            "Complete authentication system for the application.\n\n"
            "#### **Benefits:**\n"
            "- Security\n"
            "- User management\n"
        )

        epic = Epic(name="Auth System", number="1.0")
        epic.parse_content(legacy_response)

        assert epic.duration == 80
        assert epic.priority == "Critical"
        assert "authentication" in epic.description.lower()

    def test_milestone_legacy_format(self):
        """Test that legacy milestone format is still parsed."""
        legacy_response = (
            "## Milestone 1: Foundation\n\n"
            "**Duration:** 200 hours\n"
            "**Priority:** Critical\n"
            "**Goal:** Build foundation\n\n"
            "### **What it is and why we need it:**\n"
            "Sets up the initial infrastructure.\n\n"
            "### **Benefits:**\n"
            "- Ready for development\n"
            "- Team onboarding\n"
        )

        milestone = Milestone(name="Foundation", number="1")
        milestone.parse_content(legacy_response)

        assert milestone.duration == 200
        assert milestone.priority == "Critical"
        assert milestone.goal == "Build foundation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
