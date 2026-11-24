#!/usr/bin/env python3
"""Screenshot a walkthrough page with headless Chrome, at desktop width and at phone width.

Headless Chrome cannot make its window narrower than 500 px, so the phone shot loads the page
inside a 375 px iframe. Each shot is trimmed to the content height and cut into slices that are
small enough to read one by one.

Usage:
  python shoot.py <page.html> --out-dir <dir> [--width 1100] [--phone 375] [--slice 1800]
Chrome is found at the usual Windows / macOS / Linux locations, or set CHROME to its path.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--width", type=int, default=1100)
    ap.add_argument("--phone", type=int, default=375)
    ap.add_argument("--slice", type=int, default=1800, help="slice height in px")
    args = ap.parse_args()
    page = args.page.resolve()
    if not page.exists():
        print(f"Page not found: {page}", file=sys.stderr)
        return 1
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome()
    stem = page.stem

    wide = shoot(chrome, page.as_uri(), args.width, out_dir / f"{stem}-w{args.width}.png")
    print(f"desktop {args.width}px: height {wide.height}, {slices(wide, out_dir / f'{stem}-w{args.width}.png', args.slice)} slices")

    # The iframe is as tall as the page would be, so the outer shot shows the whole phone layout.
    frame = out_dir / f"{stem}-frame{args.phone}.html"
    frame.write_text(
        "<!doctype html><meta charset='utf-8'><style>body{margin:0;background:#888}"
        f"iframe{{width:{args.phone}px;height:{FRAME_HEIGHT}px;border:0;background:#fff}}</style>"
        f"<iframe src='{page.as_uri()}'></iframe>", encoding="utf-8")
    # 520 px: just above the 500 px minimum window width of headless Chrome.
    phone = shoot(chrome, frame.as_uri(), 520, out_dir / f"{stem}-p{args.phone}.png", keep=(args.phone, FRAME_HEIGHT))
    print(f"phone {args.phone}px: height {phone.height}, {slices(phone, out_dir / f'{stem}-p{args.phone}.png', args.slice)} slices")
    return 0


if __name__ == "__main__":
    sys.exit(main())
