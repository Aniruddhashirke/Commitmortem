---
name: scan-repo
description: Use when a repo URL or path is given. Reads history into SQLite and picks milestones.
---

## Inputs
Repo URL or local path.

## Steps
1. Clone or read the repo (server/ingest.py).
2. Extract commits, contributors, issues, README, dependency files.
3. Store in SQLite.
4. Pick milestone commits (keyword + change size + first/last); ask Gemma for summaries.

## Output
Repo JSON summary and database rows.

## Guardrails
- Public repos only
- Cap commits at a configurable limit (default 500)
- Respect API rate limits
