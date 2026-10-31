# Architecture

    GitHub URL / local path
          |
    server/ingest.py        git log -> SQLite (commits, contributors, milestones); GitHub REST -> issues
          |
    SQLite (demo/commitmortem.db)  repo, contributor, commits, issue, milestone, story
          |
    harness/core.py         loads skills/*/SKILL.md, routes calls, step cap, trace log
          |
    skills -> modules       scan-repo -> ingest.py        ofrenda-builder -> ofrenda.py
                            seance -> seance.py           haunting-report -> haunting.py
                            calavera -> calavera.py       resurrect -> resurrect.py
          |
    server/app.py           stdlib HTTP API + static web/
          |
    web/index.html          ofrenda, seance chat, haunting report, resurrect view

Design choices
- Zero dependencies (Python standard library + git) so the demo runs anywhere with no install.
- Every generative step has a deterministic offline fallback, so the demo survives a network or API failure.
- Grounding: the seance only answers from retrieved commits/issues and every claim must cite `[commit:sha7]` or `[issue:#n]`; answers failing the check are regenerated once, then replaced by an extractive answer built from the retrieved items.
- Safety: ghost output is always labeled as an AI imitation; public data only; resurrect runs in a temp copy, with allow-listed commands and a step cap, and never pushes.
