"""ID generation utilities for Arcane.

All IDs in the project are generated using this module to ensure
consistent, unique, sortable identifiers.
"""

from ulid import ULID


def generate_id(prefix: str) -> str:
    """Generate a unique ID with the given prefix.

    Uses ULID (Universally Unique Lexicographically Sortable Identifier)
    to ensure IDs are unique and sortable by creation time.

    Args:
        prefix: The type prefix for the ID (e.g., "task", "story", "epic")

    Returns:
        A string in the format "{prefix}-{ulid}", e.g., "task-01HQ3K9V..."

    Example:
        >>> generate_id("task")
        'task-01HQ3K9V7YJZQX8E3Y4N6MWKPR'
    """
    return f"{prefix}-{ULID()}"
