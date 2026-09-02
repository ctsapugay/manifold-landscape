#!/usr/bin/env python3
"""Local development server for Manifold Landscape (constraint C-LOCAL: localhost only).

    python3 web/server.py            # serve on http://127.0.0.1:8765
    python3 web/server.py --port N

Serves the single-page app and a small JSON API:
    GET  /                  the app
    GET  /api/catalog       list of example problems (id, area, title)
    GET  /api/scene?id=S1   the verified solution + step-tagged geometry for one example
    POST /api/solve         solve a problem descriptor (JSON body) — for user-posed problems

The server never computes mathematics itself: it calls the engine, which returns only
verified quantities. Standard library only; no external dependencies.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.problems import (  # noqa: E402
    CATALOG, CATALOG_BY_ID, solve_descriptor, answer_question,
)

WEB = ROOT / "web"
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json; charset=utf-8")

    def log_message(self, *_args) -> None:  # keep the console quiet
        pass

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path in STATIC:
            name, ctype = STATIC[path]
            f = WEB / name
            if f.exists():
                self._send(200, f.read_bytes(), ctype)
            else:
                self._json(404, {"error": f"missing {name}"})
            return
        if path == "/api/catalog":
            self._json(200, [{"id": d["id"], "area": d["area"], "title": d["title"]}
                             for d in CATALOG])
            return
        if path == "/api/scene":
            qs = parse_qs(parsed.query)
            pid = (qs.get("id") or [""])[0]
            desc = CATALOG_BY_ID.get(pid)
            if not desc:
                self._json(404, {"error": f"no such problem {pid!r}"})
                return
            try:
                self._json(200, solve_descriptor(desc))
            except Exception as exc:  # surface a clean error, never a stack trace to the UI
                self._json(500, {"error": f"{type(exc).__name__}: {exc}"})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception as exc:
            self._json(400, {"error": f"bad JSON: {exc}"})
            return
        if path == "/api/solve":
            try:
                self._json(200, solve_descriptor(body))
            except Exception as exc:
                self._json(400, {"error": f"{type(exc).__name__}: {exc}"})
            return
        if path == "/api/ask":
            desc = CATALOG_BY_ID.get(body.get("id")) or body.get("descriptor")
            question = (body.get("question") or "").strip()
            if not desc or not question:
                self._json(400, {"error": "need a known problem id (or descriptor) and a question"})
                return
            try:
                self._json(200, answer_question(desc, question))
            except Exception as exc:
                self._json(500, {"error": f"{type(exc).__name__}: {exc}"})
            return
        self._json(404, {"error": "not found"})


def main(argv: list[str]) -> int:
    port = 8765
    if "--port" in argv:
        port = int(argv[argv.index("--port") + 1])
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Manifold Landscape → http://127.0.0.1:{port}  (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
