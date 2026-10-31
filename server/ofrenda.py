"""ofrenda-builder: map real data to a frame per contributor, candle per milestone, marigold density by activity."""
from . import db, gemma
def build(repo_id):
    c = db.connect(); repo = c.execute("SELECT * FROM repo WHERE id=?", (repo_id,)).fetchone()
    cons = [dict(r) for r in c.execute("SELECT * FROM contributor WHERE repo_id=? ORDER BY commit_count DESC", (repo_id,))]
    total = sum(x["commit_count"] for x in cons) or 1
    for x in cons:
        x["marigolds"] = max(3, round(40 * x["commit_count"] / total))
        facts = f"{x['name']} made {x['commit_count']} commits between {x['first_commit'][:10]} and {x['last_commit'][:10]}."
        txt = gemma.generate("Write a warm 2 sentence remembrance using ONLY these facts, inventing nothing: " + facts, fast=True)
        x["remembrance"] = txt or facts + " Their work is remembered here."
    candles = [dict(r) for r in c.execute("SELECT m.label,m.weight,c.sha,c.date FROM milestone m JOIN commits c ON c.id=m.commit_id WHERE m.repo_id=? ORDER BY c.date", (repo_id,))]
    n = c.execute("SELECT COUNT(*) n FROM commits WHERE repo_id=?", (repo_id,)).fetchone()["n"]
    iss = [dict(r) for r in c.execute("SELECT number,title,state FROM issue WHERE repo_id=? ORDER BY number DESC", (repo_id,))]; c.close()
    open_ = [i for i in iss if i["state"] == "open"]
    return {"repo": dict(repo), "commit_count": n, "frames": cons, "candles": candles,
            "issues": {"open": len(open_), "closed": len(iss) - len(open_), "unanswered": open_[:5]}}
