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
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_dotenv() -> None:
    """Load KEY=VALUE lines from a local .env into the environment (without overwriting
    anything already set). Stdlib only; .env is gitignored so no secret is tracked
    (constraint C-SECRETS). This is how the agent picks up ANTHROPIC_API_KEY to run as the
    live Claude tutor; with no key it falls back to the deterministic offline brain."""
    env = ROOT / ".env"
    if not env.exists():
        return
    for raw in env.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

from web.problems import (  # noqa: E402
    CATALOG, CATALOG_BY_ID, solve_descriptor, answer_question,
)
from agent import build_agent  # noqa: E402
from agent.agent import _claude_available  # noqa: E402

# One stateful agent per browser session (local, single-user; kept in memory). A session's
# agent remembers the current problem and — on the Claude path — the running conversation, so
# follow-up questions and view moves are multi-turn (G6). The offline brain is used when no
# API key is configured, so the app always works.
_AGENTS: dict[str, object] = {}
_AGENTS_LOCK = threading.Lock()


def _agent_for(session: str):
    with _AGENTS_LOCK:
        agent = _AGENTS.get(session)
        if agent is None:
            agent = build_agent()
            _AGENTS[session] = agent
        return agent

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
        if path.startswith("/vendor/"):
            # locally-vendored assets (Three.js). Resolve inside web/ only — no traversal.
            rel = path.lstrip("/")
            f = (WEB / rel).resolve()
            if WEB in f.parents and f.is_file():
                ctype = ("application/javascript; charset=utf-8" if f.suffix == ".js"
                         else "application/octet-stream")
                self._send(200, f.read_bytes(), ctype)
            else:
                self._json(404, {"error": "not found"})
            return
        if path == "/api/catalog":
            self._json(200, [{"id": d["id"], "area": d["area"], "title": d["title"]}
                             for d in CATALOG])
            return
        if path == "/api/agent/health":
            claude = _claude_available()
            self._json(200, {
                "brain": "claude" if claude else "offline",
                "claude_available": claude,
                "model": os.environ.get("MANIFOLD_MODEL", "claude-sonnet-4-6") if claude else None,
            })
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
        if path == "/api/agent":
            session = str(body.get("session") or "default")
            text = (body.get("text") or "").strip()
            if not text:
                self._json(400, {"error": "need a non-empty 'text'"})
                return
            if body.get("reset"):
                _agent_for(session).reset()
            try:
                result = _agent_for(session).run(text)
                self._json(200, result.to_dict())
            except Exception as exc:  # never surface a stack trace to the UI (G8)
                self._json(200, {"answer": f"Something went wrong: {type(exc).__name__}.",
                                 "declined": True, "scene": None, "trace": {},
                                 "quantities": [], "directives": []})
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
