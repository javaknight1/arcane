#!/usr/bin/env python3
"""Main entry point for Arcane CLI.

Provides a simple command-line interface for AI-powered roadmap generation.
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .main_cli import ArcaneCLI
from .engines.generation import RoadmapGenerationEngine
from .engines.export import FileExportEngine
from .engines.import_engine import NotionImportEngine


def main():
    """Main entry point with command selection."""
    parser = argparse.ArgumentParser(
        prog='arcane',
        description='AI-powered roadmap generation and project integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  interactive    Full interactive roadmap generation workflow
  generate       Generate roadmap from idea (requires --idea)
  export         Export existing roadmap to files (requires --roadmap)
  import         Import roadmap to Notion (requires --roadmap)

Examples:
  python -m arcane interactive                    # Interactive workflow
  python -m arcane generate --idea "Task manager" # Generate only
  python -m arcane export --roadmap roadmap.json  # Export only
  python -m arcane import --roadmap roadmap.json  # Import only
        """
    )

    parser.add_argument(
        'command',
        choices=['interactive', 'generate', 'export', 'import'],
        help='Command to execute'
    )

    parser.add_argument(
        '--idea',
        help='Project idea description (for generate command)'
    )

    parser.add_argument(
        '--roadmap',
        help='Path to roadmap JSON file (for export/import commands)'
    )

    parser.add_argument(
        '--provider',
        choices=['claude', 'openai', 'gemini'],
        default='claude',
        help='LLM provider to use (default: claude)'
    )

    parser.add_argument(
        '--output',
        help='Output file base name (default: generated_roadmap)'
    )

    parser.add_argument(
        '--formats',
        nargs='+',
        choices=['csv', 'json', 'yaml'],
        default=['csv', 'json', 'yaml'],
        help='Export formats (default: all)'
    )

    # Parse arguments
    if len(sys.argv) == 1:
        # No arguments provided, run interactive mode
        cli = ArcaneCLI()
        cli.run()
        return

    args = parser.parse_args()

    # Execute appropriate command
    try:
        if args.command == 'interactive':
            # Full interactive workflow
            cli = ArcaneCLI()
            cli.run()

        elif args.command == 'generate':
            if not args.idea:
                print("Error: generate command requires --idea")
                parser.print_help()
                return

            # Generate roadmap only
            print(f"🤖 Generating roadmap with {args.provider}...")
            engine = RoadmapGenerationEngine(args.provider)
            roadmap = engine.generate_roadmap(args.idea, {})

            # Save to JSON for later use
            exporter = FileExportEngine()
            output_base = args.output or 'generated_roadmap'
            json_file = exporter.export(roadmap, f"{output_base}.json", "json")

            print(f"✅ Roadmap generated and saved to: {json_file}")
            stats = roadmap.get_statistics()
            print(f"📊 Generated {stats['total_items']} items across {stats['milestones']} milestones")

        elif args.command == 'export':
            if not args.roadmap:
                print("Error: export command requires --roadmap")
                parser.print_help()
                return

            # TODO: Load roadmap from JSON and export
            print("Error: Export from existing roadmap not yet implemented")
            print("Use 'interactive' or 'generate' commands instead")

        elif args.command == 'import':
            if not args.roadmap:
                print("Error: import command requires --roadmap")
                parser.print_help()
                return

            # TODO: Load roadmap from JSON and import to Notion
            print("Error: Import from existing roadmap not yet implemented")
            print("Use 'interactive' command for full workflow")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()