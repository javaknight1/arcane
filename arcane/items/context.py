"""ProjectContext model - built from discovery question answers.

The ProjectContext captures all information gathered during the
question/answer phase and is injected into every AI generation call.
"""

from pydantic import BaseModel


class ProjectContext(BaseModel):
    """Project context built from question answers.

    Field names MUST match the Question.key values exactly so the
    conductor can build this directly from the answers dict.
    """

    # Basic information
    project_name: str
    vision: str
    problem_statement: str
    target_users: list[str]

    # Constraints
    timeline: str
    team_size: int
    developer_experience: str
    budget_constraints: str

    # Technical
    tech_stack: list[str] = []
    infrastructure_preferences: str = "No preference"
    existing_codebase: bool = False

    # Requirements
    must_have_features: list[str]
    nice_to_have_features: list[str] = []
    out_of_scope: list[str] = []
    similar_products: list[str] = []
    notes: str = ""
