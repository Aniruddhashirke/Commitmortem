# Gemma 4 usage

Models (configurable in `.env`): `gemma-4-31b-it` for reasoning, `gemma-4-26b-a4b-it` for fast tasks, through the Gemini API (`server/gemma.py`). An Ollama path exists as an option.

| Task | Module | Model tier | Why Gemma | Offline fallback |
| --- | --- | --- | --- | --- |
| Seance answers (cited, in maintainer style) | seance.py | fast | grounded generation over retrieved commits/issues | extractive answer from retrieved items |
| Remembrance text per contributor | ofrenda.py | fast | warm prose from real facts only | factual sentence from the data |
| Calavera epitaph | calavera.py | fast | creative, culturally aware verse | template verse from repo facts |
| Resurrection fix proposal | resurrect.py | reasoning | reads the build log + sources, proposes the smallest patch as JSON | rule: Python `collections` ABC fix |

Planned, not built yet: commit/diff summarization, LLM milestone selection (currently heuristic), maintainer style profile (currently statistics), haunting-report severity classification (currently rules).

## Status (be honest in the submission)
- Verified end to end: the offline paths (scan, ofrenda, seance with citation post-check, haunting report, resurrect on a Python sample and import-check fallback, issue ingest with a mocked GitHub response).
- NOT yet verified: any call to Gemma 4. Before submitting, run with `GEMINI_API_KEY`, record real séance transcripts and a real resurrect log here, and confirm the model names.

## Results to fill in after the Gemma run
- Citation pass rate on the first try (target: most answers) and how often the regenerate step triggers.
- Séance latency (target under 8 s).
- One captured séance transcript and one resurrection report.
