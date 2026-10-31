---
name: resurrect
description: Use when the user clicks Resurrect.
---

## Inputs
Repo path, optional allow-listed build/test command.

## Steps
1. Copy repo to a sandbox directory.
2. Run the build or tests.
3. Gemma (or offline rule) proposes the smallest fix as JSON.
4. Apply and re-run, at most 3 loops.

## Output
Unified diff, step log, resurrection report.

## Guardrails
- Sandbox only
- Allow-listed commands
- Step cap
- Never push or publish
