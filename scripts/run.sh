#!/bin/bash

# Arcane CLI - Comprehensive Roadmap Generation
# This script includes ALL available project scope and planning flags

python -m arcane interactive \
    --idea-file idea.txt \
    --provider claude \
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
    --infra-budget unlimited \
    --services-budget enterprise \
    --deployment-environment kubernetes \
    --geographic-distribution global \
    --scaling-expectations viral \
    --payment-integrations stripe paypal square cryptocurrency bank-transfers \
    --communication-integrations email sms push-notifications in-app-chat video-calls \
    --business-integrations crm accounting analytics support marketing-automation \
    --developer-integrations github-gitlab ci-cd monitoring error-tracking feature-flags \
    --data-integrations rest-apis graphql-apis webhooks websockets file-uploads databases \
    --success-metric revenue \
    --success-timeline long \
    --measurement-approach quantitative \
    --failure-tolerance zero \
    --formats csv json yaml