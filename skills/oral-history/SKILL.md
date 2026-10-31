---
name: oral-history
description: Optional. Use when the user wants to add their own story to a project (not implemented in v0).
---

## Inputs
Typed answers or a voice recording.

## Steps
1. Gemma asks 5-7 interview questions.
2. Optionally transcribe audio with Whisper.
3. Save as story rows and merge into the ofrenda.

## Output
Story entries and an updated ofrenda.

## Guardrails
- Consent reminder before saving
- Local storage by default
