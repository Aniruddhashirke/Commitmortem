"""scan-repo: read a local git repo (or clone a public URL) into SQLite."""
import os, re, subprocess, tempfile, datetime, json, urllib.request
from collections import Counter
from . import db, gemma
SEP = "\x1e"; FS = "\x1f"
def _git(path, *args):
    return subprocess.run(["git", "-C", path, *args], capture_output=True, text=True, check=True).stdout
def _checkout(src):
    if os.path.isdir(src): return os.path.abspath(src)
    if not re.match(r"^https://github\.com/[\w.-]+/[\w.-]+/?$", src): raise ValueError("public GitHub URL or local path only")
    dest = tempfile.mkdtemp(prefix="commitmortem-")
    subprocess.run(["git", "clone", "--quiet", src, dest], check=True, timeout=120); return dest
def _gh_slug(src):
    m = re.match(r"^https://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", src); return m.groups() if m else None
def _http_json(url):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "commitmortem"}
    if os.environ.get("GITHUB_TOKEN"): h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=20))
def fetch_issues(owner, repo, pages=3):
    """Public issues only (pull requests filtered out). Failures such as rate limits skip issues, never the scan."""
    out = []
    for p in range(1, pages + 1):
        try: batch = _http_json(f"https://api.github.com/repos/{owner}/{repo}/issues?state=all&per_page=100&page={p}")
        except Exception as e: print("[issues] skipped:", e); break
        out += [i for i in batch if "pull_request" not in i]
        if len(batch) < 100: break
    return out
def _style(msgs):
    if not msgs: return ""
    n = len(msgs); avg = sum(len(m) for m in msgs) / n
    lower = sum(m[:1].islower() for m in msgs) / n
    words = Counter(w for m in msgs for w in re.findall(r"[a-z']{4,}", m.lower()))
    common = ", ".join(w for w, _ in words.most_common(4))
    return f"avg {avg:.0f} chars; {'lowercase' if lower > .6 else 'Capitalised'} openers; favourite words: {common}"
MILE_RE = re.compile(r"\b(init|first|release|v?\d+\.\d+|launch|rewrite|major|initial|finally|1\.0)\b", re.I)
def scan(src, limit=500):
    path = _checkout(src); name = os.path.basename(path.rstrip("/")) if os.path.isdir(src) else src.rstrip("/").split("/")[-1]
    out = _git(path, "log", f"-n{limit}", "--reverse", f"--pretty=format:{SEP}%H{FS}%an{FS}%ae{FS}%aI{FS}%B{FS}", "--name-only")
    c = db.connect(); cur = c.cursor()
    cur.execute("DELETE FROM repo WHERE url=?", (src,))
    cur.execute("INSERT INTO repo(url,name,scanned_at) VALUES(?,?,?)", (src, name, datetime.datetime.utcnow().isoformat()))
    rid = cur.lastrowid; authors = {}; rows = []
    for t in ("commits", "contributor", "milestone", "issue", "story"):  # SQLite reuses ids, so clear anything left from an earlier scan
        cur.execute(f"DELETE FROM {t} WHERE repo_id=? OR repo_id NOT IN (SELECT id FROM repo)", (rid,))
    for chunk in out.split(SEP)[1:]:
        sha, an, ae, date, body, files = (chunk.split(FS, 5) + [""])[:6] if chunk.count(FS) >= 5 else (chunk.split(FS) + [""] * 6)[:6]
        msg = body.strip(); nfiles = len([f for f in files.strip().splitlines() if f.strip()])
        a = authors.setdefault(an, {"handle": ae.split("@")[0], "dates": [], "msgs": []})
        a["dates"].append(date); a["msgs"].append(msg.splitlines()[0] if msg else "")
        rows.append((sha, an, date, msg, nfiles))
    ids = {}
    for an, a in authors.items():
        cur.execute("INSERT INTO contributor(repo_id,name,handle,commit_count,first_commit,last_commit,style_notes) VALUES(?,?,?,?,?,?,?)",
                    (rid, an, a["handle"], len(a["dates"]), min(a["dates"]), max(a["dates"]), _style(a["msgs"])))
        ids[an] = cur.lastrowid
    cids = []
    for sha, an, date, msg, nfiles in rows:
        cur.execute("INSERT INTO commits(repo_id,sha,author_id,date,message,files_changed,summary) VALUES(?,?,?,?,?,?,?)",
                    (rid, sha, ids[an], date, msg, nfiles, (msg.splitlines() or [""])[0]))
        cids.append((cur.lastrowid, msg, nfiles))
    # milestone detection: keyword hits + biggest changes + first/last commit
    scored = [(cid, (3 if MILE_RE.search(m.splitlines()[0] if m else "") else 0) + min(nf, 10) / 5 + (3 if i in (0, len(cids) - 1) else 0), m)
              for i, (cid, m, nf) in enumerate(cids)]
    for cid, s, m in sorted(scored, key=lambda x: -x[1])[:8]:
        cur.execute("INSERT INTO milestone(repo_id,commit_id,label,weight) VALUES(?,?,?,?)", (rid, cid, (m.splitlines() or [""])[0][:80], s))
    slug = _gh_slug(src); issues = fetch_issues(*slug) if slug else []
    for i in issues:
        cur.execute("INSERT INTO issue(repo_id,number,title,state,summary,created) VALUES(?,?,?,?,?,?)",
                    (rid, i["number"], i["title"], i["state"], re.sub(r"\s+", " ", i.get("body") or "")[:300], i.get("created_at", "")))
    c.commit(); c.close()
    return {"repo_id": rid, "name": name, "commits": len(rows), "contributors": len(authors), "issues": len(issues), "path": path}
