"""Arcane - AI-Powered Roadmap Generation CLI.

A comprehensive command-line tool that transforms ideas into actionable roadmaps
and integrates with project management tools. Built with a clean, modular
architecture for maximum flexibility and extensibility.
"""

# Core engines
from .engines.generation import NewGuidedRoadmapGenerator
from .engines.export import FileExportEngine
from .engines.import_engine import NotionImportEngine

# Data models
from .items import Roadmap, Project, Milestone, Epic, Story, Task

# LLM clients
from .llm_clients import LLMClientFactory, BaseLLMClient, ClaudeLLMClient, OpenAILLMClient, GeminiLLMClient

# Prompt system
from .prompts import PromptBuilder

# CLI
from .main_cli import ArcaneCLI

__version__ = "2.0.0"

__all__ = [
    # Core engines
    "NewGuidedRoadmapGenerator",
    "FileExportEngine",
    "NotionImportEngine",

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
    "PromptBuilder",
    "ArcaneCLI",
]