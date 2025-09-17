"""Application settings and constants."""

# Default project preferences
DEFAULT_TIMELINE = '6-months'
DEFAULT_COMPLEXITY = 'moderate'
DEFAULT_TEAM_SIZE = '2-3'
DEFAULT_FOCUS = 'mvp'

# Valid status values
VALID_STATUSES = [
    'Not Started',
    'In Progress',
    'Completed',
    'Blocked',
    'Cancelled'
]

# Priority levels
PRIORITY_LEVELS = {
    'Project': 'Critical',
    'Milestone': 'Critical',
    'Epic': 'Critical',
    'Story': 'High',
    'Task': 'Medium'
}

# Duration multipliers (in hours)
DURATION_MULTIPLIERS = {
    'hour': 1,
    'hours': 1,
    'day': 8,
    'days': 8,
    'week': 40,
    'weeks': 40,
    'month': 160,
    'months': 160
}

# LLM model configurations
LLM_MODELS = {
    'claude': {
        'model': 'claude-3-5-sonnet-20241022',
        'max_tokens': 8000,
        'temperature': 0.7
    },
    'openai': {
        'model': 'gpt-4-turbo-preview',
        'max_tokens': 8000,
        'temperature': 0.7
    },
    'gemini': {
        'model': 'gemini-1.5-pro',
        'max_tokens': 8000,
        'temperature': 0.7
    }
}

# Export formats
EXPORT_FORMATS = ['csv', 'json', 'yaml']

# CSV field names
CSV_FIELDNAMES = [
    'Name',
    'Type',
    'Parent',
    'Duration',
    'Priority',
    'Status',
    'Goal/Description',
    'Benefits',
    'Prerequisites',
    'Technical Requirements',
    'Claude Code Prompt'
]