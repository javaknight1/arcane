"""Storage management for Arcane roadmaps.

Provides persistence for roadmaps and project contexts,
with support for resuming incomplete generations.
"""

from .manager import StorageManager

__all__ = ["StorageManager"]
