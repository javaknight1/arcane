#!/usr/bin/env python3
"""Arcane API Usage Examples"""

import os
from arcane import (
    RoadmapGenerationEngine,
    FileExportEngine,
    NotionImportEngine,
    LLMClientFactory,
    PromptBuilder,
    Project,
    Milestone,
    Epic,
    Story,
    Task,
    Roadmap
)


def basic_generation_example():
    """Basic roadmap generation example."""
    print("=== Basic Roadmap Generation ===")

    # Generate roadmap using the engine
    engine = RoadmapGenerationEngine('claude')

    preferences = {
        'timeline': '6-months',
        'complexity': 'moderate',
        'team_size': '2-3',
        'focus': 'mvp'
    }

    idea = "Build a task management web application with real-time collaboration"
    roadmap = engine.generate_roadmap(idea, preferences)

    print(f"Generated roadmap: {roadmap.project.name}")
    stats = roadmap.get_statistics()
    print(f"Statistics: {stats}")

    return roadmap


def export_example(roadmap):
    """Export roadmap to multiple formats."""
    print("\n=== Export Example ===")

    exporter = FileExportEngine()

    # Export to all formats
    exported_files = exporter.export_multiple(
        roadmap,
        'example_roadmap',
        formats=['csv', 'json', 'yaml']
    )

    print(f"Exported files: {exported_files}")

    # Export to specific format
    csv_file = exporter.export(roadmap, 'specific_export.csv', 'csv')
    print(f"CSV file: {csv_file}")


def import_example(roadmap):
    """Import roadmap to Notion."""
    print("\n=== Notion Import Example ===")

    # Check if Notion credentials are available
    if not os.getenv('NOTION_TOKEN') or not os.getenv('NOTION_PARENT_PAGE_ID'):
        print("Skipping Notion import (missing environment variables)")
        print("Set NOTION_TOKEN and NOTION_PARENT_PAGE_ID to test Notion import")
        return

    try:
        importer = NotionImportEngine()
        result = importer.import_roadmap(roadmap)
        print(f"Notion import successful!")
        print(f"Container page: {result.get('container_page_id')}")
        print(f"Database: {result.get('database_id')}")
    except Exception as e:
        print(f"Notion import failed: {e}")


def llm_clients_example():
    """Example of using different LLM clients."""
    print("\n=== LLM Clients Example ===")

    providers = ['claude', 'openai', 'gemini']

    for provider in providers:
        try:
            client = LLMClientFactory.create(provider)
            print(f"✅ {provider} client created successfully")

            # Test with a simple prompt
            prompt = "What are the key phases of software development?"
            # response = client.generate(prompt)  # Uncomment to test
            print(f"   {provider} client ready for generation")

        except Exception as e:
            print(f"❌ {provider} client failed: {e}")


def prompt_builder_example():
    """Example of using the prompt builder."""
    print("\n=== Prompt Builder Example ===")

    builder = PromptBuilder()

    # Build a roadmap generation prompt
    prompt = builder.build_roadmap_prompt(
        idea_content="AI-powered customer service chatbot",
        timeline="4-months",
        complexity="complex",
        team_size="4-8",
        focus="feature"
    )

    print(f"Generated prompt length: {len(prompt)} characters")
    print(f"Prompt preview: {prompt[:200]}...")

    # Build other types of prompts
    milestone_prompt = builder.build_milestone_refinement_prompt(
        "Milestone 1: Foundation Setup"
    )
    print(f"Milestone refinement prompt ready: {len(milestone_prompt)} chars")


def manual_roadmap_creation():
    """Example of manually creating roadmap objects."""
    print("\n=== Manual Roadmap Creation ===")

    # Create project
    project = Project(
        name="Custom Task Manager",
        description="A manually created roadmap example"
    )

    # Create milestone
    milestone = Milestone(
        name="MVP Development",
        number="1",
        parent=project,
        duration=320,  # hours
        description="Build the minimum viable product"
    )

    # Create epic
    epic = Epic(
        name="User Authentication",
        number="1.0",
        parent=milestone,
        duration=80,
        description="Implement user registration and login"
    )

    # Create story
    story = Story(
        name="User Registration",
        number="1.0.1",
        parent=epic,
        duration=24,
        description="Allow users to create accounts",
        technical_requirements="Email validation, password hashing"
    )

    # Create tasks
    task1 = Task(
        name="Create registration form",
        number="1.0.1.1",
        parent=story,
        duration=8,
        description="Build frontend registration form"
    )

    task2 = Task(
        name="Implement backend validation",
        number="1.0.1.2",
        parent=story,
        duration=16,
        description="Add server-side validation and user creation"
    )

    # Create roadmap
    roadmap = Roadmap(project)

    print(f"Created roadmap: {roadmap.project.name}")
    stats = roadmap.get_statistics()
    print(f"Manual roadmap stats: {stats}")

    return roadmap


def advanced_roadmap_analysis(roadmap):
    """Advanced analysis of roadmap data."""
    print("\n=== Advanced Roadmap Analysis ===")

    # Get all items by type
    milestones = roadmap.get_milestones()
    epics = roadmap.get_epics()
    stories = roadmap.get_stories()
    tasks = roadmap.get_tasks()

    print(f"Breakdown:")
    print(f"  Milestones: {len(milestones)}")
    print(f"  Epics: {len(epics)}")
    print(f"  Stories: {len(stories)}")
    print(f"  Tasks: {len(tasks)}")

    # Analyze durations
    total_duration = roadmap.project.calculate_total_duration()
    print(f"  Total estimated hours: {total_duration}")

    # Find items by criteria
    long_stories = [s for s in stories if s.duration and s.duration > 40]
    print(f"  Stories > 40 hours: {len(long_stories)}")

    # Status analysis
    all_items = roadmap.get_all_items()
    status_counts = {}
    for item in all_items:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1

    print(f"  Status breakdown: {status_counts}")


if __name__ == "__main__":
    print("🚀 Arcane API Examples")
    print("=" * 50)

    # Run examples
    roadmap = basic_generation_example()
    export_example(roadmap)
    import_example(roadmap)
    llm_clients_example()
    prompt_builder_example()

    manual_roadmap = manual_roadmap_creation()
    advanced_roadmap_analysis(manual_roadmap)

    print("\n" + "=" * 50)
    print("✅ All examples completed!")
    print("Check the generated files and try the different APIs.")