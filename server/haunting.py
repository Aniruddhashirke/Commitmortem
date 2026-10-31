"""haunting-report: code smells phrased as hauntings, always tied to a real file/line."""
import os, re, json, subprocess, time
from . import gemma
SKIP = {".git", "node_modules", "__pycache__", ".venv"}
OLD_PY = {r"collections\.(Mapping|MutableMapping|Iterable|Sequence|Callable|Set)\b": "removed in Python 3.10; use collections.abc", r"^\s*import imp\b": "module `imp` removed in 3.12; use importlib"}
def report(path):
    out = []
    for root, ds, fs in os.walk(path):
        ds[:] = [d for d in ds if d not in SKIP]
        for f in fs:
            p = os.path.join(root, f); rel = os.path.relpath(p, path).replace(os.sep, "/")
            try: lines = open(p, encoding="utf-8").read().splitlines()
            except Exception: continue
            if len(lines) > 400: out.append({"file": rel, "line": 1, "kind": "giant file", "severity": "medium", "note": f"{len(lines)} lines in one file", "fix": "split into modules"})
            if time.time() - os.path.getmtime(p) > 3 * 365 * 86400: out.append({"file": rel, "line": 1, "kind": "stale file", "severity": "low", "note": "untouched for 3+ years", "fix": "verify it still builds"})
            in_doc = False
            for n, ln in enumerate(lines, 1):
                cnt = ln.count('"""') + ln.count("'''"); was = in_doc
                if cnt % 2: in_doc = not in_doc
                skip_code = was or cnt > 0 or ln.strip().startswith("#") or not f.endswith(".py")
                if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", ln): out.append({"file": rel, "line": n, "kind": "unfinished business", "severity": "low", "note": ln.strip()[:100], "fix": "finish or delete the task"})
                for pat, why in OLD_PY.items():
                    if not skip_code and re.search(pat, ln): out.append({"file": rel, "line": n, "kind": "deprecated API", "severity": "high", "note": ln.strip()[:100] + " - " + why, "fix": why})
            if f == "package.json":
                try:
                    deps = json.load(open(p)).get("dependencies", {})
                    for k, v in deps.items():
                        if re.match(r"^[~^]?0\.", v): out.append({"file": rel, "line": 1, "kind": "pre-1.0 dependency", "severity": "medium", "note": f"{k}@{v}", "fix": "check for a maintained release"})
                except Exception: pass
    flavour = {"deprecated API": "A curse from an older runtime", "unfinished business": "A restless promise never kept",
               "giant file": "A sprawling mansion with no exits", "stale file": "Dust, undisturbed", "pre-1.0 dependency": "A borrowed ghost that never grew up"}
    for h in out: h["haunting"] = flavour.get(h["kind"], "Something stirs") + f" in {h['file']}:{h['line']}"
    return sorted(out, key=lambda h: {"high": 0, "medium": 1, "low": 2}[h["severity"]])
