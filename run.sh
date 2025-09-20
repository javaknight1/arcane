#!/bin/bash

python -m arcane interactive \
    --provider claude \
    --output-dir output \
    --idea-file idea.txt \
    --timeline 12-months \
    --focus mvp \
    --team-size 1 \
    --industry b2b-saas \
    --regulatory gdpr pci-dss soc2 iso27001 \
    --technical-challenges realtime-data complex-logic integrations ml-ai data-migrations microservices graphql-apis \
    --team-expertise learning \
    --team-distribution colocated \
    --dev-methodology agile \
    --budget-range undefined \
    --infra-budget moderate \
    --services-budget free \
    --deployment-environment kubernetes \
    --geographic-distribution single-region \
    --scaling-expectations steady \
    --payment-integrations none \
    --communication-integrations none \
    --business-integrations none \
    --developer-integrations github-gitlab ci-cd monitoring error-tracking feature-flags \
    --data-integrations rest-apis webhooks databases \
    --success-metric adoption \
    --success-timeline medium \
    --measurement-approach mixed \
    --failure-tolerance zero