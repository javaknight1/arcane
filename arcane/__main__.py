#!/usr/bin/env python3
"""Main entry point for Arcane CLI.

Provides a simple command-line interface for AI-powered roadmap generation.
"""

import argparse
import sys
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

  # Use predefined profiles (skips ALL questions)
  python -m arcane interactive --profile mvp-startup             # Solo founder building MVP
  python -m arcane interactive --profile ai-startup --provider openai # AI startup with different LLM
  python -m arcane interactive --profile enterprise-migration    # Large team migration project
  python -m arcane interactive --profile healthcare-app          # HIPAA-compliant healthcare app
  python -m arcane interactive --profile fintech                 # Financial services platform

  # Skip basic roadmap prompts
  python -m arcane interactive --provider claude --timeline 6-months --complexity moderate --team-size 2-3 --focus mvp

  # Extended timeline and team size examples
  python -m arcane interactive --timeline 18-months --team-size 15                    # Large project with specific team size
  python -m arcane interactive --timeline "2.5 years" --team-size 30+               # Multi-year enterprise initiative
  python -m arcane interactive --timeline "4 months" --team-size 7                  # Custom timeline with exact team size

  # Include non-technical aspects in roadmap
  python -m arcane interactive --roadmap-aspects business-strategy marketing-sales
  python -m arcane interactive --roadmap-aspects legal-compliance operations risk-management # Enterprise focus

  # Skip industry context prompts
  python -m arcane interactive --industry healthcare --regulatory hipaa gdpr --market-maturity established --target-market national

  # Skip technical and team prompts
  python -m arcane interactive --technical-challenges realtime-data ml-ai --team-expertise expert --team-distribution remote-sync --dev-methodology agile

  # Skip budget and deployment prompts
  python -m arcane interactive --budget-range funded --infra-budget moderate --deployment-environment cloud --scaling-expectations viral

  # Skip integration prompts
  python -m arcane interactive --payment-integrations stripe --communication-integrations email sms --business-integrations analytics

  # Skip success metrics prompts
  python -m arcane interactive --success-metric revenue --success-timeline medium --measurement-approach mixed --failure-tolerance low

  # Comprehensive example (skip all prompts)
  python -m arcane interactive --provider claude --timeline 18-months --complexity moderate --team-size 12 --focus mvp \\
    --roadmap-aspects business-strategy marketing-sales legal-compliance \\
    --industry healthcare --regulatory hipaa --market-maturity established --target-market national \\
    --technical-challenges realtime-data integrations --team-expertise expert --dev-methodology agile \\
    --budget-range funded --deployment-environment cloud --success-metric revenue

  # File handling examples
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

    # Profile selection for predefined configurations
    parser.add_argument(
        '--profile',
        choices=['mvp-startup', 'enterprise-migration', 'ai-startup', 'mobile-app', 'ecommerce',
                'healthcare-app', 'fintech', 'microservices', 'blockchain', 'education-platform'],
        help='Use predefined profile (skips ALL questions). Profiles: mvp-startup (solo/bootstrap), '
             'enterprise-migration (large team), ai-startup (ML-focused), mobile-app (B2C), '
             'ecommerce, healthcare-app (HIPAA), fintech (compliance), microservices (scale), '
             'blockchain (Web3), education-platform (LMS)'
    )

    parser.add_argument(
        '--timeline',
        help='Project timeline: 3-months, 6-months, 12-months, 18-months, 24-months, 36-months, or custom (e.g., "4 months", "5 years") - skips timeline prompt'
    )

    parser.add_argument(
        '--complexity',
        choices=['simple', 'moderate', 'complex'],
        help='Technical complexity level (skips complexity prompt)'
    )

    parser.add_argument(
        '--team-size',
        help='Development team size: ranges (1, 2-3, 4-8, 9-15, 16-30, 30+) or specific number (e.g., 5, 12, 25) - skips team size prompt'
    )

    parser.add_argument(
        '--focus',
        choices=['mvp', 'feature', 'migration', 'optimization'],
        help='Primary project focus (skips focus prompt)'
    )

    parser.add_argument(
        '--scope-control',
        choices=['strict', 'standard', 'creative', 'expansive'],
        help='LLM creative liberty: strict (only direct items), standard (supporting items), creative (useful features), expansive (all enhancements) - skips scope control prompt'
    )

    parser.add_argument(
        '--roadmap-aspects',
        nargs='+',
        choices=['business-strategy', 'marketing-sales', 'legal-compliance', 'operations', 'customer-support', 'finance-accounting', 'hr-team', 'product-management', 'qa-testing', 'risk-management', 'technical-only'],
        help='Non-technical aspects to include in roadmap (can specify multiple, skips roadmap aspects prompt)'
    )

    # Industry context flags
    parser.add_argument(
        '--industry',
        choices=['b2b-saas', 'b2c-mobile', 'ecommerce', 'healthcare', 'finance', 'education', 'gaming', 'enterprise', 'government', 'non-profit', 'other'],
        help='Industry/domain (skips industry prompt)'
    )

    parser.add_argument(
        '--regulatory',
        nargs='+',
        choices=['gdpr', 'hipaa', 'pci-dss', 'soc2', 'iso27001', 'ferpa', 'fedramp', 'none'],
        help='Regulatory requirements (can specify multiple, skips regulatory prompt)'
    )

    parser.add_argument(
        '--market-maturity',
        choices=['greenfield', 'emerging', 'established', 'saturated'],
        help='Market maturity level (skips market maturity prompt)'
    )

    parser.add_argument(
        '--target-market',
        choices=['local', 'regional', 'national', 'global'],
        help='Target market size (skips target market prompt)'
    )

    # Technical challenges flags (Task 2)
    parser.add_argument(
        '--technical-challenges',
        nargs='+',
        choices=['realtime-data', 'high-concurrency', 'complex-logic', 'integrations', 'ml-ai', 'blockchain', 'iot-hardware', 'multi-tenant', 'offline-first', 'data-migrations', 'microservices', 'graphql-apis'],
        help='Technical challenges (can specify multiple, skips technical challenges prompt)'
    )

    # Enhanced team assessment flags (Task 3)
    parser.add_argument(
        '--team-expertise',
        choices=['learning', 'intermediate', 'expert', 'mixed'],
        help='Team expertise level (skips team expertise prompt)'
    )

    parser.add_argument(
        '--team-distribution',
        choices=['colocated', 'remote-sync', 'remote-async', 'hybrid'],
        help='Team distribution type (skips team distribution prompt)'
    )

    parser.add_argument(
        '--dev-methodology',
        choices=['agile', 'kanban', 'waterfall', 'adhoc'],
        help='Development methodology (skips methodology prompt)'
    )

    # Budget context flags (Task 4)
    parser.add_argument(
        '--budget-range',
        choices=['bootstrap', 'seed', 'funded', 'enterprise', 'undefined'],
        help='Overall budget range (skips budget range prompt)'
    )

    parser.add_argument(
        '--infra-budget',
        choices=['minimal', 'moderate', 'substantial', 'unlimited'],
        help='Monthly infrastructure budget (skips infrastructure budget prompt)'
    )

    parser.add_argument(
        '--services-budget',
        choices=['free', 'basic', 'professional', 'enterprise'],
        help='Third-party services budget (skips services budget prompt)'
    )

    # Deployment environment flags (Task 5)
    parser.add_argument(
        '--deployment-environment',
        choices=['cloud', 'serverless', 'kubernetes', 'traditional', 'on-premise', 'hybrid', 'edge'],
        help='Primary deployment environment (skips deployment environment prompt)'
    )

    parser.add_argument(
        '--geographic-distribution',
        choices=['single-region', 'multi-region', 'global', 'data-residency'],
        help='Geographic distribution needs (skips geographic distribution prompt)'
    )

    parser.add_argument(
        '--scaling-expectations',
        choices=['steady', 'daily-peaks', 'seasonal', 'viral', 'batch'],
        help='Scaling expectations (skips scaling expectations prompt)'
    )

    # Integration requirements flags (Task 6)
    parser.add_argument(
        '--payment-integrations',
        nargs='+',
        choices=['stripe', 'paypal', 'square', 'cryptocurrency', 'bank-transfers', 'none'],
        help='Payment integrations (can specify multiple, skips payment integrations prompt)'
    )

    parser.add_argument(
        '--communication-integrations',
        nargs='+',
        choices=['email', 'sms', 'push-notifications', 'in-app-chat', 'video-calls', 'none'],
        help='Communication integrations (can specify multiple, skips communication integrations prompt)'
    )

    parser.add_argument(
        '--business-integrations',
        nargs='+',
        choices=['crm', 'accounting', 'analytics', 'support', 'marketing-automation', 'none'],
        help='Business tool integrations (can specify multiple, skips business integrations prompt)'
    )

    parser.add_argument(
        '--developer-integrations',
        nargs='+',
        choices=['github-gitlab', 'ci-cd', 'monitoring', 'error-tracking', 'feature-flags', 'none'],
        help='Developer tool integrations (can specify multiple, skips developer integrations prompt)'
    )

    parser.add_argument(
        '--data-integrations',
        nargs='+',
        choices=['rest-apis', 'graphql-apis', 'webhooks', 'websockets', 'file-uploads', 'databases', 'none'],
        help='Data source integrations (can specify multiple, skips data integrations prompt)'
    )

    # Success metrics flags (Task 7)
    parser.add_argument(
        '--success-metric',
        choices=['adoption', 'revenue', 'cost-saving', 'speed', 'performance', 'satisfaction', 'innovation'],
        help='Primary success metric (skips success metric prompt)'
    )

    parser.add_argument(
        '--success-timeline',
        choices=['immediate', 'short', 'medium', 'long'],
        help='Success timeline (skips success timeline prompt)'
    )

    parser.add_argument(
        '--measurement-approach',
        choices=['quantitative', 'qualitative', 'mixed', 'none'],
        help='Measurement approach (skips measurement approach prompt)'
    )

    parser.add_argument(
        '--failure-tolerance',
        choices=['zero', 'low', 'moderate', 'high'],
        help='Acceptable failure rate (skips failure tolerance prompt)'
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
                scope_control=getattr(args, 'scope_control', None),
                roadmap_aspects=getattr(args, 'roadmap_aspects', None),
                industry=getattr(args, 'industry', None),
                regulatory=getattr(args, 'regulatory', None),
                market_maturity=getattr(args, 'market_maturity', None),
                target_market=getattr(args, 'target_market', None),
                technical_challenges=getattr(args, 'technical_challenges', None),
                team_expertise=getattr(args, 'team_expertise', None),
                team_distribution=getattr(args, 'team_distribution', None),
                dev_methodology=getattr(args, 'dev_methodology', None),
                budget_range=getattr(args, 'budget_range', None),
                infra_budget=getattr(args, 'infra_budget', None),
                services_budget=getattr(args, 'services_budget', None),
                deployment_environment=getattr(args, 'deployment_environment', None),
                geographic_distribution=getattr(args, 'geographic_distribution', None),
                scaling_expectations=getattr(args, 'scaling_expectations', None),
                payment_integrations=getattr(args, 'payment_integrations', None),
                communication_integrations=getattr(args, 'communication_integrations', None),
                business_integrations=getattr(args, 'business_integrations', None),
                developer_integrations=getattr(args, 'developer_integrations', None),
                data_integrations=getattr(args, 'data_integrations', None),
                success_metric=getattr(args, 'success_metric', None),
                success_timeline=getattr(args, 'success_timeline', None),
                measurement_approach=getattr(args, 'measurement_approach', None),
                failure_tolerance=getattr(args, 'failure_tolerance', None),
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