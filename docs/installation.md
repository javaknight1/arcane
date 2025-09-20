# Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Notion account with API access
- API keys for your chosen LLM provider (Claude, OpenAI, or Gemini)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd arcane
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** This installs all dependencies including optional LLM providers. If you only plan to use one LLM provider, you can install dependencies selectively:

```bash
# Core dependencies only
pip install notion-client python-dotenv rich inquirer

# Then add your preferred LLM provider
pip install anthropic        # For Claude
pip install openai          # For OpenAI
pip install google-generativeai  # For Gemini
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:

```env
# Notion Configuration (Required)
NOTION_TOKEN=your_notion_integration_token
NOTION_PARENT_PAGE_ID=your_parent_page_id

# LLM Provider API Keys (Choose one or more)
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
```

### 5. Notion Setup

1. **Create a Notion Integration:**
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Give it a name and select your workspace
   - Copy the "Internal Integration Token" to your `.env` file

2. **Get Parent Page ID:**
   - Create or navigate to the Notion page where you want the roadmap
   - Copy the page ID from the URL (the 32-character string after the last `/`)
   - Add it to your `.env` file as `NOTION_PARENT_PAGE_ID`

3. **Share the page with your integration:**
   - In Notion, click "Share" on your parent page
   - Invite your integration by name

### 6. LLM Provider Setup

Choose at least one LLM provider and set up API access:

#### Claude (Anthropic)
1. Go to https://console.anthropic.com/
2. Create an API key
3. Add to `.env` as `ANTHROPIC_API_KEY`

#### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create an API key
3. Add to `.env` as `OPENAI_API_KEY`

#### Google Gemini
1. Go to https://makersuite.google.com/app/apikey
2. Create an API key
3. Add to `.env` as `GOOGLE_API_KEY`

## Verification

Test your installation:

```bash
python -m arcane --help
```

You should see the CLI help message indicating successful installation.

## Troubleshooting

### Common Issues

1. **"Module not found" errors**: Ensure virtual environment is activated and dependencies are installed
2. **"Invalid API key" errors**: Double-check your API keys in the `.env` file
3. **"Permission denied" errors**: Ensure your Notion integration has access to the parent page

### Getting Help

If you encounter issues:
1. Check the [troubleshooting guide](troubleshooting.md)
2. Review the [FAQ](faq.md)
3. Open an issue on the project repository