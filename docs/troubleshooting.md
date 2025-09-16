# Troubleshooting Guide

This guide helps resolve common issues when using the Roadmap Notion tool.

## Installation Issues

### Python Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'roadmap_notion'
```

**Solutions:**
1. Ensure virtual environment is activated:
   ```bash
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify you're in the correct directory:
   ```bash
   ls -la  # Should show roadmap_notion/ directory
   ```

### Package Dependencies

**Error:**
```
ImportError: No module named 'anthropic'/'openai'/'google.generativeai'
```

**Solution:**
Install the specific LLM provider package:
```bash
pip install anthropic        # For Claude
pip install openai          # For OpenAI
pip install google-generativeai  # For Gemini
```

## Environment Configuration

### Missing Environment Variables

**Error:**
```
❌ Error: NOTION_TOKEN and NOTION_PARENT_PAGE_ID must be set in .env file
```

**Solutions:**
1. Create `.env` file in project root:
   ```bash
   touch .env
   ```

2. Add required variables:
   ```env
   NOTION_TOKEN=your_token_here
   NOTION_PARENT_PAGE_ID=your_page_id_here
   ```

3. Verify `.env` file is not in `.gitignore` if you expect it to be tracked

### Invalid API Keys

**Error:**
```
RuntimeError: Claude API error: Invalid API key
```

**Solutions:**
1. Verify API key format (should be long alphanumeric string)
2. Check for extra spaces or characters in `.env` file
3. Regenerate API key from provider console
4. Ensure sufficient credits/quota on API account

## Notion Integration

### Permission Denied

**Error:**
```
NotionClientError: Could not find database with ID: ...
```

**Solutions:**
1. **Share page with integration:**
   - Go to your Notion page
   - Click "Share" button
   - Invite your integration by name
   - Ensure it has "Can edit" permissions

2. **Verify parent page ID:**
   - Copy URL of your Notion page
   - Extract 32-character ID from URL
   - Should look like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

3. **Check integration permissions:**
   - Go to https://www.notion.so/my-integrations
   - Verify integration is active
   - Check workspace permissions

### Database Creation Fails

**Error:**
```
NotionClientError: body failed validation
```

**Solutions:**
1. Ensure parent page exists and is accessible
2. Verify integration has database creation permissions
3. Check if page already contains maximum number of blocks (rare)

## File Processing

### Roadmap File Not Found

**Error:**
```
❌ Error: Input file 'roadmap.txt' not found!
```

**Solutions:**
1. Verify file path is correct:
   ```bash
   ls -la roadmap.txt
   ```

2. Use absolute path:
   ```bash
   python -m roadmap_notion parse /full/path/to/roadmap.txt
   ```

3. Check file permissions:
   ```bash
   chmod 644 roadmap.txt
   ```

### CSV Parsing Errors

**Error:**
```
❌ No items to save!
```

**Solutions:**
1. **Check file format:** Ensure roadmap file follows expected hierarchy:
   ```
   ## Milestone 1: Name
   ### Epic 1.0: Name
   #### Story 1.0.1: Name
   ##### Task 1.0.1.1: Name
   ```

2. **Verify encoding:** Use UTF-8 encoding for special characters

3. **Check for empty lines:** Remove excessive empty lines that might break parsing

## LLM Generation Issues

### Generation Timeout

**Error:**
```
RuntimeError: OpenAI API error: Request timed out
```

**Solutions:**
1. **Simplify project description:** Reduce complexity of input
2. **Retry generation:** Temporary API issues are common
3. **Switch providers:** Try different LLM if one is having issues
4. **Check API status:** Visit provider status pages

### Poor Quality Output

**Issues:**
- Generated roadmap is too generic
- Missing important project details
- Incorrect hierarchy structure

**Solutions:**
1. **Improve project description:**
   ```txt
   # Bad
   "A web app for managing tasks"

   # Good
   "A field service management SaaS platform for HVAC companies with:
   - Work order scheduling and dispatch
   - GPS tracking for technicians
   - Customer portal for service requests
   - Integration with QuickBooks for billing
   - Mobile apps for iOS and Android"
   ```

2. **Adjust complexity settings:** Match technical complexity to your team's capabilities

3. **Use appropriate timeline:** Longer timelines generate more detailed roadmaps

## Import Process Issues

### Partial Import

**Error:**
```
Warning: Could not set parent relationship for Task X: ...
```

**Solutions:**
1. **Check parent names:** Ensure parent item names exactly match
2. **Verify CSV structure:** Parent column should reference exact Name values
3. **Review hierarchy:** Ensure proper nesting (Task → Story → Epic → Milestone)

### Memory Issues

**Error:**
```
MemoryError: Unable to allocate array
```

**Solutions:**
1. **Break down large roadmaps:** Split into multiple smaller imports
2. **Increase system memory:** Close other applications
3. **Process in batches:** Import milestones one at a time

## Performance Issues

### Slow Generation

**Symptoms:**
- Long delays during AI generation
- CLI appears frozen

**Solutions:**
1. **Check internet connection:** Ensure stable connection to API providers
2. **Reduce complexity:** Simplify project requirements
3. **Monitor API quotas:** You may be hitting rate limits

### Slow Import

**Symptoms:**
- Long delays during Notion import
- Many items to process

**Solutions:**
1. **Normal behavior:** Large roadmaps (100+ items) take time
2. **Monitor progress:** Look for progress indicators in output
3. **Avoid interruption:** Let process complete fully

## Debug Mode

Enable verbose output for troubleshooting:

```bash
export DEBUG=1
python -m roadmap_notion
```

This will show:
- API request/response details
- File processing steps
- Detailed error messages

## Common Fixes

### Reset Environment

If multiple issues persist:

1. **Clean virtual environment:**
   ```bash
   deactivate
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Verify all environment variables:**
   ```bash
   python -c "import os; print([k for k in os.environ.keys() if 'API' in k or 'NOTION' in k])"
   ```

3. **Test basic functionality:**
   ```bash
   python -c "from roadmap_notion.cli import RoadmapCLI; print('Import successful')"
   ```

### Clean State

Start fresh with a new Notion page:

1. Create new Notion page
2. Share with integration
3. Update `NOTION_PARENT_PAGE_ID` in `.env`
4. Run import again

## Getting Additional Help

If issues persist:

1. **Check existing issues:** Search project repository for similar problems
2. **Gather information:**
   - Python version: `python --version`
   - OS and version
   - Error messages (full stack trace)
   - Steps to reproduce

3. **Create detailed issue:**
   - Include system information
   - Attach relevant files (anonymized)
   - Describe expected vs actual behavior

4. **Temporary workarounds:**
   - Use different LLM provider
   - Manually edit CSV files
   - Import smaller sections at a time

## Error Code Reference

| Error Code | Meaning | Solution |
|------------|---------|----------|
| `401` | Unauthorized API access | Check API keys |
| `403` | Forbidden Notion access | Share page with integration |
| `404` | Resource not found | Verify page/database IDs |
| `429` | Rate limit exceeded | Wait and retry |
| `500` | Server error | Retry or switch providers |