"""Build a starter workbook from a finished WOW workbook.

The starter keeps the sheets handed to participants and removes the rest:
worksheets, their windows/thumbnails, and every calculated field that only the
removed sheets need (decided on the dependency tree). Dashboard zones of the
removed sheets become blank zones of the same size, so the layout keeps its gaps.
Shared filters, colors and formatting stay as they are.

Usage:
  python build_starter.py --twbx <final.twbx> (--keep "A,B" | --remove "C,D")
                          [--out <YYYYWNN_Starter.twbx>] [--dry-run]

--dry-run prints the plan (kept/removed sheets and calcs, blank zones) as JSON
and writes nothing. Without it, the starter .twbx and its .twb are written next
to each other and the same JSON report is printed, with leftover references.
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

# Zone coordinates are in 1/100000 of the dashboard size (Tableau's zone unit)
ZONE_UNIT = 100000
# Element types inside a dashboard that point at a sheet by name besides worksheet zones
SHEET_REF_ATTRS = ("name", "worksheet", "source-sheet", "target-sheet")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--twbx", required=True, help="Finished workbook (.twbx or .twb)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--keep", help="Comma-separated worksheet names handed to participants")
    g.add_argument("--remove", help="Comma-separated worksheet names participants build")
    p.add_argument("--out", help="Output .twbx path (required unless --dry-run)")
    p.add_argument("--dry-run", action="store_true", help="Print the plan only")
    a = p.parse_args()
    if not a.dry_run and not a.out:
        p.error("--out is required unless --dry-run")
    return a


def split_names(s):
    return [n.strip() for n in s.split(",") if n.strip()]


def load(src: Path):
    """Return (twb bytes, twb member name, zip members) from a .twbx or .twb."""
    if src.suffix.lower() == ".twb":
        return src.read_bytes(), src.name, None
    with zipfile.ZipFile(src) as z:
        twbs = [n for n in z.namelist() if n.lower().endswith(".twb") and "/" not in n]
        if len(twbs) != 1:
            sys.exit(f"expected one .twb at the root of {src}, found {twbs}")
        return z.read(twbs[0]), twbs[0], z


def inner(name):
    """'[Calculation_1]' -> 'Calculation_1'."""
    return name[1:-1] if name.startswith("[") and name.endswith("]") else name


def ref_pattern(names):
    """Matches a field's inner name as a bracketed field or inside an instance name
    such as [none:Calculation_1:nk]."""
    alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(r"[\[:](" + alt + r")[\]:]")


def text_of(el):
    return etree.tostring(el, encoding="unicode")


def collect_calcs(root):
    """{inner name: (datasource element, column element)} for calculated fields."""
    calcs = {}
    for ds in root.findall("./datasources/datasource"):
        if ds.get("name") == "Parameters":
            continue  # parameters are left as they are
        for col in ds.findall("./column"):
            if col.find("calculation") is not None:
                calcs[inner(col.get("name"))] = (ds, col)
    return calcs


def used_calcs(root, calcs, kept_sheets, removed_sheets):
    """Calcs reachable from what stays: kept worksheets, dashboards (minus removed
    sheet zones), shared views and actions that do not touch removed sheets."""
    pat = ref_pattern(calcs)
    roots = []
    for ws in root.findall("./worksheets/worksheet"):
        if ws.get("name") in kept_sheets:
            roots.append(text_of(ws))
    for dash in root.findall("./dashboards/dashboard"):
        d = etree.fromstring(text_of(dash))
        for z in list(d.iter("zone")):
            if z.get("name") in removed_sheets and z.get("type-v2") is None:
                z.getparent().remove(z)
        roots.append(text_of(d))
    for tag in ("shared-views", "actions"):
        for el in root.findall(f"./{tag}"):
            roots.append(text_of(el))
    seen = set()
    stack = [m for t in roots for m in pat.findall(t)]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        formula = text_of(calcs[n][1].find("calculation"))
        stack.extend(pat.findall(formula))
    return seen


def remove_sheets(root, removed):
    gone = []
    for path in ("./worksheets/worksheet", "./windows/window", "./thumbnails/thumbnail"):
        for el in root.findall(path):
            if el.get("name") in removed:
                el.getparent().remove(el)
    for vp in list(root.iter("viewpoint")):
        if vp.get("name") in removed:
            vp.getparent().remove(vp)
    # Actions whose source or target is a removed sheet cannot work in the starter
    for act in list(root.iter("action")):
        t = text_of(act)
        if any(f"'{s}'" in t or f'"{s}"' in t for s in removed):
            gone.append(act.get("caption") or act.get("name"))
            act.getparent().remove(act)
    return gone


def remove_calcs(root, calcs, removed_calcs):
    """Drop the calc columns and everything in the datasources that names them
    (column instances, folder items, color encodings, sorts)."""
    if not removed_calcs:
        return
    pat = ref_pattern(removed_calcs)
    for ds in {calcs[n][0] for n in removed_calcs}:
        for el in list(ds.iter()):
            parent = el.getparent()
            if parent is None or el is ds:
                continue
            if el.tag == "column" and inner(el.get("name", "")) in removed_calcs:
                parent.remove(el)
            elif el.tag != "column" and any(pat.search(v) for v in el.attrib.values()):
                parent.remove(el)
    # Dashboard-level datasource-dependencies may still list them
    for dd in root.iter("datasource-dependencies"):
        for el in list(dd):
            if any(pat.search(v) for v in el.attrib.values()):
                dd.remove(el)


def dashboard_px(dash):
    size = dash.find("size")
    if size is None:
        return None, None
    w = size.get("maxwidth") or size.get("minwidth")
    h = size.get("maxheight") or size.get("minheight")
    return (int(w) if w else None), (int(h) if h else None)


def blank_zones(root, removed, kept):
    """Replace runs of adjacent removed-sheet zones with one blank zone each.
    Retarget filter/legend zones that belong to a removed sheet."""
    report, warnings = [], []
    for dash in root.findall("./dashboards/dashboard"):
        width_px, height_px = dashboard_px(dash)
        zones = list(dash.iter("zone"))
        next_id = max((int(z.get("id")) for z in zones if (z.get("id") or "").isdigit()), default=0) + 1

        # Filter / legend / highlighter zones carry the sheet they belong to in name=
        kept_ws = {ws.get("name"): text_of(ws) for ws in root.findall("./worksheets/worksheet") if ws.get("name") in kept}
        for z in zones:
            if z.get("type-v2") is not None and z.get("name") in removed:
                field = z.get("param") or ""
                inst = field.split("].[")[-1].rstrip("]") if field else ""
                target = next((n for n, t in kept_ws.items() if inst and inst in t), None)
                if target:
                    z.set("name", target)
                else:
                    warnings.append(f"zone {z.get('id')} ({z.get('type-v2')}) belongs to removed sheet "
                                    f"'{z.get('name')}' and no kept sheet uses {field or 'its field'}; removed")
                    z.getparent().remove(z)

        parents = {z.getparent() for z in dash.iter("zone") if z.get("name") in removed and z.get("type-v2") is None}
        for parent in parents:
            horizontal = parent.get("param") == "horz"
            run = []
            for child in list(parent) + [None]:
                is_removed = (child is not None and child.tag == "zone"
                              and child.get("name") in removed and child.get("type-v2") is None)
                if is_removed:
                    run.append(child)
                    continue
                if not run:
                    continue
                first = run[0]
                attrs = {k: first.get(k) for k in ("x", "y", "w", "h")}
                if parent.get("type-v2") == "layout-flow":
                    axis = "w" if horizontal else "h"
                    attrs[axis] = str(sum(int(z.get(axis)) for z in run))
                    span_px = width_px if horizontal else height_px
                    blank = {"id": str(next_id), "type-v2": "empty", **attrs}
                    if span_px:
                        blank["fixed-size"] = str(round(int(attrs[axis]) / ZONE_UNIT * span_px))
                        blank["is-fixed"] = "true"
                    el = etree.Element("zone", blank)
                    el.tail = first.tail
                    parent.insert(parent.index(first), el)
                    for z in run:
                        parent.remove(z)
                    report.append({"dashboard": dash.get("name"), "replaces": [z.get("name") for z in run],
                                   "zone": el.get("id"), "fixed_px": el.get("fixed-size"),
                                   "direction": "horz" if horizontal else "vert"})
                    next_id += 1
                else:
                    # Floating or tiled-basic zones: one blank per sheet, same box
                    for z in run:
                        el = etree.Element("zone", {"id": str(next_id), "type-v2": "empty",
                                                    **{k: z.get(k) for k in ("x", "y", "w", "h")}})
                        for k in ("is-floating",):
                            if z.get(k):
                                el.set(k, z.get(k))
                        el.tail = z.tail
                        parent.replace(z, el)
                        report.append({"dashboard": dash.get("name"), "replaces": [z.get("name")],
                                       "zone": el.get("id"), "fixed_px": None, "direction": None})
                        next_id += 1
                run = []
    return report, warnings


def leftovers(xml_text, removed_sheets, removed_calcs):
    left = {}
    if removed_calcs:
        for m in ref_pattern(removed_calcs).findall(xml_text):
            left[m] = left.get(m, 0) + 1
    for s in removed_sheets:
        n = xml_text.count(f"'{s}'") + xml_text.count(f'"{s}"')
        if n:
            left[s] = n
    return left


def main():
    a = parse_args()
    src = Path(a.twbx)
    data, twb_name, _ = load(src)
    root = etree.fromstring(data, etree.XMLParser(remove_blank_text=False, huge_tree=True))

    sheets = [ws.get("name") for ws in root.findall("./worksheets/worksheet")]
    asked = split_names(a.keep or a.remove)
    unknown = [n for n in asked if n not in sheets]
    if unknown:
        sys.exit(f"unknown worksheet(s): {unknown}. Worksheets: {sheets}")
    kept = set(asked) if a.keep else set(sheets) - set(asked)
    removed = set(sheets) - kept

    calcs = collect_calcs(root)
    used = used_calcs(root, calcs, kept, removed)
    removed_calcs = {n for n in calcs if n not in used}

    def caption(n):
        return calcs[n][1].get("caption") or n

    plan = {
        "source": src.name,
        "kept_sheets": [s for s in sheets if s in kept],
        "removed_sheets": [s for s in sheets if s in removed],
        "kept_calcs": sorted(caption(n) for n in used),
        "removed_calcs": sorted(caption(n) for n in removed_calcs),
    }

    removed_actions = remove_sheets(root, removed)
    remove_calcs(root, calcs, removed_calcs)
    blanks, warnings = blank_zones(root, removed, kept)
    # The starter is a new workbook: drop every link to a published copy (workbook,
    # worksheet and dashboard level). They name the Cloud site and would leak into
    # the public starter.
    plan["removed_repository_locations"] = 0
    for rl in list(root.iter("repository-location")):
        rl.getparent().remove(rl)
        plan["removed_repository_locations"] += 1

    out_xml = etree.tostring(root, xml_declaration=True, encoding="utf-8")
    plan.update({"blank_zones": blanks, "removed_actions": removed_actions, "warnings": warnings,
                 "leftover_references": leftovers(out_xml.decode("utf-8"), removed, removed_calcs)})

    if not a.dry_run:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        twb_path = out.with_suffix(".twb")
        twb_path.write_bytes(out_xml)
        member = out.stem + ".twb"
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
            dst.writestr(member, out_xml)
            if src.suffix.lower() == ".twbx":
                with zipfile.ZipFile(src) as z:
                    for info in z.infolist():
                        if info.filename != twb_name and not info.is_dir():
                            dst.writestr(info, z.read(info.filename))
        plan["output"] = {"twbx": str(out), "twb": str(twb_path)}

    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if plan["leftover_references"] or warnings:
        sys.exit(2)


if __name__ == "__main__":
    main()
