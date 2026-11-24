#!/usr/bin/env python3
"""Turn the editable walkthrough source into a single-file page, then check it is safe to publish.

1. Every "embed:<path>" (path relative to the theme folder) in the source becomes a base64 data URI,
   wherever it appears: an img src, a JS string, CSS url().
2. The output is scanned for things a public repository must not carry:
   absolute or personal paths, file:// URLs, e-mail addresses, Tableau Cloud URLs,
   and the site / project / workbook identifiers found in every publish-result.json under the theme
   folder (the finished workbook and the verification workbook). Workbook names that start with the
   challenge week (YYYYWNN, e.g. 2026W47) are public titles and are not checked.
   Any hit fails the build (exit 1) and the output file is not written.
   Mentions of working folders (refine/, tmp/) are reported as warnings: readers cannot open them.

Usage:
  python build_walkthrough.py --theme-dir outputs/2026-01-01-theme --lang ja
      [--src tmp/walkthrough/walkthrough-ja.src.html] [--out guide/walkthrough-ja.html]
"""

import argparse
import base64
import json
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

EMBED_RE = re.compile(r"embed:([^\"'\s)]+)")
# A single-file page over this size is slow to open from a repository viewer.
WARN_SIZE_BYTES = 3 * 1024 * 1024

FORBIDDEN = [
    (re.compile(r"[A-Za-z]:\\\\?[^\s\"'<>]*"), "Windows absolute path"),
    (re.compile(r"(?<![\w.])/(?:Users|home)/[^\s\"'<>]+"), "home directory path"),
    # Built from parts so this source file does not itself contain a file-scheme URL.
    (re.compile("file" + r":/{2,3}", re.IGNORECASE), "file-scheme URL"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "e-mail address"),
    (re.compile(r"[\w.-]*online\.tableau\.com", re.IGNORECASE), "Tableau Cloud URL"),
]
# Workbook names such as "2026W47" or "2026W47 Starter" are the challenge's public titles.
PUBLIC_WORKBOOK_NAME = re.compile(r"^\d{4}W\d{2}\b")
WORKING_FOLDERS = re.compile(r"\b(?:refine|tmp|prototype|Archived)/[^\s\"'<>]*")


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    return Path.cwd()


def identifiers(theme: Path) -> list[tuple[str, str]]:
    """Site, project and workbook names from every publish-result.json: real names that must not leak."""
    out = []
    for result in sorted(theme.rglob("publish-result*.json")):
        try:
            data = json.loads(result.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for key in ("projectName", "workbookId", "workbookName"):
            value = data.get(key)
            if not value:
                continue
            if key == "workbookName" and PUBLIC_WORKBOOK_NAME.match(str(value)):
                continue
            out.append((str(value), f"{result.name} {key}"))
        url = data.get("webpageUrl") or ""
        m = re.search(r"/site/([^/]+)/", urlparse(url).fragment or url)
        if m:
            out.append((m.group(1), "Tableau Cloud site name"))
    return list(dict.fromkeys(out))


def embed(html: str, theme: Path) -> tuple[str, list[str]]:
    used = []

    def repl(m: re.Match) -> str:
        rel = m.group(1)
        path = (theme / rel).resolve()
        if not path.exists():
            raise SystemExit(f"embed target not found: {rel}")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        used.append(rel)
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

    return EMBED_RE.sub(repl, html), list(dict.fromkeys(used))


def scan(html: str, theme: Path) -> tuple[list[str], list[str]]:
    text = re.sub(r"data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+", "", html)
    errors, warnings = [], []
    for rx, label in FORBIDDEN:
        for m in rx.finditer(text):
            errors.append(f"{label}: {m.group(0)[:80]}")
    for value, label in identifiers(theme):
        if value and value in text:
            errors.append(f"{label}: {value}")
    for m in WORKING_FOLDERS.finditer(text):
        warnings.append(f"working-folder path (readers cannot open it): {m.group(0)}")
    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme-dir", required=True)
    ap.add_argument("--lang", choices=("ja", "en"), required=True)
    ap.add_argument("--src", help="relative to the theme folder (default: tmp/walkthrough/walkthrough-<lang>.src.html)")
    ap.add_argument("--out", help="relative to the theme folder (default: guide/walkthrough-<lang>.html)")
    args = ap.parse_args()
    args.src = args.src or f"tmp/walkthrough/walkthrough-{args.lang}.src.html"
    args.out = args.out or f"guide/walkthrough-{args.lang}.html"

    theme = Path(args.theme_dir)
    if not theme.is_absolute():
        theme = (find_repo_root(Path(__file__).resolve()) / theme).resolve()
    src = theme / args.src
    if not src.exists():
        print(f"source not found: {src}", file=sys.stderr)
        return 1

    html, used = embed(src.read_text(encoding="utf-8"), theme)
    errors, warnings = scan(html, theme)
    for w in dict.fromkeys(warnings):
        print(f"WARN  {w}")
    if errors:
        for e in dict.fromkeys(errors):
            print(f"ERROR {e}")
        print("Not written. Remove the items above from the source and run again.", file=sys.stderr)
        return 1

    out = theme / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8", newline="\n")
    size = out.stat().st_size
    print(f"wrote {out.relative_to(theme).as_posix()} ({size:,} bytes, {len(used)} files embedded: {', '.join(used)})")
    if size > WARN_SIZE_BYTES:
        print(f"WARN  output is over {WARN_SIZE_BYTES // (1024 * 1024)} MB; shrink the images")
    return 0


if __name__ == "__main__":
    sys.exit(main())
