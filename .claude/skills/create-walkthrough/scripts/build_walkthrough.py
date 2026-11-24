#!/usr/bin/env python3
"""Turn the editable walkthrough source into a single-file page, check it, and optionally screenshot it.

1. Every "embed:<path>" (path relative to the theme folder) in the source becomes a base64 data URI,
   wherever it appears: an img src, a JS string, CSS url().
2. The output is scanned for things a public repository must not carry:
   absolute or personal paths, file:// URLs, e-mail addresses, Tableau Cloud URLs,
   and the site / project / workbook identifiers found in every publish-result.json under the theme
   folder (the finished workbook and the verification workbook). Workbook names that start with the
   challenge week (YYYYWNN, e.g. 2026W47) are public titles and are not checked.
   Any hit fails the build (exit 1) and the output file is not written.
   Mentions of working folders (refine/, tmp/) are reported as warnings: readers cannot open them.
   With --lang en, any Japanese character left in the page (text, comments or CSS) is an error.
3. --shoot <dir>: headless Chrome shots at 1100 px and at 375 px (inside an iframe, because
   headless Chrome cannot make its window narrower than 500 px), trimmed to the content and cut
   into 1800 px slices to read one by one. Chrome is found at the usual places, or set CHROME.

Usage:
  python build_walkthrough.py --theme-dir outputs/2026-01-01-theme --lang ja
      [--src tmp/walkthrough/walkthrough-ja.src.html] [--out guide/walkthrough-ja.html]
      [--shoot tmp/walkthrough/shots]
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

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
# Hiragana, katakana, CJK ideographs and full-width forms: none may remain in the English page.
CJK_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff00-\uffef]")
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


CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chromium-browser",
]
# Taller than a long walkthrough at phone width; the shot is trimmed to the content afterwards.
MAX_HEIGHT = 60000
# Blank rows kept under the last content row.
TRIM_MARGIN = 40
# The iframe ends a little above the window bottom, so the crop below it holds only the page.
FRAME_HEIGHT = MAX_HEIGHT - 100
# Chrome needs a moment to lay out web fonts and images before the screenshot.
VIRTUAL_TIME_MS = 5000


def find_chrome() -> str:
    for c in [os.environ.get("CHROME", "")] + CANDIDATES:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    raise SystemExit("Chrome not found. Set CHROME to its path.")


def shoot(chrome: str, url: str, width: int, out: Path, keep: tuple[int, int] | None = None) -> Image.Image:
    """Take the shot, keep the top-left (width, height) box if given, trim to the last content row."""
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--virtual-time-budget={VIRTUAL_TIME_MS}", f"--window-size={width},{MAX_HEIGHT}",
                    f"--screenshot={out}", url], capture_output=True, check=False)
    if not out.exists():
        raise SystemExit(f"Chrome wrote no screenshot for {url}")
    im = Image.open(out).convert("RGB")
    if keep:
        im = im.crop((0, 0, min(keep[0], im.width), min(keep[1], im.height)))
    bg = im.getpixel((2, im.height - 2))
    px = im.load()
    last = 0
    for y in range(im.height - 1, 0, -1):
        if any(px[x, y] != bg for x in range(0, im.width, 3)):
            last = y
            break
    im = im.crop((0, 0, im.width, min(im.height, last + TRIM_MARGIN)))
    im.save(out)
    return im


def slices(im: Image.Image, out: Path, seg: int) -> int:
    for old in out.parent.glob(f"{out.stem}-*.png"):
        old.unlink()
    n = 0
    for n, y in enumerate(range(0, im.height, seg), 1):
        im.crop((0, y, im.width, min(im.height, y + seg))).save(out.with_name(f"{out.stem}-{n:02d}.png"))
    return n


def shoot_page(page: Path, out_dir: Path, width: int = 1100, phone: int = 375, seg: int = 1800):
    out_dir.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    stem = page.stem
    wide = shoot(chrome, page.resolve().as_uri(), width, out_dir / f"{stem}-w{width}.png")
    print(f"shot {width}px: height {wide.height}, {slices(wide, out_dir / f'{stem}-w{width}.png', seg)} slices")
    frame = out_dir / f"{stem}-frame{phone}.html"
    frame.write_text(
        "<!doctype html><meta charset='utf-8'><style>body{margin:0;background:#888}"
        f"iframe{{width:{phone}px;height:{FRAME_HEIGHT}px;border:0;background:#fff}}</style>"
        f"<iframe src='{page.resolve().as_uri()}'></iframe>", encoding="utf-8")
    # 520 px: just above the 500 px minimum window width of headless Chrome.
    narrow = shoot(chrome, frame.as_uri(), 520, out_dir / f"{stem}-p{phone}.png", keep=(phone, FRAME_HEIGHT))
    print(f"shot {phone}px: height {narrow.height}, {slices(narrow, out_dir / f'{stem}-p{phone}.png', seg)} slices")


def scan(html: str, theme: Path, lang: str) -> tuple[list[str], list[str]]:
    text = re.sub(r"data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+", "", html)
    errors, warnings = [], []
    for rx, label in FORBIDDEN:
        for m in rx.finditer(text):
            errors.append(f"{label}: {m.group(0)[:80]}")
    for value, label in identifiers(theme):
        if value and value in text:
            errors.append(f"{label}: {value}")
    if lang == "en":
        for n, line in enumerate(text.splitlines(), 1):
            if CJK_RE.search(line):
                errors.append(f"Japanese left in the English page, line {n}: {line.strip()[:60]}")
    for m in WORKING_FOLDERS.finditer(text):
        warnings.append(f"working-folder path (readers cannot open it): {m.group(0)}")
    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme-dir", required=True)
    ap.add_argument("--lang", choices=("ja", "en"), required=True)
    ap.add_argument("--src", help="relative to the theme folder (default: tmp/walkthrough/walkthrough-<lang>.src.html)")
    ap.add_argument("--out", help="relative to the theme folder (default: guide/walkthrough-<lang>.html)")
    ap.add_argument("--shoot", help="after writing, screenshot the page into this folder (relative to the theme folder)")
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
    errors, warnings = scan(html, theme, args.lang)
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
    if args.shoot:
        shoot_page(out, theme / args.shoot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
