"""Arcane - AI-Powered Roadmap Generation CLI.

A comprehensive command-line tool that transforms ideas into actionable roadmaps
and integrates with project management tools. Built with a clean, modular
architecture for maximum flexibility and extensibility.
"""

# Core engines
from .engines.generation import RoadmapGenerator
from .engines.export import FileExporter
from .engines.importers import NotionImporter

# Data models
from .items import Roadmap, Project, Milestone, Epic, Story, Task

# LLM clients
from .clients import LLMClientFactory, BaseLLMClient, ClaudeLLMClient, OpenAILLMClient, GeminiLLMClient

# Prompt system
from .prompts import RoadmapPromptBuilder

# CLI
from .main_cli import ArcaneCLI

__version__ = "2.0.0"

__all__ = [
    # Core engines
    "RoadmapGenerator",
    "FileExporter",
    "NotionImporter",

    # Data models
    "Roadmap",
    "Project",
    "Milestone",
    "Epic",
    "Story",
    "Task",

    # LLM clients
    "LLMClientFactory",
    "BaseLLMClient",
    "ClaudeLLMClient",
    "OpenAILLMClient",
    "GeminiLLMClient",

    # Utilities
    "RoadmapPromptBuilder",
    "ArcaneCLI",
]