"""Skill harness: loads skills/*/SKILL.md, routes calls to server modules, enforces guardrails, records a trace.
This is the adapter point for TinyHarness: swap `Harness.run` internals for its skill loader / tool-call API."""
import os, json, time, re
from server import ingest, seance, haunting, calavera, ofrenda, resurrect, gemma
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TRACE = os.path.join(ROOT, "demo", "trace.jsonl")
MAX_STEPS = 12  # per run session
def _load_skills():
    skills = {}
    d = os.path.join(ROOT, "skills")
    for n in sorted(os.listdir(d)):
        p = os.path.join(d, n, "SKILL.md")
        if not os.path.isfile(p): continue
        txt = open(p).read(); m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n(.*)", txt, re.S)
        if m: skills[m.group(1).strip()] = {"name": m.group(1).strip(), "description": m.group(2).strip(), "body": m.group(3).strip()}
    return skills
class Harness:
    def __init__(self):
        self.skills = _load_skills(); self.steps = 0; self.sources = {}
        self.handlers = {
            "scan-repo": lambda a: self._scan(a),
            "ofrenda-builder": lambda a: ofrenda.build(a["repo"]),
            "seance": lambda a: seance.ask(a["repo"], a["question"]),
            "haunting-report": lambda a: haunting.report(self._path(a["repo"])),
            "calavera": lambda a: {"epitaph": calavera.epitaph(a["repo"])},
            "resurrect": lambda a: resurrect.resurrect(self._path(a["repo"]), a.get("command")),
        }
    def _scan(self, a):
        r = ingest.scan(a["source"], a.get("limit", 500)); self.sources[r["repo_id"]] = r["path"]; return r
    def _path(self, rid):
        if rid not in self.sources: raise KeyError(f"repo {rid} has no known local path; run scan-repo first")
        return self.sources[rid]
    def list(self): return [{"name": s["name"], "description": s["description"], "implemented": s["name"] in self.handlers} for s in self.skills.values()]
    def run(self, skill, **args):
        if skill not in self.skills: raise KeyError(f"unknown skill: {skill}")
        if skill not in self.handlers: raise NotImplementedError(f"skill '{skill}' is specified but not implemented yet")
        self.steps += 1
        if self.steps > MAX_STEPS: raise RuntimeError("step cap reached")
        t0 = time.time(); ok = True
        try: return self.handlers[skill](args)
        except Exception: ok = False; raise
        finally:
            os.makedirs(os.path.dirname(TRACE), exist_ok=True)
            with open(TRACE, "a") as f:
                f.write(json.dumps({"ts": time.time(), "skill": skill, "args": {k: v for k, v in args.items() if k != "question"} | ({"question": args["question"][:80]} if "question" in args else {}),
                                    "ok": ok, "ms": round((time.time() - t0) * 1000), "gemma": gemma.available()}) + "\n")
