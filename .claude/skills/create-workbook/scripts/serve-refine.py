#!/usr/bin/env python3
"""Serve a theme folder on localhost so the refine compare page can be opened in a browser.

    python serve-refine.py outputs/{theme} [--port 8790]

The theme folder is the web root: the compare page is /refine/compare.html and drafts are /prototype/*.html.
Text files are sent as UTF-8 (prototype HTML may lack a charset meta) and nothing is cached, so a plain
reload always shows the latest draft and render. Binds to 127.0.0.1 only.
"""

import argparse
import functools
import http.server
import sys
from pathlib import Path

# Any free local port works; 8790 avoids the common dev-server ports (3000, 5173, 8000, 8080).
DEFAULT_PORT = 8790


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".md": "text/plain; charset=utf-8",
    }

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *_args):
        return


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("theme_dir", help="outputs/{theme}")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = p.parse_args()

    root = Path(args.theme_dir).resolve()
    if not (root / "refine").is_dir():
        print(f"ERROR: {root / 'refine'} not found. Run iterate.ts first.", file=sys.stderr)
        return 2

    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), functools.partial(Handler, directory=str(root)))
    print(f"compare page: http://127.0.0.1:{args.port}/refine/compare.html", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
