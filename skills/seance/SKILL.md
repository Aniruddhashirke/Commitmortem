---
name: seance
description: Use when the user asks the ghost a question.
---

## Inputs
Question, repo index, maintainer style profile.

## Steps
1. Retrieve top-k commits/issues (TF-IDF).
2. Build numbered context.
3. Gemma answers in the maintainer's style citing [commit:sha7] or [issue:#n].
4. Post-check: regenerate once, else fall back to an extractive cited answer.

## Output
Answer text plus citation list.

## Guardrails
- Always show the AI-imitation label
- Say 'I do not remember' when nothing is retrieved
- Public data only
