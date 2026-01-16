#!/bin/bash

# Arcane CLI - Simple Roadmap Generation
# This script includes a reasonable subset of flags for typical projects

python -m arcane interactive \
    --provider claude \
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
    --infra-budget moderate \
    --services-budget professional \
    --deployment-environment cloud \
    --geographic-distribution single-region \
    --scaling-expectations steady \
    --payment-integrations stripe \
    --communication-integrations email \
    --business-integrations analytics \
    --developer-integrations github-gitlab ci-cd monitoring \
    --data-integrations rest-apis databases \
    --success-metric adoption \
    --success-timeline medium \
    --measurement-approach mixed \
    --failure-tolerance low \
    --formats csv json