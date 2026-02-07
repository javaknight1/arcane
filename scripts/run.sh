#!/bin/bash

# Arcane CLI - Comprehensive Roadmap Generation
# This script includes ALL available project scope and planning flags

python -m arcane interactive \
    --idea-file idea.txt \
    --model claude \
    --output-dir output \
    --timeline "10 years" \
    --complexity complex \
    --focus mvp \
    --team-size 30 \
    --scope-control expansive \
    --industry b2b-saas \
    --regulatory gdpr pci-dss soc2 iso27001 \
    --market-maturity emerging \
    --target-market global \
    --technical-challenges realtime-data complex-logic integrations ml-ai data-migrations microservices graphql-apis blockchain iot-hardware multi-tenant offline-first \
    --team-expertise expert \
    --team-distribution colocated \
    --dev-methodology agile \
    --budget-range enterprise \
    --deployment-environment kubernetes \
    --geographic-distribution global \
    --scaling-expectations viral \
    --integrations payments notifications business-tools developer-tools external-apis \
    --success-metric revenue \
    --formats csv json yaml
    # --export-to linear  # Uncomment to export to: notion, jira, asana, linear, trello, github_projects, azure_devops, monday, clickup, file_only, skip
