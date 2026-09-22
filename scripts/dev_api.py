# -*- coding: utf-8 -*-
"""Local stand-in for Vercel Python functions: python scripts/dev_api.py  (serves /api/* on :5050)."""
import os, sys, importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(ROOT, "api")
sys.path.insert(0, API)
mods = {}
for f in os.listdir(API):
    if f.endswith(".py") and not f.startswith("_"):
        spec = importlib.util.spec_from_file_location(f[:-3], os.path.join(API, f)); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        mods["/api/" + f[:-3]] = m

class Dispatch(BaseHTTPRequestHandler):
    def _route(self):
        p = self.path.split("?")[0].rstrip("/")
        m = mods.get(p)
        if not m:
            self.send_response(404); self.end_headers(); self.wfile.write(b"not found"); return
        m.handle(self)
    def do_POST(self): self._route()
    def do_GET(self): self._route()
    def log_message(self, fmt, *a): sys.stderr.write("[api] " + (fmt % a) + "\n")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    print("dev api on http://localhost:%d  routes: %s" % (port, ", ".join(sorted(mods))), flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Dispatch).serve_forever()
