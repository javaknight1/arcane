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

Interactive Mode Examples:
  python -m arcane interactive                                    # Full interactive workflow with guided generation
  python -m arcane interactive --provider claude                 # Skip LLM selection
  python -m arcane interactive --provider claude --timeline 6-months --complexity moderate --team-size 2-3 --focus mvp
                                                                  # Skip preference prompts
  python -m arcane interactive --idea-file myidea.txt --no-export # Use idea file, skip export
  python -m arcane interactive --output-dir ./generated          # Use specific output directory

Other Commands:
  python -m arcane generate --idea "Task manager"                # Generate only
  python -m arcane export --roadmap roadmap.json                 # Export only
  python -m arcane import --roadmap roadmap.json                 # Import only
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
        '--output-dir',
        help='Output directory for generated files (default: output)'
    )

    parser.add_argument(
        '--idea-file',
        help='Path to text file containing project idea description'
    )

    parser.add_argument(
        '--timeline',
        choices=['3-months', '6-months', '12-months'],
        help='Project timeline (skips timeline prompt)'
    )

    parser.add_argument(
        '--complexity',
        choices=['simple', 'moderate', 'complex'],
        help='Technical complexity level (skips complexity prompt)'
    )

    parser.add_argument(
        '--team-size',
        choices=['1', '2-3', '4-8', '8+'],
        help='Development team size (skips team size prompt)'
    )

    parser.add_argument(
        '--focus',
        choices=['mvp', 'feature', 'migration', 'optimization'],
        help='Primary project focus (skips focus prompt)'
    )

    parser.add_argument(
        '--no-export',
        action='store_true',
        help='Skip file export (no CSV/JSON files created)'
    )


    parser.add_argument(
        '--formats',
        nargs='+',
        choices=['csv', 'json', 'yaml'],
        default=['csv'],
        help='Export formats (default: csv only)'
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
            # Full interactive workflow with optional pre-set arguments
            cli = ArcaneCLI()
            cli.run(
                provider=getattr(args, 'provider', None),
                idea_file=getattr(args, 'idea_file', None),
                output_dir=getattr(args, 'output_dir', None),
                timeline=getattr(args, 'timeline', None),
                complexity=getattr(args, 'complexity', None),
                team_size=getattr(args, 'team_size', None),
                focus=getattr(args, 'focus', None),
                no_export=getattr(args, 'no_export', False),
                formats=getattr(args, 'formats', ['csv'])
            )

        elif args.command in ['generate', 'export', 'import']:
            print(f"Note: The '{args.command}' command has been deprecated.")
            print("Please use the 'interactive' mode for the full roadmap generation workflow.")
            print("\nRunning interactive mode...")
            cli = ArcaneCLI()
            cli.run()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()