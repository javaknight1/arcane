#!/usr/bin/env python3
"""Main entry point for the roadmap-notion package.

Provides multiple command options for different workflows.
"""

import argparse
import sys
from pathlib import Path

from .cli import main as cli_main
from .importer import main as importer_main
from .parser import main as parser_main


def main():
    """Main entry point with command selection."""
    parser = argparse.ArgumentParser(
        prog='roadmap-notion',
        description='Roadmap generation and Notion import toolkit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  generate    Interactive roadmap generation (LLM → roadmap → CSV → Notion)
  import      Import existing CSV file to Notion
  parse       Convert roadmap text file to CSV

Examples:
  python -m roadmap_notion generate           # Interactive full workflow
  python -m roadmap_notion import data.csv    # Import CSV to Notion
  python -m roadmap_notion parse roadmap.txt  # Convert text to CSV
        """
    )

    parser.add_argument(
        'command',
        choices=['generate', 'import', 'parse'],
        help='Command to execute'
    )

    parser.add_argument(
        'file',
        nargs='?',
        help='File to process (required for import/parse commands)'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='Output file path (for parse command)'
    )

    # Parse arguments
    if len(sys.argv) == 1:
        # No arguments provided, show help
        parser.print_help()
        return

    args = parser.parse_args()

    # Execute appropriate command
    try:
        if args.command == 'generate':
            # Interactive roadmap generation
            cli_main()

        elif args.command == 'import':
            if not args.file:
                print("Error: import command requires a CSV file path")
                parser.print_help()
                return

            # Import CSV to Notion
            sys.argv = ['roadmap_notion.importer', args.file]
            importer_main()

        elif args.command == 'parse':
            if not args.file:
                print("Error: parse command requires a text file path")
                parser.print_help()
                return

            # Parse roadmap text to CSV
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File not found: {args.file}")
                return

            output_path = args.output or str(file_path.with_suffix('.csv'))

            # Set up arguments for parser
            sys.argv = ['roadmap_notion.parser', str(file_path), output_path]
            parser_main()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()