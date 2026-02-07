#!/bin/bash

# Arcane CLI - Simple Roadmap Generation
# This script includes a reasonable subset of flags for typical projects

python -m arcane interactive \
    --model claude \
    --output-dir output \
    --idea-file idea.txt \
    --timeline "12-months" \
    --complexity moderate \
    --focus mvp \
    --team-size 5 \
    --roadmap-aspects technical-only \
    --scope-control standard \
    --industry b2b-saas \
    --regulatory none \
    --market-maturity emerging \
    --target-market national \
    --technical-challenges integrations complex-logic \
    --team-expertise intermediate \
    --team-distribution remote-sync \
    --dev-methodology agile \
    --budget-range funded \
    --deployment-environment cloud \
    --geographic-distribution single-region \
    --scaling-expectations steady \
    --integrations payments notifications developer-tools \
    --success-metric adoption \
    --formats csv json
    # --export-to linear  # Uncomment to export to: notion, jira, asana, linear, trello, github_projects, azure_devops, monday, clickup, file_only, skip
