#!/bin/bash

# Arcane CLI - Comprehensive Business + Technical Roadmap
# This script generates a holistic roadmap covering all business and technical aspects

python -m arcane interactive \
    --provider claude \
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
    --infra-budget substantial \
    --services-budget professional \
    --deployment-environment kubernetes \
    --geographic-distribution multi-region \
    --scaling-expectations daily-peaks \
    --payment-integrations stripe paypal bank-transfers \
    --communication-integrations email sms push-notifications in-app-chat \
    --business-integrations crm accounting analytics support \
    --developer-integrations github-gitlab ci-cd monitoring error-tracking feature-flags \
    --data-integrations rest-apis graphql-apis webhooks websockets databases \
    --success-metric revenue \
    --success-timeline long \
    --measurement-approach quantitative \
    --failure-tolerance low \
    --formats csv json yaml