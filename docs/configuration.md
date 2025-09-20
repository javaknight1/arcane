# 🔧 Arcane CLI Configuration Guide

This guide explains how to configure the Arcane CLI to customize its behavior, performance, and output according to your needs.

## 📁 Configuration File Location

Arcane looks for configuration files in the following order:

1. `~/.arcane/config.yaml` (user-specific configuration)
2. `./config.yaml` (project-specific configuration)
3. Environment-specific files: `config.development.yaml`, `config.testing.yaml`, `config.production.yaml`
4. Built-in defaults (if no configuration file is found)

## 🚀 Quick Setup

### 1. Create Configuration Directory
```bash
mkdir -p ~/.arcane
```

### 2. Create Your Configuration File
```bash
touch ~/.arcane/config.yaml
```

### 3. Add Your Basic Settings
```yaml
# Minimal configuration example
llm:
  default_provider: "claude"

generation:
  interactive_mode: true
  default_timeline: "6-months"

files:
  default_output_dir: "./my-roadmaps"
```

## 📚 Complete Configuration Reference

### 🤖 LLM Settings

Controls how Arcane interacts with AI language models for roadmap generation.

```yaml
llm:
  default_provider: "claude"           # Which LLM to use by default
  default_model: "claude-3-sonnet"     # Specific model version
  max_tokens: 4000                     # Maximum tokens per request
  temperature: 0.7                     # Creativity level (0.0-1.0)
  enable_cost_estimation: true         # Show estimated costs
  cost_threshold_warning: 1.0          # Warn if cost exceeds this ($)
  rate_limit_delay: 1.0               # Delay between requests (seconds)
  api_keys: {}                        # Store API keys (use environment variables instead)
```

#### Field Explanations:

- **`default_provider`**: The AI service to use
  - Options: `"claude"`, `"openai"`, `"gemini"`
  - Purpose: Determines which AI service generates your roadmaps
  - Impact: Different providers have different strengths and pricing

- **`default_model`**: Specific model version within the provider
  - Examples: `"claude-3-sonnet"`, `"gpt-4"`, `"gemini-pro"`
  - Purpose: Controls the capability and cost of AI generation
  - Impact: Newer models are usually more capable but more expensive

- **`max_tokens`**: Maximum length of AI responses
  - Range: 1000-8000 (depends on provider)
  - Purpose: Controls how detailed the generated roadmaps can be
  - Impact: Higher values allow more detailed roadmaps but cost more

- **`temperature`**: Controls AI creativity vs consistency
  - Range: 0.0 (very consistent) to 1.0 (very creative)
  - Purpose: Balances predictable vs innovative roadmap content
  - Recommended: 0.7 for good balance, 0.3 for consistency, 0.9 for creativity

- **`enable_cost_estimation`**: Show estimated costs before generation
  - Purpose: Helps you understand the financial impact of roadmap generation
  - Recommended: `true` for cost-conscious users

- **`cost_threshold_warning`**: Alert when estimated cost exceeds this amount
  - Purpose: Prevents accidentally expensive operations
  - Units: USD
  - Recommended: Set based on your budget comfort level

- **`rate_limit_delay`**: Pause between API requests
  - Purpose: Prevents hitting rate limits with AI providers
  - Units: Seconds
  - Impact: Higher values are safer but slower; lower values are faster but may hit limits

### ⚙️ Generation Settings

Controls how roadmaps are generated and what defaults are used.

```yaml
generation:
  interactive_mode: true               # Prompt user for preferences
  save_outputs: true                   # Save generated files
  cache_templates: true                # Cache prompt templates
  validate_inputs: true                # Validate user inputs
  max_retries: 3                      # Retry failed requests
  request_timeout: 30.0               # Timeout for API requests (seconds)

  # Default values when not specified
  default_timeline: "6-months"        # Project duration
  default_complexity: "moderate"      # Technical complexity
  default_team_size: 3                # Development team size

  # Generation behavior
  mode_choices: ["automatic", "interactive"]
  default_mode: "automatic"

  # Token estimation for cost calculation
  outline_output_tokens: 3000         # Expected outline length
  milestone_output_tokens: 400        # Expected milestone detail
  epic_output_tokens: 800            # Expected epic detail
  story_output_tokens: 1200          # Expected story detail

  # Roadmap structure based on timeline
  milestones_per_timeline:
    "3-months": 3                     # Short projects
    "6-months": 4                     # Medium projects
    "12-months": 6                    # Long projects

  # Complexity affects roadmap detail
  epics_per_milestone:
    simple: 1.5                       # Fewer features for simple projects
    moderate: 2.0                     # Standard feature count
    complex: 3.0                      # More features for complex projects

  stories_per_epic:
    simple: 2                         # Basic functionality
    moderate: 2                       # Standard functionality
    complex: 3                        # Detailed functionality

  tasks_per_story:
    simple: 3                         # Basic implementation steps
    moderate: 4                       # Standard implementation steps
    complex: 5                        # Detailed implementation steps
```

#### Field Explanations:

- **`interactive_mode`**: Whether to prompt user for roadmap preferences
  - `true`: Ask questions to customize the roadmap
  - `false`: Use defaults and CLI flags only
  - Purpose: Controls user experience - interactive vs automated

- **`save_outputs`**: Whether to save generated roadmaps to files
  - Purpose: Useful for testing vs production use
  - `false`: Only display results, don't save files

- **`cache_templates`**: Store prompt templates in memory for reuse
  - Purpose: Improves performance for multiple generations
  - `false`: Reload templates each time (useful for development)

- **`validate_inputs`**: Check user inputs for consistency
  - Purpose: Prevents common configuration mistakes
  - `false`: Skip validation (faster but potentially problematic)

- **`max_retries`**: How many times to retry failed API requests
  - Purpose: Handles temporary network or API issues
  - Range: 1-5 (higher values more resilient but slower on permanent failures)

- **`request_timeout`**: Maximum wait time for API responses
  - Purpose: Prevents hanging on slow API responses
  - Units: Seconds
  - Recommended: 30-60 seconds depending on your patience

- **Default Values**: Used when user doesn't specify preferences
  - Purpose: Provides sensible starting points
  - Impact: Affects the generated roadmap structure and detail

- **Token Estimation**: Used for cost calculation
  - Purpose: Predicts how much each roadmap component will cost
  - Impact: More accurate estimates help with budget planning

- **Structure Ratios**: Control roadmap hierarchy and detail
  - Purpose: Balances comprehensiveness with manageability
  - Impact: Higher values create more detailed but longer roadmaps

### 📁 File Operation Settings

Controls where and how files are saved and organized.

```yaml
files:
  default_output_dir: "./output"              # Where to save roadmaps
  template_cache_dir: "./cache/templates"     # Template storage
  progress_save_dir: "./output/progress"      # Progress tracking files
  default_project_name: "roadmap"            # Default filename base
  timestamp_format: "%Y%m%d_%H%M%S"          # Timestamp format

  # Directory structure
  run_directory_pattern: "{timestamp}"        # Unique folder per run

  # File naming patterns
  outline_filename_pattern: "{project_name}_outline.md"
  roadmap_filename_pattern: "{project_name}_complete.md"
  progress_filename_pattern: "{project_name}_progress.json"

  # Export capabilities
  supported_export_formats:
    - "md"                                    # Markdown files
    - "json"                                  # JSON data
    - "csv"                                   # Spreadsheet format
    - "yaml"                                  # YAML data
    - "html"                                  # Web pages
```

#### Field Explanations:

- **`default_output_dir`**: Base directory for all generated files
  - Purpose: Organizes your roadmaps in a consistent location
  - Examples: `"./roadmaps"`, `"~/Documents/Projects"`, `"/tmp/arcane"`

- **`template_cache_dir`**: Where to store cached prompt templates
  - Purpose: Improves performance by avoiding template reloading
  - Impact: Uses disk space but speeds up repeated generations

- **`progress_save_dir`**: Where to save generation progress (for resuming)
  - Purpose: Allows resuming interrupted long generations
  - Impact: Useful for complex roadmaps that take a long time

- **`default_project_name`**: Base name for generated files
  - Purpose: Creates recognizable filenames
  - Impact: Used when project name can't be determined from content

- **`timestamp_format`**: How timestamps appear in filenames and folders
  - Format: Python strftime format
  - Purpose: Ensures unique filenames and chronological sorting
  - Examples: `"%Y%m%d_%H%M%S"` → `20241215_143022`

- **Directory and File Patterns**: Control file organization
  - Variables: `{timestamp}`, `{project_name}`, `{date}`, `{time}`
  - Purpose: Creates organized, predictable file structures
  - Impact: Makes it easier to find and manage your roadmaps

- **`supported_export_formats`**: Which file formats Arcane can create
  - Purpose: Determines integration options with other tools
  - Impact: More formats = more flexibility for sharing and using roadmaps

### 🎨 Display and Console Settings

Controls how information is presented to you in the terminal.

```yaml
display:
  console_width: 120                   # Maximum line width
  show_progress: true                  # Show progress bars
  use_rich_formatting: true           # Use colors and formatting
  show_cost_warnings: true            # Display cost alerts
  verbose_logging: false              # Show detailed logs
  debug: false                        # Show debug information

  # Color scheme
  success_color: "green"              # Successful operations
  warning_color: "yellow"             # Warnings and cautions
  error_color: "red"                  # Errors and failures
  info_color: "cyan"                  # General information
  highlight_color: "bold cyan"        # Important highlights
```

#### Field Explanations:

- **`console_width`**: Maximum line width for text output
  - Purpose: Ensures readable formatting on different screen sizes
  - Range: 80-200 characters
  - Impact: Wider allows more information per line; narrower fits smaller screens

- **`show_progress`**: Display progress bars during generation
  - Purpose: Shows how long operations will take
  - `false`: Useful for scripted/automated usage

- **`use_rich_formatting`**: Enable colors, bold text, tables, etc.
  - Purpose: Makes output more readable and professional
  - `false`: Plain text only (useful for logs or simple terminals)

- **`show_cost_warnings`**: Display estimated costs and alerts
  - Purpose: Helps manage AI API expenses
  - `false`: Hide cost information (useful when cost isn't a concern)

- **`verbose_logging`**: Show detailed operation information
  - Purpose: Useful for troubleshooting or understanding what's happening
  - Impact: Much more output; can be overwhelming for normal use

- **`debug`**: Show technical debugging information
  - Purpose: For developers or when reporting issues
  - Impact: Very verbose output with technical details

- **Color Settings**: Customize the appearance of different message types
  - Options: `"red"`, `"green"`, `"yellow"`, `"blue"`, `"cyan"`, `"magenta"`, `"white"`, `"bold red"`, etc.
  - Purpose: Makes it easier to quickly identify different types of information
  - Impact: Purely aesthetic but improves usability

## 🌍 Environment-Specific Configuration

You can have different settings for development, testing, and production environments.

### Creating Environment Configs

Create separate files for each environment:

```bash
# Development settings
~/.arcane/config.development.yaml

# Testing settings
~/.arcane/config.testing.yaml

# Production settings
~/.arcane/config.production.yaml
```

### Development Environment Example

```yaml
# config.development.yaml
display:
  debug: true                         # Show debug info in development
  verbose_logging: true               # Detailed logs for debugging

generation:
  cache_templates: false              # Always reload templates (for template development)
  max_retries: 1                      # Fail fast in development
  validate_inputs: true               # Catch issues early

llm:
  cost_threshold_warning: 0.5         # Lower threshold in development
  temperature: 0.3                    # More consistent for testing

files:
  default_output_dir: "./dev-output"  # Separate dev files
```

### Testing Environment Example

```yaml
# config.testing.yaml
generation:
  save_outputs: false                 # Don't clutter with test files
  interactive_mode: false             # Automated testing

llm:
  default_provider: "mock"            # Use mock provider for tests
  enable_cost_estimation: false       # No costs in testing

display:
  show_progress: false                # Clean test output
  use_rich_formatting: false          # Plain text for CI/CD
```

### Production Environment Example

```yaml
# config.production.yaml
generation:
  max_retries: 5                      # More resilient in production
  request_timeout: 60.0               # Longer timeout for reliability

llm:
  cost_threshold_warning: 5.0         # Higher threshold for production use
  rate_limit_delay: 2.0               # Conservative rate limiting

display:
  verbose_logging: false              # Clean production output
  debug: false                        # No debug info in production

files:
  default_output_dir: "/var/arcane/output"  # Production file location
```

## 🔐 Security Best Practices

### API Key Management

**❌ Don't do this:**
```yaml
llm:
  api_keys:
    anthropic: "sk-ant-123456..."     # Never store keys in config files
```

**✅ Do this instead:**
```bash
# Use environment variables
export ANTHROPIC_API_KEY="sk-ant-123456..."
export OPENAI_API_KEY="sk-proj-123456..."
export GOOGLE_API_KEY="AIza123456..."
```

### File Permissions

Protect your configuration files:
```bash
chmod 600 ~/.arcane/config.yaml      # Only you can read/write
chmod 700 ~/.arcane/                 # Only you can access the directory
```

## 🛠️ Common Configuration Scenarios

### Scenario 1: Cost-Conscious User

```yaml
llm:
  default_provider: "claude"          # Generally cost-effective
  max_tokens: 2000                    # Limit response length
  enable_cost_estimation: true        # Always show costs
  cost_threshold_warning: 0.50        # Alert at 50 cents

generation:
  default_complexity: "simple"        # Shorter roadmaps
  milestones_per_timeline:
    "6-months": 3                     # Fewer milestones = less cost
```

### Scenario 2: Enterprise User

```yaml
llm:
  default_provider: "openai"          # Enterprise-grade
  max_tokens: 8000                    # Detailed roadmaps
  cost_threshold_warning: 10.0        # Higher budget

generation:
  default_complexity: "complex"       # Detailed enterprise roadmaps
  validate_inputs: true               # Ensure quality
  max_retries: 5                      # High reliability

files:
  default_output_dir: "/shared/roadmaps"  # Team-accessible location
```

### Scenario 3: Developer/Testing

```yaml
llm:
  temperature: 0.1                    # Very consistent for testing

generation:
  interactive_mode: false             # Scriptable
  save_outputs: true                  # Keep test artifacts

display:
  debug: true                         # See what's happening
  verbose_logging: true               # Detailed logs
  use_rich_formatting: false          # Plain text for logs
```

### Scenario 4: Quick Prototyping

```yaml
generation:
  default_timeline: "3-months"        # Fast projects
  default_complexity: "simple"        # MVP focus
  interactive_mode: false             # Skip questions

llm:
  temperature: 0.9                    # More creative suggestions

files:
  default_output_dir: "./prototypes"  # Organized folder
```

## 🔄 Configuration Loading Order

Arcane loads configuration in this priority order (later files override earlier ones):

1. **Built-in defaults** (lowest priority)
2. **System-wide config**: `/etc/arcane/config.yaml`
3. **User config**: `~/.arcane/config.yaml`
4. **Project config**: `./config.yaml`
5. **Environment config**: `./config.{environment}.yaml`
6. **Command-line flags** (highest priority)

This allows you to have:
- Personal defaults in `~/.arcane/config.yaml`
- Project-specific overrides in `./config.yaml`
- Environment-specific settings for dev/test/prod
- One-off overrides with command-line flags

## 🐛 Troubleshooting Configuration

### Common Issues

**Configuration not loading:**
```bash
# Check if file exists and is readable
ls -la ~/.arcane/config.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('~/.arcane/config.yaml'))"
```

**Environment not detected:**
```bash
# Set environment explicitly
export ARCANE_ENV=development
```

**Permission issues:**
```bash
# Fix file permissions
chmod 600 ~/.arcane/config.yaml
chmod 700 ~/.arcane/
```

### Debug Configuration Loading

Enable debug mode to see what configuration is being loaded:

```bash
export DEBUG=1
python -m arcane --help
```

This will show you:
- Which config files were found and loaded
- What the final merged configuration looks like
- Any configuration validation errors

## 📝 Configuration Validation

Arcane validates your configuration and will warn you about:

- **Invalid values**: Wrong data types or out-of-range values
- **Missing required settings**: Critical configuration that must be set
- **Deprecated options**: Settings that are no longer supported
- **Conflicting settings**: Options that don't work well together

If validation fails, Arcane will:
1. Show you exactly what's wrong
2. Suggest how to fix it
3. Fall back to safe defaults when possible

## 🔗 Related Documentation

- [Installation Guide](installation.md) - Setting up Arcane CLI
- [Usage Guide](usage.md) - How to use Arcane CLI
- [CLI Reference](CLI_USAGE.md) - All command-line options
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

---

**Need help?** If you're having trouble with configuration, check the [troubleshooting guide](troubleshooting.md) or open an issue on GitHub with your configuration file (remove any sensitive information first!).