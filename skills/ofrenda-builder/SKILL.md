---
name: ofrenda-builder
description: Use when a scanned repo needs its remembrance page.
---

## Inputs
Contributors, milestones, activity data.

## Steps
1. Frame per contributor, candle per milestone, marigold count by commit share.
2. Gemma writes a short remembrance per contributor from real commit facts (server/ofrenda.py).

## Output
ofrenda JSON for the web app.

## Guardrails
- Only facts present in the data
- No invented biography
