#!/usr/bin/env python3
"""Draft the chapter table of a walkthrough from the spec that extract_twb.py wrote.

One row per sheet, in chapter order. A calc is created in the first sheet that needs it and
reused afterwards. Each row lists the calcs to create, the calcs reused from earlier rows (only
those the sheet's pills or the new calcs reference directly), the dimensions in the view and the
table calcs set in its Edit Table Calculation dialog (nested calcs along specific dimensions).

--order gives the order (decided by Claude, approved by the user). Without it, and for sheets it
leaves out, the dashboard order (top to bottom, left to right) is used.
--given lists sheets the reader receives ready-made (a starter): their calcs count as built and
they get no row.

Usage:
  python plan_chapters.py twb-spec.json [--order "Sheet A,Sheet B"] [--given "Sheet C"] [--md out.md]
"""

import argparse
import json
import sys
from pathlib import Path


def dashboard_rank(spec: dict) -> dict[str, tuple]:
    rank = {}
    for db in spec["dashboards"]:
        for z in db["zones"]:
            if z["type"] == "sheet" and z["name"] and z["name"] not in rank:
                rank[z["name"]] = (z["y_pct"], z["x_pct"])
    return rank


def dialog_calcs(ws: dict) -> list[str]:
    """Nested calcs the reader sets in the dialog: computed along specific dimensions."""
    out = []
    for tc in ws["table_calcs"]:
        for n in tc["nested"]:
            if n["ordering_type"] == "Field":
                label = f"{n['calc']}: {' → '.join(n['order']) or '?'}"
                if label not in out:
                    out.append(label)
    return out


def plan(spec: dict, order: list[str], given: list[str]) -> list[dict]:
    sheets = {ws["name"]: ws for ws in spec["worksheets"]}
    unknown = [s for s in order + given if s not in sheets]
    if unknown:
        raise SystemExit(f"Unknown sheet(s): {unknown}. Sheets: {list(sheets)}")
    rank = dashboard_rank(spec)
    refs = {c["caption"]: c["ref_captions"] for c in spec["calcs"]}
    built: set[str] = set()
    for s in given:
        built |= set(sheets[s]["calcs_needed"])
    rest = sorted((s for s in sheets if s not in given and s not in order), key=lambda s: rank.get(s, (999, 999)))
    chapters = []

    def take(name: str):
        ws = sheets[name]
        new = [c for c in ws["calcs_needed"] if c not in built]
        # Reused = built calcs this chapter touches directly: a pill on the sheet or an input of a new calc.
        direct = {r["calc"] for r in ws["tree"] if r.get("calc")}
        for c in new:
            direct |= set(refs.get(c, []))
        reused = [c for c in ws["calcs_needed"] if c in built and c in direct]
        chapters.append({"sheet": name, "new": new, "reused": reused, "dimensions": ws["dimensions"],
                         "dialog": dialog_calcs(ws), "on_dashboard": name in rank})
        built.update(new)

    for name in list(order) + rest:
        take(name)
    return chapters


def to_markdown(spec: dict, chapters: list[dict], given: list[str]) -> str:
    calcs = {c["caption"]: c for c in spec["calcs"]}
    lines = [f"# 章立ての下書き: {spec['source']}", ""]
    if given:
        lines.append(f"渡すシート（章を立てない）: {', '.join(given)}")
        lines.append("")
    lines += ["| 章 | 作るシート | 作る計算 | 前の章から使う計算 | ディメンション | ダイアログで決める方向 |",
              "|---|---|---|---|---|---|"]
    for i, ch in enumerate(chapters, 1):
        def fmt(names):
            return "・".join(f"`{n}`{'△' if calcs.get(n, {}).get('kind') == 'tc' else ''}" for n in names) or "—"
        sheet = ch["sheet"] + ("" if ch["on_dashboard"] else "（ダッシュボード外）")
        lines.append(f"| {i} | {sheet} | {fmt(ch['new'])} | {fmt(ch['reused'])} | "
                     f"{', '.join(ch['dimensions']) or '—'} | {'<br>'.join(ch['dialog']) or '—'} |")
    lines += ["", "△ = 自分で表計算関数を使う計算。", ""]
    lines.append("## ダッシュボード上の並び（上から）")
    rank = dashboard_rank(spec)
    lines.append(" → ".join(sorted(rank, key=lambda s: rank[s])))
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", type=Path, help="twb-spec.json from extract_twb.py")
    ap.add_argument("--order", default="", help="comma-separated sheet names, in chapter order")
    ap.add_argument("--given", default="", help="comma-separated sheets the reader receives ready-made")
    ap.add_argument("--md", type=Path, help="write the table here instead of stdout")
    ap.add_argument("--json", type=Path, help="also write the chapters as JSON")
    args = ap.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    split = lambda s: [x.strip() for x in s.split(",") if x.strip()]  # noqa: E731
    given = split(args.given)
    chapters = plan(spec, split(args.order), given)
    md = to_markdown(spec, chapters, given)
    if args.json:
        args.json.write_text(json.dumps(chapters, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.md:
        args.md.write_text(md, encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
