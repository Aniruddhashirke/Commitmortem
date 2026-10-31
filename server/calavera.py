"""calavera: kind, humorous epitaph that teases the project, never its people."""
from . import db, gemma
def epitaph(repo_id):
    c = db.connect(); r = c.execute("SELECT name FROM repo WHERE id=?", (repo_id,)).fetchone()
    n = c.execute("SELECT COUNT(*) n, MIN(date) a, MAX(date) b FROM commits WHERE repo_id=?", (repo_id,)).fetchone()
    k = c.execute("SELECT COUNT(*) n FROM contributor WHERE repo_id=?", (repo_id,)).fetchone()["n"]; c.close()
    name = r["name"]; a, b = (n["a"] or "")[:4], (n["b"] or "")[:4]
    out = gemma.generate(f"Write a 4-8 line humorous calavera verse (Dia de los Muertos tradition) for the abandoned project '{name}' "
                         f"with {n['n']} commits between {a} and {b}. Tease the project gently, never its people. No real tragedies.", fast=True)
    return out or (f"Here lies {name}, {n['n']} commits deep,\nIts last one in {b}, then eternal sleep.\n"
                   f"{k} {'soul' if k == 1 else 'souls'} left their mark, then wandered away,\nBut marigolds guide it past the build's iron gate.\n"
                   f"So fork it, dear stranger, and light it a flame,\nFor code that is read never dies in vain.")
