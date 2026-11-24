#!/usr/bin/env python3
"""Figures for a walkthrough: verification workbooks, and "where is this sheet" frames.

make  <finished.twbx> <out.twbx> [--sheets "A,B"]
  Writes two copies of the finished workbook (packaged data kept, source untouched):
  - <out>.twbx: the axis "display = false" formats are removed from the worksheets (all by
    default), so each worksheet, published as a view, renders with its axes and title.
    Prints "axes shown: none" when the finished workbook hides no axes.
  - <out>_Frames.twbx + <out>_Frames.zones.json: every sheet zone on the dashboards gets a
    solid border in a colour of its own. Axes stay hidden here: shown axes change the height
    of zones that are not fixed.

frame --render <clean.png> --marked <frames.png> --zones <zones.json> --out-dir <dir> [--sheets "A,B"]
  Cloud lays a dashboard out again when it renders, so the saved zone x/y/w/h do not give
  pixel positions. This finds each sheet's colour in the render of the _Frames dashboard and
  draws an orange frame at that place on the clean render of the finished dashboard (same
  size), cropped to a band around the zone. Writes <out-dir>/ctx-<sheet>.png.
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

WORKSHEET_RE = re.compile(r"(<worksheet\b[^>]*\bname='(?P<name>[^']*)'.*?</worksheet>)", re.DOTALL)
AXIS_RULE_RE = re.compile(r"(<style-rule element='axis'>)(?P<body>.*?)(</style-rule>)", re.DOTALL)
HIDE_RE = re.compile(r"\s*<format attr='display'[^>]*value='false'[^>]*/>")
DASHBOARDS_RE = re.compile(r"<dashboards>.*?</dashboards>", re.DOTALL)
# A sheet zone: has a name, no type-v2 (filters, text and layout zones have one), and no child zones.
SHEET_ZONE_RE = re.compile(r"(<zone (?=[^>]*\bname=')(?![^>]*\btype-v2=)[^>]*?>)(?P<body>(?:(?!<zone ).)*?)(</zone>)", re.DOTALL)
ZONE_NAME_RE = re.compile(r"\bname='([^']*)'")
BORDER_RE = re.compile(r"\s*<format attr='border-(?:color|style|width)' value='[^']*' />")
# Saturated colours that a viz rarely uses, one per sheet zone.
MARK_COLORS = ["#ff00ff", "#00ff00", "#ff0000", "#0000ff", "#00ffff", "#ffff00", "#800080", "#008000",
               "#800000", "#000080", "#008080", "#808000", "#ff8000", "#8000ff", "#0080ff", "#ff0080"]
# Border width in dashboard pixels; thin enough to leave the layout as it is.
MARK_WIDTH = "2"


def show_axes(twb: str, sheets: set[str] | None) -> tuple[str, list[str]]:
    changed = []

    def per_sheet(m: re.Match) -> str:
        name = m.group("name")
        if sheets is not None and name not in sheets:
            return m.group(1)
        count = 0

        def per_rule(r: re.Match) -> str:
            nonlocal count
            body, n = HIDE_RE.subn("", r.group("body"))
            count += n
            return r.group(1) + body + r.group(3)

        text = AXIS_RULE_RE.sub(per_rule, m.group(1))
        if count:
            changed.append(f"{name} ({count})")
        return text

    return WORKSHEET_RE.sub(per_sheet, twb), changed


def mark_zones(twb: str) -> tuple[str, list[dict]]:
    marks: list[dict] = []

    def per_zone(m: re.Match) -> str:
        name = ZONE_NAME_RE.search(m.group(1)).group(1)
        if len(marks) >= len(MARK_COLORS):
            raise SystemExit(f"More than {len(MARK_COLORS)} sheet zones; add colours to MARK_COLORS.")
        color = MARK_COLORS[len(marks)]
        marks.append({"sheet": name, "color": color})
        border = (f"<format attr='border-color' value='{color}' />"
                  f"<format attr='border-style' value='solid' />"
                  f"<format attr='border-width' value='{MARK_WIDTH}' />")
        body = BORDER_RE.sub("", m.group("body"))
        if "<zone-style>" in body:
            body = body.replace("<zone-style>", "<zone-style>" + border, 1)
        else:
            body = f"<zone-style>{border}</zone-style>" + body
        return m.group(1) + body + m.group(3)

    def per_block(b: re.Match) -> str:
        return SHEET_ZONE_RE.sub(per_zone, b.group(0))

    return DASHBOARDS_RE.sub(per_block, twb), marks


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


def cmd_make(args) -> int:
    if args.src.suffix.lower() != ".twbx" or not args.src.exists():
        print(f"Need an existing .twbx: {args.src}", file=sys.stderr)
        return 1
    if args.out.resolve() == args.src.resolve():
        print("Output must differ from the source workbook.", file=sys.stderr)
        return 1
    sheets = {s.strip() for s in args.sheets.split(",") if s.strip()} or None
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frames = args.out.with_name(f"{args.out.stem}_Frames.twbx")
    with zipfile.ZipFile(args.src) as zin:
        twbs = [n for n in zin.namelist() if n.lower().endswith(".twb")]
        if len(twbs) != 1:
            print(f"Expected one .twb inside, found {twbs}", file=sys.stderr)
            return 1
        # Read everything first: writestr() updates the ZipInfo it is given, which breaks later reads.
        entries = [(item.filename, item.date_time, zin.read(item.filename)) for item in zin.infolist()]
    twb = next(data for name, _, data in entries if name == twbs[0]).decode("utf-8")
    axes_twb, changed = show_axes(twb, sheets)
    frames_twb, marks = mark_zones(twb)
    for target, text in ((args.out, axes_twb), (frames, frames_twb)):
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zout:
            for name, date_time, data in entries:
                info = zipfile.ZipInfo(name, date_time)
                info.compress_type = zipfile.ZIP_DEFLATED
                zout.writestr(info, text.encode("utf-8") if name == twbs[0] else data)
    zones_json = frames.with_suffix(".zones.json")
    zones_json.write_text(json.dumps(marks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"wrote {frames} and {zones_json.name} ({len(marks)} sheet zones marked)")
    print("axes shown: " + (", ".join(changed) if changed else "none (no hidden axes found)"))
    return 0




def cmd_frame(args) -> int:
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




def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    mk = sub.add_parser("make", help="write the two verification workbooks")
    mk.add_argument("src", type=Path)
    mk.add_argument("out", type=Path)
    mk.add_argument("--sheets", default="", help="comma-separated worksheet names (default: all)")
    fr = sub.add_parser("frame", help="draw where each sheet sits on the dashboard")
    fr.add_argument("--render", required=True, type=Path, help="clean render of the finished dashboard")
    fr.add_argument("--marked", required=True, type=Path, help="render of the same dashboard in the _Frames workbook")
    fr.add_argument("--zones", required=True, type=Path, help="<out>_Frames.zones.json from make")
    fr.add_argument("--out-dir", required=True, type=Path)
    fr.add_argument("--sheets", default="", help="comma-separated sheet names (default: every marked zone)")
    args = ap.parse_args()
    return cmd_make(args) if args.cmd == "make" else cmd_frame(args)


if __name__ == "__main__":
    sys.exit(main())
