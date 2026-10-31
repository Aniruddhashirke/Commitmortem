"""Zero-dependency API + static server: python3 -m server.app"""
import json, os, sys, mimetypes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from . import db
from harness.core import Harness
WEB = os.path.join(os.path.dirname(__file__), "..", "web")
HX = Harness()  # all skill calls go through the harness
class H(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/api/repos":
                c = db.connect(); r = [dict(x) for x in c.execute("SELECT * FROM repo")]; c.close(); return self._json(r)
            if u.path == "/api/ofrenda": rid = int(q["repo"]); o = HX.run("ofrenda-builder", repo=rid); o["epitaph"] = HX.run("calavera", repo=rid)["epitaph"]; return self._json(o)
            if u.path == "/api/report": return self._json(HX.run("haunting-report", repo=int(q["repo"])))
            if u.path == "/api/skills": return self._json(HX.list())
            path = os.path.join(WEB, "index.html" if u.path == "/" else u.path.lstrip("/"))
            if os.path.isfile(path):
                b = open(path, "rb").read(); self.send_response(200); self.send_header("Content-Type", mimetypes.guess_type(path)[0] or "text/plain"); self.end_headers(); return self.wfile.write(b)
            self._json({"error": "not found"}, 404)
        except Exception as e: self._json({"error": str(e)}, 500)
    def do_POST(self):
        u = urlparse(self.path); body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        try:
            if u.path == "/api/scan": return self._json(HX.run("scan-repo", source=body["source"]))
            if u.path == "/api/seance": return self._json(HX.run("seance", repo=int(body["repo"]), question=body["question"]))
            if u.path == "/api/resurrect": return self._json(HX.run("resurrect", repo=int(body["repo"])))
            self._json({"error": "not found"}, 404)
        except Exception as e: self._json({"error": str(e)}, 500)
    def log_message(self, *a): pass
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    if len(sys.argv) > 1:  # preload: python3 -m server.app <path-or-url>
        print("scanned", HX.run("scan-repo", source=sys.argv[1]))
    print(f"Commitmortem on http://localhost:{port}"); ThreadingHTTPServer(("", port), H).serve_forever()
