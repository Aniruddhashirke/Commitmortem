"""seance: retrieval-grounded ghost answers with mandatory citations + post-check."""
import re, math
from collections import Counter
from . import db, gemma
LABEL = "[AI imitation based on public commits]"
STOP = set("the a an of to in is was and or for with why what who how did do you your this that it on at be are".split())
def _stem(w): return re.sub(r"(ing|ed|es|s)$", "", w) if len(w) > 4 else w
def _tok(t): return [_stem(w) for w in re.findall(r"[a-z0-9_]+", t.lower()) if w not in STOP and len(w) > 2]
GENERIC = {"repo", "project", "code", "should", "thing", "about", "tell", "histori", "story", "happen", "everyth", "anyth", "repositori", "suggest", "recommend", "advic", "help", "start", "begin", "summar", "overview", "know"}
def overview(repo_id, k=5):
    c = db.connect()
    rows = c.execute("SELECT c.sha,c.message,c.date,u.name FROM milestone m JOIN commits c ON c.id=m.commit_id JOIN contributor u ON u.id=c.author_id WHERE m.repo_id=? ORDER BY c.date", (repo_id,)).fetchall(); c.close()
    return [("commit", r["sha"][:7], r["message"], r["date"], r["name"]) for r in rows[:k]]
def retrieve(repo_id, question, k=5):
    c = db.connect(); q = Counter(w for w in _tok(question) if w not in GENERIC)
    if not q: c.close(); return overview(repo_id, k)
    docs = [("commit", r["sha"][:7], r["message"], r["date"], r["name"]) for r in c.execute(
        "SELECT c.sha,c.message,c.date,u.name FROM commits c JOIN contributor u ON u.id=c.author_id WHERE c.repo_id=?", (repo_id,))]
    docs += [("issue", f"#{r['number']}", r["title"] + " " + (r["summary"] or ""), r["created"] or "", "") for r in c.execute("SELECT * FROM issue WHERE repo_id=?", (repo_id,))]
    df = Counter(w for d in docs for w in set(_tok(d[2]))); N = max(len(docs), 1)
    scored = []
    for d in docs:
        t = Counter(_tok(d[2])); s = sum((1 + math.log(t[w])) * math.log(1 + N / df[w]) for w in q if t[w])
        if s > 0: scored.append((s, d))
    scored.sort(key=lambda x: -x[0]); c.close()
    return [d for _, d in scored[:k]]
def valid_cites(text, ctx):
    ok = {f"[{k}:{i}]" for k, i, *_ in ctx}
    found = re.findall(r"\[(?:commit:[0-9a-f]{7}|issue:#\d+)\]", text)
    return bool(found) and all(f in ok for f in found)
def ask(repo_id, question):
    ctx = retrieve(repo_id, question)
    if not ctx:
        c = db.connect(); hints = [r["summary"] for r in c.execute("SELECT summary FROM commits WHERE repo_id=? ORDER BY files_changed DESC LIMIT 3", (repo_id,))]; c.close()
        return {"label": LABEL, "answer": "I do not remember that. The commits keep their silence. Ask me about something I wrote, for example: " + "; ".join(f"\"{h[:60]}\"" for h in hints if h), "citations": []}
    c = db.connect(); style = c.execute("SELECT style_notes FROM contributor WHERE repo_id=? ORDER BY commit_count DESC LIMIT 1", (repo_id,)).fetchone()
    c.close()
    numbered = "\n".join(f"[{k}:{i}] ({d}) {m.splitlines()[0] if m else ''}" for k, i, m, d, _ in ctx)
    prompt = (f"You are an AI imitation of an open-source maintainer, speaking from beyond the repo. Maintainer style: {style['style_notes'] if style else 'plain'}.\n"
              "Answer ONLY from the numbered context. Every claim must cite like [commit:abc1234] or [issue:#12]. "
              "Invent no personal facts. If unsure say you do not remember.\n\nCONTEXT:\n" + numbered + f"\n\nQUESTION: {question}")
    ans = None
    for _ in range(2):  # regenerate once if the citation post-check fails
        out = gemma.generate(prompt, fast=True)
        if out is None: break
        if valid_cites(out, ctx): ans = out; break
    if ans is None:  # offline / failed check: extractive answer built purely from retrieved commits
        line = lambda k, i, m, d: (f"Issue {i} was raised: \"{m[:90]}\" [{k}:{i}]." if k == "issue"
                                   else f"On {d[:10]} I wrote \"{(m.splitlines() or [''])[0]}\" [{k}:{i}].")
        ans = "Here is what the history remembers: " + " ".join(line(k, i, m, d) for k, i, m, d, _ in ctx[:3])
    return {"label": LABEL, "answer": ans, "citations": [{"ref": f"{k}:{i}", "date": d[:10], "text": ((m.splitlines() or [''])[0])[:100], "author": a} for k, i, m, d, a in ctx]}
