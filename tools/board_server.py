#!/usr/bin/env python3
"""Serve the Constraint Board live on localhost, auto-refreshing in the browser.

    python3 tools/board_server.py            # http://127.0.0.1:8787
    python3 tools/board_server.py --port 9000
    python3 tools/board_server.py --open     # also open it in your default browser

Leave the page open on your Mac and watch the board move as the worker makes progress:
the page re-fetches the current state every couple of seconds, so criteria tick over and
the check bar turns green with no refreshing on your part.

It reflects whatever the repo and the last verify run say *right now*. It does not re-run
checks — that is the worker's job — so it shows a STALE flag when the code has changed
since verify last ran. To move the check bar, the worker (or you) runs tools/verify.py;
the board picks up the new results within a couple of seconds.

Local only: binds to 127.0.0.1 and opens no outbound connection (constraint C-LOCAL). The
page pulls fonts from Google Fonts, exactly as the published Artifact does.

Standard library only.
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import status  # noqa: E402

POLL_MS = 2500


def full_page() -> str:
    """The wrapping document: styles once, a live indicator, and a poll-and-swap script."""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"{status.page_head()}"
        "<style>#live{position:fixed;top:10px;right:12px;z-index:9;display:flex;"
        "align-items:center;gap:6px;font:600 11px/1 'IBM Plex Mono',monospace;"
        "letter-spacing:.1em;text-transform:uppercase;color:var(--faint)}"
        "#live b{width:7px;height:7px;border-radius:50%;background:var(--ok);"
        "animation:lp 2s ease-in-out infinite}@keyframes lp{50%{opacity:.25}}"
        "@media (prefers-reduced-motion:reduce){#live b{animation:none}}</style>"
        "</head><body>"
        '<div id="live"><b></b>live</div>'
        f'<div id="root">{status.render_body(status.collect())}</div>'
        "<script>"
        "async function tick(){try{const r=await fetch('/fragment',{cache:'no-store'});"
        "if(r.ok){const h=await r.text();const root=document.getElementById('root');"
        "if(root.innerHTML!==h)root.innerHTML=h;}}catch(e){}}"
        f"setInterval(tick,{POLL_MS});"
        "document.addEventListener('visibilitychange',()=>{if(!document.hidden)tick();});"
        "</script></body></html>"
    )


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._send(full_page())
        elif path == "/fragment":
            self._send(status.render_body(status.collect()))
        else:
            self.send_error(404, "not found")

    def log_message(self, *args) -> None:  # keep the terminal quiet
        pass


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Serve the Constraint Board live on localhost.")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--open", action="store_true", help="open the board in your browser")
    args = ap.parse_args(argv)

    url = f"http://127.0.0.1:{args.port}"
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Constraint Board live at {url}   (Ctrl+C to stop)")
    print(f"Auto-refreshes every {POLL_MS // 1000}s. It reflects current state; run "
          "tools/verify.py to update the checks.")
    if args.open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
