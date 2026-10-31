"""resurrect: sandboxed build-fix loop (max 3 fixes). Never pushes anything."""
import os, shutil, subprocess, sys, tempfile, json, difflib, re
from . import gemma
ALLOW = {"python -m unittest", "python -m pytest", "npm test", "npm run build", "rake test", "bundle exec rake"}
EXT = (".py", ".rb", ".js", ".json", ".gemspec", "Rakefile", "Gemfile")
ABC = "Mapping|MutableMapping|Sequence|MutableSequence|Set|MutableSet|Iterable|Iterator|Callable|Hashable|Sized|Container|KeysView|ItemsView|ValuesView"
def _argv(cmd):
    a = cmd.split(); return [sys.executable] + a[1:] if a[0] == "python" else a
def detect(path):
    """Returns (command, reason). command is None when no known build system is found."""
    has = lambda *n: any(os.path.exists(os.path.join(path, x)) for x in n)
    if has("package.json"): return "npm test", "package.json found"
    if has("Rakefile", "Gemfile") or any(f.endswith(".gemspec") for f in os.listdir(path)): return "rake test", "Ruby project (Rakefile/Gemfile/gemspec)"
    if has("setup.py", "requirements.txt", "pyproject.toml") or any(f.endswith(".py") for f in os.listdir(path)) or _import_targets(path): return "python -m unittest", "Python project"
    return None, "no known build system (looked for package.json, Rakefile/Gemfile, Python files)"
def _run(argv, cwd):
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=120); return p.returncode, (p.stdout + p.stderr)[-3000:]
def _read(sb, exts=(".py",)):
    out = {}
    for r, ds, fs in os.walk(sb):
        ds[:] = [d for d in ds if d != ".git"]
        for f in fs:
            if f.endswith(exts):
                try: t = open(os.path.join(r, f), encoding="utf-8", newline="").read()
                except Exception: continue
                if len(t) < 60000: out[os.path.relpath(os.path.join(r, f), sb).replace(os.sep, "/")] = t
    return out
def _import_targets(sb):
    """Top-level packages (dirs with __init__.py) or modules to import when a repo has no test suite."""
    pk = sorted(d for d in os.listdir(sb) if os.path.isfile(os.path.join(sb, d, "__init__.py")) and not d.startswith(("test", ".")))
    if pk: return pk
    return sorted(f[:-3] for f in os.listdir(sb) if f.endswith(".py") and f not in ("setup.py", "conftest.py") and not f.startswith("test") and f[:-3].isidentifier())
def fix_collections(src):
    """Python 3.10 removed the ABC aliases from `collections`. Rewrites code lines only (never docstrings or comments)."""
    out, in_doc = [], False
    for line in src.splitlines(keepends=True):
        n = line.count('"""') + line.count("'''"); was = in_doc
        if n % 2: in_doc = not in_doc
        if was or n or line.strip().startswith("#"): out.append(line); continue
        body = line.rstrip("\r\n"); eol = line[len(body):]
        m = re.fullmatch(rf"(\s*)from collections import ((?:{ABC})(?:\s*,\s*(?:{ABC}))*)\s*", body)
        if m: body = f"{m.group(1)}from collections.abc import {m.group(2)}"
        body = re.sub(rf"\bcollections\.({ABC})\b", r"collections.abc.\1", body)
        out.append(body + eol)
    new = "".join(out)
    if "collections.abc." in new and not re.search(r"^\s*import collections\.abc", new, re.M):
        new = re.sub(r"^import collections[ \t]*(?=\r?$)", "import collections\nimport collections.abc", new, count=1, flags=re.M)
    return new
def _propose(log, files):
    out = gemma.generate("Build failed. Propose the SMALLEST fix as JSON {\"file\":..,\"old\":..,\"new\":..} (exact substring). Only JSON.\n"
                         f"LOG:\n{log}\nFILES:\n" + "\n".join(f"--- {k}\n{v}" for k, v in files.items()))
    if out:
        try: return json.loads(re.sub(r"```(json)?", "", out).strip())
        except Exception: pass
    for f, src in files.items():  # offline rule, Python only
        if f.endswith(".py"):
            new = fix_collections(src)
            if new != src: return {"file": f, "old": src, "new": new}
    return None
def resurrect(src, cmd=None):
    sb = tempfile.mkdtemp(prefix="commitmortem-sandbox-"); shutil.rmtree(sb); shutil.copytree(src, sb, ignore=shutil.ignore_patterns(".git"))
    before = _read(sb, EXT); reason = "command given"
    if not cmd: cmd, reason = detect(sb)
    base = {"sandbox": sb, "diff": "", "steps": [], "detected": cmd, "reason": reason}
    if cmd is None: return {**base, "ok": False, "report": "Cannot resurrect: " + reason + "."}
    if cmd not in ALLOW: return {**base, "ok": False, "report": f"Command not allow-listed: {cmd}"}
    if shutil.which(_argv(cmd)[0]) is None: return {**base, "ok": False, "report": f"Cannot run '{cmd}': '{_argv(cmd)[0]}' is not installed on this machine."}
    steps, mode, argv, label, fixes = [], "tests", _argv(cmd), cmd, 0
    for _ in range(6):
        rc, log = _run(argv, sb); steps.append({"step": len(steps), "command": label, "exit": rc, "log": log[-600:]})
        if rc == 0: break
        if mode == "tests" and cmd == "python -m unittest" and (rc == 5 or "NO TESTS RAN" in log):
            names = _import_targets(sb)
            if names:  # no test suite: the check becomes "does the package import?"
                mode, label = "import", "import " + ", ".join(names); argv = [sys.executable, "-c", "import " + ", ".join(names)]
                steps.append({"step": len(steps), "note": "No tests found, so verifying by importing: " + ", ".join(names)}); continue
        if fixes >= 3: break
        fix = _propose(log, _read(sb, EXT))
        if not fix: steps.append({"step": len(steps), "note": "no fix proposed"}); break
        p = os.path.join(sb, fix["file"])
        try: s = open(p, encoding="utf-8", newline="").read()
        except Exception: break
        if fix["old"] not in s: break
        open(p, "w", encoding="utf-8", newline="").write(s.replace(fix["old"], fix["new"], 1)); fixes += 1
        steps.append({"step": len(steps), "applied": {"file": fix["file"]}})
    after = _read(sb, EXT)
    diff = "".join(l for k in after for l in difflib.unified_diff(before.get(k, "").splitlines(1), after[k].splitlines(1), f"a/{k}", f"b/{k}"))
    ok = bool(steps) and steps[-1].get("exit") == 0
    if ok: report = "Resurrected: build passes after the patch." if mode == "tests" else "Resurrected: the package imports cleanly after the patch. No test suite was found, so importing is the only check."
    else:
        report = f"Attempted with `{label}`: could not revive within the step cap. The failing output is in the step log."
        if not any(k.endswith(".py") for k in after): report += " Offline fixes cover Python only; other languages need Gemma (set GEMINI_API_KEY)."
    return {**base, "ok": ok, "diff": diff, "steps": steps, "report": report}
