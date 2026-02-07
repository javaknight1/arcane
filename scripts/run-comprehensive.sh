#!/bin/bash

# Arcane CLI - Comprehensive Business + Technical Roadmap
# This script generates a holistic roadmap covering all business and technical aspects

python -m arcane interactive \
    --model claude \
    --output-dir output \
    --idea-file idea.txt \
    --timeline "24-months" \
    --complexity complex \
    --focus feature \
    --team-size 15 \
    --roadmap-aspects business-strategy marketing-sales legal-compliance operations customer-support finance-accounting hr-team product-management qa-testing risk-management \
    --scope-control creative \
    --industry enterprise \
    --regulatory soc2 iso27001 gdpr \
    --market-maturity established \
    --target-market global \
    --technical-challenges realtime-data high-concurrency integrations microservices ml-ai multi-tenant \
    --team-expertise expert \
    --team-distribution hybrid \
    --dev-methodology agile \
    --budget-range funded \
    --deployment-environment kubernetes \
    --geographic-distribution multi-region \
    --scaling-expectations daily-peaks \
    --integrations payments notifications business-tools developer-tools external-apis \
    --success-metric revenue \
    --formats csv json yaml
    # --export-to linear  # Uncomment to export to: notion, jira, asana, linear, trello, github_projects, azure_devops, monday, clickup, file_only, skip
