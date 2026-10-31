# Harness

`core.py` loads `../skills/*/SKILL.md`, routes each skill to its module in `../server/`, caps steps per session (12), and appends a trace line per call to `demo/trace.jsonl`. The API server routes every request through it.

CLI:

    python3 -m harness.run list
    python3 -m harness.run scan-repo source=demo/sample-dead-repo
    python3 -m harness.run seance repo=1 question="why does merge drop lists?"

(State such as repo paths lives in one process, so scan and follow-up calls belong in the same run, as the API server does.)

## TinyHarness
`Harness.run` is the single adapter point. This layer was written without access to TinyHarness's source, so replace the loader and dispatch in `core.py` with TinyHarness's skill and tool-call API; the skills and handlers stay unchanged.
