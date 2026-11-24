#!/usr/bin/env python3
"""Make the two verification workbooks for walkthrough figures from the finished workbook.

Each keeps everything else, including the packaged data:
1. <out>.twbx, for single-sheet renders: the finished dashboard hides the axes of its sheets, so a
   single-sheet render cannot show where the marks sit. The axis "display = false" formats are
   removed from the chosen worksheets (all by default). Published to Cloud, each worksheet becomes
   a view with its axes and title.
2. <out>_Frames.twbx, for "where is this sheet" figures: every sheet zone on the dashboards gets a
   solid border in a colour of its own, and <out>_Frames.zones.json maps each colour to its sheet.
   Cloud lays a dashboard out again when it renders (zone heights differ from the saved x/y/w/h),
   so frame_context.py finds each sheet by its colour in the render of this dashboard. The axes
   stay hidden here, because shown axes change the height of zones that are not fixed.

The source workbook is never modified.

Usage:
  python make_sheet_views.py <finished.twbx> <out.twbx> [--sheets "Sheet A,Sheet B"]
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--sheets", default="", help="comma-separated worksheet names (default: all)")
    args = ap.parse_args()
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


if __name__ == "__main__":
    sys.exit(main())
