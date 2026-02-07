#!/bin/bash

# Arcane CLI - Solo Developer Side Project (Hybrid Mode)
# Uses Claude for outline generation (quality), Ollama for tasks ($0 cost)
# Requires: ollama pull llama3.2 (or your preferred model)
#
# This script uses the --preset solo flag to auto-fill most settings
# The preset sets: 1 dev, bootstrap budget, adhoc methodology, cloud deployment, etc.

python -m arcane interactive \
    --model ollama/qwen2.5:14b \
    --outline-model claude \
    --idea-file telchar.txt \
    --output-dir output \
    --preset solo \
    --timeline "6-months" \
    --complexity moderate \
    --focus mvp \
    --roadmap-aspects technical-only \
    --industry other \
    --market-maturity greenfield \
    --target-market local \
    --technical-challenges complex-logic \
    --success-metric adoption \
    --formats csv json yaml
    # --export-to linear  # Uncomment to export to: notion, jira, asana, linear, trello, github_projects, azure_devops, monday, clickup, file_only, skip
