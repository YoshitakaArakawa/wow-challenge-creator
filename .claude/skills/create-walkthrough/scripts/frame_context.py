#!/usr/bin/env python3
"""Draw where a sheet sits on the dashboard: an orange frame on a crop of the dashboard render.

Cloud lays a dashboard out again when it renders, so the zone x/y/w/h saved in the workbook do
not give pixel positions. Instead, make_sheet_views.py gives every sheet zone of the verification
workbook a border in a colour of its own (listed in <workbook>.zones.json). This script finds each
colour in the render of that dashboard (--marked) and draws the orange frame at the same place on
the clean render of the finished dashboard (--render). Both renders must have the same size.

The crop keeps the full width and a band of the height around the zone, so the reader sees the
sheet with its neighbours.

Usage:
  python frame_context.py --render dash-all.png --marked sheets/refine/render/<Dashboard>.png \
      --zones sheets/<workbook>.zones.json --out-dir figs [--sheets "Sheet A,Sheet B"]
Writes <out-dir>/ctx-<sheet>.png (spaces and other symbols become _).
"""

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# Orange used for "build this" in the walkthrough template (--hl).
FRAME_COLOR = (242, 142, 43)
# Frame line width as a share of the image width: 6 px on a 1600 px render.
FRAME_WIDTH_SHARE = 6 / 1600
# The crop shows at least this share of the dashboard height, so short zones keep their neighbours.
MIN_CROP_SHARE = 0.30
# Extra height above and below the zone, as a share of the dashboard height.
PAD_SHARE = 0.07
# Largest per-channel difference that still counts as the marker colour (anti-aliased edges).
COLOR_TOLERANCE = 40
# A marker needs at least this many pixels; fewer means the colour was not drawn.
MIN_MARK_PIXELS = 20
# Crop edges move outward to the nearest blank row, at most this share of the height, so text is not cut.
SNAP_SHARE = 0.06
# A row counts as blank when every pixel is at least this light on each channel.
BLANK_MIN = 245


def safe_name(name: str) -> str:
    return re.sub(r"[^\w.-]+", "_", name).strip("_")


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def find_boxes(marked: Image.Image, colors: dict[str, tuple]) -> dict[str, tuple]:
    """Bounding box of the pixels of each marker colour, in one pass over the image."""
    px = marked.convert("RGB").load()
    w, h = marked.size
    boxes: dict[str, list] = {}
    counts = dict.fromkeys(colors, 0)
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            for name, (cr, cg, cb) in colors.items():
                if abs(r - cr) <= COLOR_TOLERANCE and abs(g - cg) <= COLOR_TOLERANCE and abs(b - cb) <= COLOR_TOLERANCE:
                    counts[name] += 1
                    bx = boxes.setdefault(name, [x, y, x, y])
                    bx[0], bx[1], bx[2], bx[3] = min(bx[0], x), min(bx[1], y), max(bx[2], x), max(bx[3], y)
                    break
    return {k: tuple(v) for k, v in boxes.items() if counts[k] >= MIN_MARK_PIXELS}


def blank_row(px, w: int, y: int) -> bool:
    return all(min(px[x, y]) >= BLANK_MIN for x in range(0, w, 2))


def snap(px, w: int, h: int, y: int, step: int) -> int:
    """Move y by step (-1 up, +1 down) until a blank row, within SNAP_SHARE of the height."""
    limit = round(SNAP_SHARE * h)
    for i in range(limit + 1):
        yy = y + step * i
        if yy < 0 or yy >= h:
            return max(0, min(h, yy))
        if blank_row(px, w, yy):
            return yy
    return y


def frame(img: Image.Image, box: tuple) -> Image.Image:
    w, h = img.size
    x0, y0, x1, y1 = box
    out = img.convert("RGB").copy()
    lw = max(2, round(w * FRAME_WIDTH_SHARE))
    ImageDraw.Draw(out).rectangle([x0 - lw / 2, y0 - lw / 2, x1 + lw / 2, y1 + lw / 2], outline=FRAME_COLOR, width=lw)
    band = max((y1 - y0) + 2 * PAD_SHARE * h, MIN_CROP_SHARE * h)
    mid = (y0 + y1) / 2
    top = round(max(0, min(h - band, mid - band / 2)))
    bottom = round(min(h, top + band))
    px = img.convert("RGB").load()
    top, bottom = snap(px, w, h, top, -1), snap(px, w, h, min(bottom, h - 1), +1)
    return out.crop((0, top, w, min(h, bottom + 1)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--render", required=True, type=Path, help="clean render of the finished dashboard")
    ap.add_argument("--marked", required=True, type=Path, help="render of the same dashboard in the verification workbook")
    ap.add_argument("--zones", required=True, type=Path, help="<workbook>.zones.json from make_sheet_views.py")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--sheets", default="", help="comma-separated sheet names (default: every marked zone)")
    args = ap.parse_args()
    marks = json.loads(args.zones.read_text(encoding="utf-8"))
    wanted = [s.strip() for s in args.sheets.split(",") if s.strip()] or [m["sheet"] for m in marks]
    colors = {m["sheet"]: hex_rgb(m["color"]) for m in marks if m["sheet"] in wanted}
    missing = [s for s in wanted if s not in colors]
    if missing:
        print(f"No marker for {missing}. Marked sheets: {[m['sheet'] for m in marks]}", file=sys.stderr)
        return 1
    img, marked = Image.open(args.render), Image.open(args.marked)
    if img.size != marked.size:
        print(f"Render sizes differ: {img.size} vs {marked.size}. Render both at the same resolution.", file=sys.stderr)
        return 1
    boxes = find_boxes(marked, colors)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    failed = 0
    for name in wanted:
        if name not in boxes:
            print(f"{name}: marker colour not found in {args.marked.name}", file=sys.stderr)
            failed += 1
            continue
        target = args.out_dir / f"ctx-{safe_name(name)}.png"
        frame(img, boxes[name]).save(target)
        print(f"{name}: box {boxes[name]} -> {target}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
