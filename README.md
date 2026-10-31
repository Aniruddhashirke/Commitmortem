# Commitmortem

**A post-mortem for abandoned code.** Commitmortem turns a dead public repository into a digital *ofrenda*, lets you question an AI imitation of its maintainer, and then tries to bring the project back to life in a sandbox.

Built for the **Ghost in the Machine** challenge with **Gemma 4** and an open skill harness.

> Ghost output is always labeled: **AI imitation based on public commits.**

![Commitmortem start screen](docs/screenshots/01-start.png)

## What it does

| Process | What you get |
| --- | --- |
| **I. Ofrenda** | A memorial page: calavera epitaph, a candle per milestone commit, a portrait frame per contributor with marigolds sized by activity, and open issues as "unanswered prayers" |
| **II. Séance** | Ask the ghost a question. Every answer cites real commits or issues (`[commit:abc1234]`, `[issue:#7]`). If nothing matches, it says it does not remember |
| **III. Haunting report** | Technical debt phrased as hauntings, each with a severity, a real file and line, and a suggested fix |
| **IV. Resurrect** | An agent copies the repo into a sandbox, runs its checks, tries up to 3 small fixes, and shows the steps, logs and diff. It never pushes anything |

![Ofrenda](docs/screenshots/02-ofrenda.png)
![Séance](docs/screenshots/03-seance.png)

## Architecture at a glance

```
URL/path ..> ingest ..> SQLite ..> harness ..> skills ..> Gemma 4 (or offline fallback) ..> API ..> web UI
```

Detailed view:

```
   GitHub URL / local path
              :
              :  git log + GitHub REST (issues)
              v
   +--------------------+            +-------------------------+
   |   server/ingest    | . . . . .> |  SQLite                 |
   +--------------------+            |  commits, contributors, |
                                     |  issues, milestones     |
                                     +------------+------------+
                                                  :
                                                  v
   +-------------------------------------------------------------+
   |  harness/core  - loads skills/*/SKILL.md, routes each call, |
   |                  caps steps, writes a trace                 |
   +----+------------+------------+------------+-------------+---+
        :            :            :            :             :
        v            v            v            v             v
    scan-repo     ofrenda-      seance      haunting-     resurrect
                  builder      (cited)       report       (sandbox)
        :            :            :            :             :
        . . . . . . . . . . . . . + . . . . . . . . . . . . .
                                  :
                                  :  generation: Gemma 4 via the Gemini API
                                  :  if no key or no network: offline fallbacks
                                  v
   +-------------------------------------------------------------+
   |  server/app  - stdlib HTTP API  . . . . . . . . . .> web/   |
   +-------------------------------------------------------------+
```

## Quick start

Requires **Python 3.10+** and **git**. No packages to install.

```bash
# 1. Create a small sample dead repo (use `python` instead of `python3` on Windows)
python3 demo/make_fixture.py

# 2. Start the server and preload the sample
python3 -m server.app demo/sample-dead-repo

# 3. Open http://localhost:8000
```

Or scan any public repo from the UI by pasting `https://github.com/owner/repo`.

### Use Gemma 4

```bash
cp .env.example .env          # then add your key
export GEMINI_API_KEY=...     # Windows PowerShell: $env:GEMINI_API_KEY="..."
```

Without a key the app runs in **offline mode**: cited extractive séance answers, a template epitaph, and a rule-based Python fix. That keeps the demo working with no network.

## Configuration

| Variable | Purpose |
| --- | --- |
| `GEMINI_API_KEY` | Enables Gemma 4 through the Gemini API |
| `GEMMA_REASONING_MODEL` | Model for harder tasks (default `gemma-4-31b-it`) |
| `GEMMA_FAST_MODEL` | Model for fast tasks (default `gemma-4-26b-a4b-it`) |
| `OLLAMA_URL` | Optional local model path |
| `GITHUB_TOKEN` | Optional, raises the GitHub rate limit for issue ingest |
| `PORT` | Server port (default `8000`) |
| `COMMITMORTEM_DB` | Path of the SQLite file (default `demo/commitmortem.db`) |

## How Gemma 4 is used

| Task | Module | Fallback without a key |
| --- | --- | --- |
| Séance answers with citations | `server/seance.py` | Answer built from retrieved commits and issues |
| Contributor remembrance | `server/ofrenda.py` | Factual sentence from the data |
| Calavera epitaph | `server/calavera.py` | Template verse from repo facts |
| Resurrection fix proposal | `server/resurrect.py` | Python `collections` fix only |

More detail in [`docs/GEMMA_USAGE.md`](docs/GEMMA_USAGE.md).

## Skills and harness

Each process is an agent skill: a folder under `skills/` with a `SKILL.md` (when to use, inputs, steps, output, guardrails). `harness/core.py` loads them, routes each call to its module, caps a session at 12 steps and logs a trace to `demo/trace.jsonl`.

```bash
python3 -m harness.run list
```

Skills: `scan-repo`, `ofrenda-builder`, `seance`, `haunting-report`, `calavera`, `resurrect`, and `oral-history` (specified, not built yet).

## API

| Route | Body / query | Returns |
| --- | --- | --- |
| `POST /api/scan` | `{source}` | repo id, commit, contributor and issue counts |
| `GET /api/ofrenda?repo=` | repo id | frames, candles, epitaph, issues |
| `POST /api/seance` | `{repo, question}` | label, answer, citations |
| `GET /api/report?repo=` | repo id | list of hauntings |
| `POST /api/resurrect` | `{repo}` | ok flag, report, steps, diff |
| `GET /api/skills` | none | skill list |
| `GET /api/repos` | none | scanned repos |

## Safety and ethics

- Ghost output is always labeled as an AI imitation.
- Answers must cite retrieved commits or issues. A post-check regenerates an answer with no valid citation once, then falls back to a plain answer built from the retrieved items. If nothing matches, the ghost says it does not remember.
- Public repositories only. Contributors are honored, never mocked, and no biography is invented.
- Resurrection works on a temporary copy, runs allow-listed commands only (`python -m unittest`, `npm test`, `rake test` and similar), has a step cap, and never pushes or publishes.

## Project structure

```
commitmortem/
  README.md  LICENSE  .env.example
  server/      app.py ingest.py seance.py haunting.py calavera.py ofrenda.py resurrect.py gemma.py db.py
  harness/     core.py run.py
  skills/      scan-repo/ ofrenda-builder/ seance/ haunting-report/ calavera/ resurrect/ oral-history/
  web/         index.html
  demo/        make_fixture.py DEMO_SCRIPT.md
  docs/        ARCHITECTURE.md GEMMA_USAGE.md
```

## Known limits

- Offline automatic fixes cover Python only; other languages need Gemma to propose a patch.
- Resurrection checks that a project's tests pass, or that the package imports when there are no tests. It does not prove the project is healthy.
- The `oral-history` skill (a Gemma-led interview that saves a maintainer's own story) is not built yet.
- Repo paths are kept in server memory, so rescan after restarting the server.

## License

MIT, see [`LICENSE`](LICENSE).
