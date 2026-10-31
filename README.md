# Commitmortem

Turn an abandoned open-source repo into a digital ofrenda, talk to the ghost of its maintainer, read its hauntings, and try to bring it back to life.
Built for the Ghost in the Machine challenge on Gemma 4 and an open agent harness (TinyHarness).

> Ghost output is always labeled: **AI imitation based on public commits.**

## Run (no dependencies, no API key needed)

    python3 demo/make_fixture.py          # builds a sample dead repo
    python3 -m server.app demo/sample-dead-repo
    # open http://localhost:8000

Python 3.10+ and git only. See `docs/` for architecture and Gemma usage, and `demo/DEMO_SCRIPT.md`. Without a key the app runs in offline mode (extractive cited answers, template epitaph, rule-based fix). With a key, Gemma 4 does all generation:

    export GEMINI_API_KEY=...             # see .env.example for model names

## What works today
GitHub issue ingest (open issues become cite-able `[issue:#n]` and show on the ofrenda as unanswered prayers), a skill harness (`harness/`, loads the SKILL.md files, step cap, trace log), scan-repo (git log into SQLite, milestones), ofrenda page, séance with citation post-check, haunting report, calavera, resurrect (sandboxed, 3-step cap; detects npm, Ruby/rake or Python projects and says plainly when it cannot run or fix one; offline fixes cover Python only, other languages need Gemma).

## Not done yet
TinyHarness itself (adapter point is `harness/core.py`), oral-history/voice, React+Vite port, DigitalOcean deploy, demo video.

License: MIT
