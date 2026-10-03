"""Tableau Cloud sign-in shared by the Cloud-facing scripts in this repository.

Default path is OAuth 2.0 Authorization Code + PKCE through the browser, so no static
token lives in `.env`. The resulting access_token is cached (gitignored) and reused
until the server rejects it. If `TABLEAU_PAT_NAME` / `TABLEAU_PAT_VALUE` are set,
a Personal Access Token is used instead and nothing is cached.

Required .env variables: TABLEAU_SERVER_URL
Optional .env variables: TABLEAU_SITE_ID (content URL; empty = default site),
                         OAUTH_CALLBACK_PORT (default 8765),
                         TABLEAU_PAT_NAME + TABLEAU_PAT_VALUE (switches to PAT auth)

Library usage:

    from tableau_auth import signed_in_server
    with signed_in_server() as server:
        server.workbooks.get()

CLI:

    python tableau_auth.py login    # run the browser flow now and cache the token
    python tableau_auth.py status   # exit 0 if a cached token is alive
    python tableau_auth.py logout   # sign out server-side and delete the cache
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import http.server
import json
import os
import secrets
import socketserver
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from pathlib import Path

try:
    import tableauserverclient as TSC
except ImportError:
    sys.exit("ERROR: tableauserverclient is required. Install with: pip install -r requirements.txt")

try:
    from dotenv import load_dotenv
except ImportError:
    sys.exit("ERROR: python-dotenv is required. Install with: pip install -r requirements.txt")


REPO_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(REPO_ROOT / ".env")

CLIENT_TYPE = "wow-challenge-creator"
USER_AGENT = "wow-challenge-creator/0.1 (python)"
# Loopback redirect port for the PKCE callback; any free local port works.
DEFAULT_CALLBACK_PORT = 8765
# A human has to finish the browser sign-in; five minutes covers MFA prompts.
OAUTH_TIMEOUT_SECONDS = 300
# Cached session shared with the TypeScript Cloud scripts (same JSON shape).
CACHE_PATH = REPO_ROOT / ".auth-cache" / "session.json"


def load_credentials() -> dict:
    server_url = (os.environ.get("TABLEAU_SERVER_URL") or "").rstrip("/")
    if not server_url:
        sys.exit(f"ERROR: Missing required env var TABLEAU_SERVER_URL. Configure {REPO_ROOT / '.env'}")
    return {
        "server_url": server_url,
        "site_name": os.environ.get("TABLEAU_SITE_ID", ""),
        "port": int(os.environ.get("OAUTH_CALLBACK_PORT", DEFAULT_CALLBACK_PORT)),
        "pat_name": os.environ.get("TABLEAU_PAT_NAME", ""),
        "pat_value": os.environ.get("TABLEAU_PAT_VALUE", ""),
    }


# ----- PKCE -----
def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


# ----- Local callback listener -----
class _CallbackResult:
    def __init__(self):
        self.code: str | None = None
        self.error: str | None = None
        self.event = threading.Event()


def _make_callback_handler(expected_state: str, result: _CallbackResult):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/Callback":
                self.send_response(404)
                self.end_headers()
                return
            query = urllib.parse.parse_qs(parsed.query)
            received_state = (query.get("state") or [None])[0]
            if received_state != expected_state:
                result.error = "state mismatch"
            else:
                result.code = (query.get("code") or [None])[0]
                if "error" in query:
                    result.error = (query.get("error") or [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>Sign-in received.</h2>"
                b"<p>You can close this tab and return to the terminal.</p></body></html>"
            )
            result.event.set()

        def log_message(self, *_args, **_kwargs):
            return

    return Handler


# ----- raw HTTP helpers (stdlib only) -----
def _http_post_form(url: str, body: dict[str, str], timeout: int = 30) -> dict:
    req = urllib.request.Request(
        url=url,
        data=urllib.parse.urlencode(body).encode(),
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"[auth] ERROR: POST {url} -> HTTP {e.code}\n{e.read().decode(errors='replace')}")


def _probe_session(server_url: str, api_version: str, access_token: str) -> dict | None:
    """Return sessions/current JSON when the token is alive, None otherwise."""
    req = urllib.request.Request(
        url=f"{server_url}/api/{api_version}/sessions/current",
        method="GET",
        headers={"Accept": "application/json", "X-Tableau-Auth": access_token, "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


# ----- Session cache -----
def _load_cached_session(server_url: str, site_name: str, api_version: str) -> dict | None:
    if not CACHE_PATH.exists():
        return None
    try:
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"[auth] cache unreadable, ignoring: {e}", file=sys.stderr)
        return None
    if cache.get("server_url") != server_url or cache.get("site_name") != site_name:
        return None
    access_token = cache.get("access_token")
    if not access_token:
        return None
    session = _probe_session(server_url, api_version, access_token)
    if session is None:
        print("[auth] cached token rejected by server, re-authenticating", file=sys.stderr)
        CACHE_PATH.unlink(missing_ok=True)
        return None
    return {"access_token": access_token, "user_id": session["session"]["user"]["id"]}


def _save_session(server_url: str, site_name: str, access_token: str) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps({"server_url": server_url, "site_name": site_name, "access_token": access_token}, indent=2),
        encoding="utf-8",
    )
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, CACHE_PATH)


# ----- OAuth authorization_code (PKCE) flow -----
def _run_oauth_flow(server_url: str, site_name: str, port: int) -> str:
    """Drive the browser sign-in. Returns access_token (3-part `id1|id2|site-luid`)."""
    redirect_uri = f"http://127.0.0.1:{port}/Callback"
    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(32)

    result = _CallbackResult()
    httpd = socketserver.TCPServer(("127.0.0.1", port), _make_callback_handler(state, result))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    auth_params = {
        "client_id": str(uuid.uuid4()),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
        "device_id": str(uuid.uuid4()),
        "device_name": f"{CLIENT_TYPE} (python)",
        "target_site": site_name,
        "client_type": CLIENT_TYPE,
    }
    auth_url = f"{server_url}/oauth2/v1/auth?" + urllib.parse.urlencode(auth_params)
    print("[auth] opening browser for Tableau Cloud sign-in...", file=sys.stderr)
    webbrowser.open(auth_url)

    received = result.event.wait(timeout=OAUTH_TIMEOUT_SECONDS)
    httpd.shutdown()
    if not received:
        raise SystemExit("[auth] ERROR: timed out waiting for the browser sign-in")
    if result.error or not result.code:
        raise SystemExit(f"[auth] ERROR: sign-in callback failed: {result.error!r}")

    token = _http_post_form(
        f"{server_url}/oauth2/v1/token",
        {
            "grant_type": "authorization_code",
            "code": result.code,
            "code_verifier": verifier,
            "redirect_uri": redirect_uri,
            "client_id": auth_params["client_id"],
        },
    )
    return token["access_token"]


def _derive_site_luid(access_token: str) -> str:
    parts = access_token.split("|")
    if len(parts) != 3:
        raise SystemExit("[auth] ERROR: unexpected access_token shape (expected 3 '|'-separated parts)")
    return parts[2]


def _fetch_user_id(server_url: str, api_version: str, access_token: str) -> str:
    session = _probe_session(server_url, api_version, access_token)
    if session is None:
        raise SystemExit("[auth] ERROR: freshly issued token was rejected by sessions/current")
    return session["session"]["user"]["id"]


@contextlib.contextmanager
def signed_in_server():
    """Yield a signed-in TSC.Server.

    OAuth path: reuse the cached token when alive, otherwise run the browser flow and
    cache the result. The session is left open on exit so the cache stays valid.
    PAT path (TABLEAU_PAT_NAME/VALUE set): plain TSC sign-in, signed out on exit.
    """
    creds = load_credentials()
    server_url, site_name = creds["server_url"], creds["site_name"]
    server = TSC.Server(server_url, use_server_version=True)

    if creds["pat_name"] and creds["pat_value"]:
        auth = TSC.PersonalAccessTokenAuth(creds["pat_name"], creds["pat_value"], site_name)
        with server.auth.sign_in(auth):
            yield server
        return

    api_version = server.version
    cached = _load_cached_session(server_url, site_name, api_version)
    if cached:
        access_token, user_id = cached["access_token"], cached["user_id"]
    else:
        access_token = _run_oauth_flow(server_url, site_name, creds["port"])
        user_id = _fetch_user_id(server_url, api_version, access_token)
        _save_session(server_url, site_name, access_token)

    server._set_auth(_derive_site_luid(access_token), user_id, access_token, site_url=site_name)
    yield server


# ----- CLI -----
def _cli_login() -> int:
    with signed_in_server() as server:
        print(f"signed in: site_id={server.site_id} user_id={server.user_id}")
    return 0


def _cli_status() -> int:
    if not CACHE_PATH.exists():
        print("status: no cached session (run `tableau_auth.py login`)")
        return 1
    try:
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"status: unreadable cache ({e})")
        return 1
    server_url, access_token = cache.get("server_url"), cache.get("access_token")
    if not (server_url and access_token):
        print("status: malformed cache")
        return 1
    api_version = TSC.Server(server_url, use_server_version=True).version
    session = _probe_session(server_url, api_version, access_token)
    if session is None:
        print("status: expired or invalid (next call will re-authenticate)")
        return 1
    print(f"status: alive (site={cache.get('site_name')!r} user_id={session['session']['user']['id']})")
    return 0


def _cli_logout() -> int:
    if not CACHE_PATH.exists():
        print("no cached session to remove")
        return 0
    try:
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        cache = {}
    server_url, access_token = cache.get("server_url"), cache.get("access_token")
    if server_url and access_token:
        try:
            api_version = TSC.Server(server_url, use_server_version=True).version
            req = urllib.request.Request(
                url=f"{server_url}/api/{api_version}/auth/signout",
                method="POST",
                headers={"X-Tableau-Auth": access_token, "User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=10):
                pass
            print("server-side sign-out OK")
        except Exception as e:  # best effort; the cache is removed regardless
            print(f"server-side sign-out failed (ignored): {e}")
    CACHE_PATH.unlink(missing_ok=True)
    print("cache deleted")
    return 0


def _main(argv: list[str]) -> int:
    commands = {"login": _cli_login, "status": _cli_status, "logout": _cli_logout}
    if len(argv) < 2 or argv[1] not in commands:
        print("usage: python tableau_auth.py {login|status|logout}", file=sys.stderr)
        return 2
    return commands[argv[1]]()


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
