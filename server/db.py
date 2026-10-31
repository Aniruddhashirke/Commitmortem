import sqlite3, os
DB_PATH = os.environ.get("COMMITMORTEM_DB") or os.environ.get("OSSUARY_DB") or os.environ.get("REQUIEM_DB") or (os.path.join(os.path.dirname(__file__), "..", "demo", "commitmortem.db"))
SCHEMA = """
CREATE TABLE IF NOT EXISTS repo(id INTEGER PRIMARY KEY, url TEXT UNIQUE, name TEXT, scanned_at TEXT);
CREATE TABLE IF NOT EXISTS contributor(id INTEGER PRIMARY KEY, repo_id INT, name TEXT, handle TEXT,
  commit_count INT, first_commit TEXT, last_commit TEXT, style_notes TEXT);
CREATE TABLE IF NOT EXISTS commits(id INTEGER PRIMARY KEY, repo_id INT, sha TEXT, author_id INT, date TEXT,
  message TEXT, files_changed INT, summary TEXT);
CREATE TABLE IF NOT EXISTS issue(id INTEGER PRIMARY KEY, repo_id INT, number INT, title TEXT, state TEXT, summary TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS milestone(id INTEGER PRIMARY KEY, repo_id INT, commit_id INT, label TEXT, weight REAL);
CREATE TABLE IF NOT EXISTS story(id INTEGER PRIMARY KEY, repo_id INT, source TEXT, text TEXT);
"""
def connect():
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    try: c.execute("ALTER TABLE issue ADD COLUMN created TEXT")  # databases made by older versions
    except sqlite3.OperationalError: pass
    return c
