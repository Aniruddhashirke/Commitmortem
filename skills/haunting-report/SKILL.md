---
name: haunting-report
description: Use when the user opens the report tab.
---

## Inputs
Source path of the repo.

## Steps
1. Collect signals: TODO/FIXME, deprecated APIs, giant or stale files, pre-1.0 deps (server/haunting.py).
2. Phrase each as a haunting with severity and a plain technical note.

## Output
List of hauntings with file, line, reason, suggested exorcism.

## Guardrails
- Every item references a real file and line
