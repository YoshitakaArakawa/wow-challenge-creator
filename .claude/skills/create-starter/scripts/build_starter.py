"""Build a starter workbook from a finished WOW workbook.

The starter keeps the sheets handed to participants and removes the rest:
worksheets, their windows/thumbnails, actions that start from them, and every
calculated field that nothing left in the workbook needs (decided on the
dependency tree). Dashboard zones of the removed sheets become blank zones of
the same size, so the layout keeps its gaps. Shared filters, datasource filters,
sets, colors and formatting stay as they are.

Usage:
  python build_starter.py --twbx <final.twbx|final.twb> (--keep "A,B" | --remove "C,D")
                          [--out <YYYYWNN_Starter.twbx>] [--dry-run]

--dry-run prints the plan (kept/removed sheets and calcs, blank zones) as JSON
and writes nothing. Without it, the starter .twbx and its .twb are written next
to each other and the same JSON report is printed. Exit code 2 when the report
has leftover references or warnings.
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

# Zone coordinates are in 1/100000 of the dashboard (or device layout) size
ZONE_UNIT = 100000
# Elements inside a datasource that only describe a field (where it sits in the
# data pane, its color, its instances). They do not make a calc needed, and they
# are deleted together with the calc. Anything else in a datasource that names a
# calc (filters, sets, drill paths, extract filters) keeps the calc alive.
DESCRIPTIVE_TAGS = {"column-instance", "folder-item", "encoding", "map"}
# Attributes that hold a display label, not a reference
LABEL_ATTRS = {"caption", "alias"}
# Matches [Datasource].[field] references
QUALIFIED = re.compile(r"\[([^\[\]]+)\]\.\[([^\[\]]+)\]")


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
    """Return (twb bytes, twb member name) from a .twbx or .twb."""
    if src.suffix.lower() == ".twb":
        return src.read_bytes(), src.name
    with zipfile.ZipFile(src) as z:
        twbs = [n for n in z.namelist() if n.lower().endswith(".twb") and "/" not in n]
        if len(twbs) != 1:
            sys.exit(f"expected one .twb at the root of {src}, found {twbs}")
        return z.read(twbs[0]), twbs[0]


def inner(name):
    """'[Calculation_1]' -> 'Calculation_1'."""
    return name[1:-1] if name.startswith("[") and name.endswith("]") else name


def text_of(el):
    return etree.tostring(el, encoding="unicode")


# ---------------------------------------------------------------- calcs

class Calcs:
    """Calculated fields keyed by (datasource name, inner name)."""

    def __init__(self, root):
        self.cols = {}
        self.ds = {}
        for ds in root.findall("./datasources/datasource"):
            dsn = ds.get("name")
            if dsn == "Parameters":
                continue  # parameters are left as they are
            self.ds[dsn] = ds
            for col in ds.findall("./column"):
                if col.find("calculation") is not None:
                    self.cols[(dsn, inner(col.get("name")))] = col
        self.names = {}
        for dsn, n in self.cols:
            self.names.setdefault(dsn, set()).add(n)

    def caption(self, key):
        return self.cols[key].get("caption") or key[1]

    def pattern(self, dsn):
        """Inner names of dsn's calcs, bare ([X]) or inside an instance ([none:X:nk])."""
        names = self.names.get(dsn)
        if not names:
            return None
        alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
        return re.compile(r"[\[:](" + alt + r")[\]:]")

    def unqualified(self, text, dsn):
        pat = self.pattern(dsn)
        return {(dsn, m) for m in pat.findall(text)} if pat else set()

    def qualified(self, text):
        out = set()
        for dsn, field in QUALIFIED.findall(text):
            names = self.names.get(dsn)
            if not names:
                continue
            if field in names:
                out.add((dsn, field))
            else:
                parts = field.split(":")
                if len(parts) >= 3 and ":".join(parts[1:-1]) in names:
                    out.add((dsn, ":".join(parts[1:-1])))
        return out

    def refs(self, el, default_ds=None):
        """Calcs an element points at: [ds].[field] anywhere, plus bare names inside
        <datasource-dependencies datasource=...> blocks (or default_ds)."""
        out = self.qualified(text_of(el))
        if default_ds:
            out |= self.unqualified(text_of(el), default_ds)
        for dd in el.iter("datasource-dependencies"):
            out |= self.unqualified(text_of(dd), dd.get("datasource"))
        return out

    def closure(self, start):
        seen, stack = set(), list(start)
        while stack:
            key = stack.pop()
            if key in seen or key not in self.cols:
                continue
            seen.add(key)
            stack.extend(self.refs(self.cols[key].find("calculation"), default_ds=key[0]))
        return seen


def used_calcs(root, calcs):
    """Calcs reachable from everything left after the sheets were removed."""
    start = set()
    for tag in ("worksheets", "dashboards", "shared-views", "actions"):
        for el in root.findall(f"./{tag}"):
            start |= calcs.refs(el)
    for dsn, ds in calcs.ds.items():
        for child in ds:
            if child.tag == "column" and child.find("calculation") is not None:
                continue  # a calc counts only when something reaches it
            for el in child.iter():
                if el.tag in DESCRIPTIVE_TAGS:
                    continue
                if el is child or el.getparent().tag not in DESCRIPTIVE_TAGS:
                    start |= calcs.unqualified(" ".join(el.attrib.values()) + " " + (el.text or ""), dsn)
    return calcs.closure(start)


def remove_calcs(calcs, removed):
    """Delete removed calcs and the descriptive elements that name them."""
    by_ds = {}
    for dsn, n in removed:
        by_ds.setdefault(dsn, set()).add(n)
    for dsn, names in by_ds.items():
        alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
        pat = re.compile(r"[\[:](" + alt + r")[\]:]")
        for n in names:
            col = calcs.cols[(dsn, n)]
            col.getparent().remove(col)
        for el in list(calcs.ds[dsn].iter(*DESCRIPTIVE_TAGS)):
            if el.getparent() is not None and any(pat.search(v) for v in el.attrib.values()):
                el.getparent().remove(el)


# ---------------------------------------------------------------- sheets and actions

def names_in(value):
    return [v.strip() for v in value.split(",")]


def remove_sheets(root, removed):
    for path in ("./worksheets/worksheet", "./windows/window", "./thumbnails/thumbnail"):
        for el in root.findall(path):
            if el.get("name") in removed:
                el.getparent().remove(el)
    for vp in list(root.iter("viewpoint")):
        if vp.get("name") in removed:
            vp.getparent().remove(vp)


def fix_actions(root, removed):
    """Drop actions that start from or point at a removed sheet. Exclusion lists
    only lose the removed names."""
    dropped, edited = [], []
    for act in list(root.iter("action")):
        label = act.get("caption") or act.get("name")
        drop = False
        for el in list(act.iter()):
            if el is act:
                continue
            if el.tag == "exclude-sheet":
                if el.get("name") in removed:
                    el.getparent().remove(el)
                    edited.append(label)
                continue
            for k, v in list(el.attrib.items()):
                items = names_in(v)
                hit = [i for i in items if i in removed]
                if not hit or k in LABEL_ATTRS:
                    continue
                is_exclude = el.tag == "param" and "exclude" in (el.get("name") or "")
                if is_exclude and k == "value":
                    rest = [i for i in items if i not in removed]
                    if rest:
                        el.set(k, ",".join(rest))
                    else:
                        el.getparent().remove(el)
                    edited.append(label)
                else:
                    drop = True
        if drop:
            dropped.append(label)
            act.getparent().remove(act)
    return dropped, sorted(set(edited) - set(dropped))


# ---------------------------------------------------------------- dashboards

def layout_px(zone):
    """(width px, height px) of the dashboard or device layout a zone belongs to.
    None on an axis whose size is not fixed (automatic, range, scrolling)."""
    node = zone.getparent()
    while node is not None and node.find("size") is None:
        node = node.getparent()
    size = node.find("size") if node is not None else None
    if size is None:
        return None, None

    def fixed(lo, hi):
        a, b = size.get(lo), size.get(hi)
        return int(b) if a and b and a == b else None

    w = fixed("minwidth", "maxwidth")
    h = fixed("minheight", "maxheight")
    return w, h


def is_sheet_zone(z, removed):
    return z.tag == "zone" and z.get("name") in removed and z.get("type-v2") is None


def blank_zones(root, removed, kept):
    """Retarget filter/legend zones of removed sheets, then replace runs of
    adjacent removed-sheet zones with one fixed blank zone each."""
    report, warnings = [], []
    kept_ws = {ws.get("name"): text_of(ws) for ws in root.findall("./worksheets/worksheet")
               if ws.get("name") in kept}
    for dash in root.findall("./dashboards/dashboard"):
        ids = [int(z.get("id")) for z in dash.iter("zone") if (z.get("id") or "").isdigit()]
        next_id = max(ids, default=0) + 1

        for z in list(dash.iter("zone")):
            if z.get("type-v2") is not None and z.get("name") in removed:
                field = z.get("param") or ""
                inst = field.split("].[")[-1].rstrip("]") if field else ""
                target = next((n for n, t in kept_ws.items() if inst and inst in t), None)
                if target:
                    z.set("name", target)
                else:
                    warnings.append(f"zone {z.get('id')} ({z.get('type-v2')}) of removed sheet "
                                    f"'{z.get('name')}': no kept sheet uses {field or 'its field'}; removed")
                    z.getparent().remove(z)

        parents = {z.getparent() for z in dash.iter("zone") if is_sheet_zone(z, removed)}
        for parent in parents:
            horizontal = parent.get("param") == "horz"
            flow = parent.get("type-v2") == "layout-flow"
            run = []
            for child in list(parent) + [None]:
                if child is not None and is_sheet_zone(child, removed):
                    run.append(child)
                    if flow:
                        continue
                if not run:
                    continue
                first = run[0]
                attrs = {k: first.get(k) for k in ("x", "y", "w", "h")}
                if first.get("is-floating"):
                    attrs["is-floating"] = first.get("is-floating")
                fixed_px = None
                if flow:
                    # One fixed blank as large as the run was in the saved layout.
                    # A flexible blank would not take the same share of the leftover
                    # space as a sheet does, so the kept sheets would move
                    axis = "w" if horizontal else "h"
                    attrs[axis] = str(sum(int(z.get(axis)) for z in run))
                    span = layout_px(first)[0 if horizontal else 1]
                    if span:
                        fixed_px = round(int(attrs[axis]) / ZONE_UNIT * span)
                    else:
                        warnings.append(f"blank zone for {[z.get('name') for z in run]}: layout size is not "
                                        "fixed, so the blank is not fixed either and may change size")
                el = etree.Element("zone", {"id": str(next_id), "type-v2": "empty", **attrs})
                if fixed_px is not None:
                    el.set("fixed-size", str(fixed_px))
                    el.set("is-fixed", "true")
                el.tail = first.tail
                parent.insert(parent.index(first), el)
                for z in run:
                    parent.remove(z)
                device = next((a.get("name") for a in el.iterancestors("devicelayout")), None)
                report.append({"dashboard": dash.get("name"), "device_layout": device,
                               "replaces": [z.get("name") for z in run], "zone": el.get("id"),
                               "fixed_px": fixed_px, "direction": ("horz" if horizontal else "vert") if flow else None,
                               "had_flexible_sheet": any(z.get("is-fixed") != "true" for z in run)})
                next_id += 1
                run = []
    return report, warnings


# ---------------------------------------------------------------- report

def leftovers(root, calcs, removed_sheets, removed_calcs):
    """References to removed sheets or calcs that are still in the starter."""
    left = {}
    remaining = Calcs(root)
    gone = {}
    for dsn, n in removed_calcs:
        if n not in remaining.names.get(dsn, set()):
            gone.setdefault(dsn, set()).add(n)
    for dsn, names in gone.items():
        alt = "|".join(re.escape(n) for n in names)
        pat = re.compile(r"\[" + re.escape(dsn) + r"\]\.\[(?:[^\]:]*:)?(" + alt + r")[\]:]")
        for m in pat.findall(text_of(root)):
            left[m] = left.get(m, 0) + 1
        bare = re.compile(r"[\[:](" + alt + r")[\]:]")
        for dd in root.iter("datasource-dependencies"):
            if dd.get("datasource") == dsn:
                for m in bare.findall(text_of(dd)):
                    left[m] = left.get(m, 0) + 1
        if dsn in remaining.ds:
            for m in bare.findall(text_of(remaining.ds[dsn])):
                left[m] = left.get(m, 0) + 1
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        for k, v in el.attrib.items():
            if k not in LABEL_ATTRS and any(i in removed_sheets for i in names_in(v)):
                left[v] = left.get(v, 0) + 1
        for s in removed_sheets:
            if el.text and (f'"{s}"' in el.text or f"'{s}'" in el.text):
                left[s] = left.get(s, 0) + 1
    return left


def main():
    a = parse_args()
    src = Path(a.twbx)
    data, twb_name = load(src)
    root = etree.fromstring(data, etree.XMLParser(remove_blank_text=False, huge_tree=True))

    sheets = [ws.get("name") for ws in root.findall("./worksheets/worksheet")]
    asked = split_names(a.keep or a.remove)
    unknown = [n for n in asked if n not in sheets]
    if unknown:
        sys.exit(f"unknown worksheet(s): {unknown}. Worksheets: {sheets}")
    kept = set(asked) if a.keep else set(sheets) - set(asked)
    removed = set(sheets) - kept

    # Sheets, actions and dashboard zones go first, so the calcs that only they
    # needed are no longer reachable
    calcs = Calcs(root)
    all_calcs = set(calcs.cols)
    blanks, warnings = blank_zones(root, removed, kept)
    dropped_actions, edited_actions = fix_actions(root, removed)
    remove_sheets(root, removed)
    used = used_calcs(root, calcs)
    removed_calcs = all_calcs - used
    plan = {
        "source": src.name,
        "kept_sheets": [s for s in sheets if s in kept],
        "removed_sheets": [s for s in sheets if s in removed],
        "kept_calcs": sorted(calcs.caption(k) for k in used),
        "removed_calcs": sorted(calcs.caption(k) for k in removed_calcs),
        "blank_zones": blanks,
        "removed_actions": dropped_actions,
        "edited_actions": edited_actions,
    }
    if len(calcs.ds) > 1:
        plan["removed_calcs_by_datasource"] = {
            dsn: sorted(calcs.caption(k) for k in removed_calcs if k[0] == dsn) for dsn in calcs.ds}
    remove_calcs(calcs, removed_calcs)

    # The starter is a new workbook: drop every link to a published copy. They
    # name the Cloud site and would leak into the public starter.
    rl = list(root.iter("repository-location"))
    for el in rl:
        el.getparent().remove(el)
    plan["removed_repository_locations"] = len(rl)
    plan["warnings"] = warnings
    plan["leftover_references"] = leftovers(root, calcs, removed, removed_calcs)

    out_xml = etree.tostring(root, xml_declaration=True, encoding="utf-8")
    if not a.dry_run:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        twb_path = out.with_suffix(".twb")
        # Re-running on the starter's own .twb (after a manual fix) must not clobber the input first
        if twb_path.resolve() != src.resolve():
            twb_path.write_bytes(out_xml)
        member = out.stem + ".twb"
        extras = []
        if src.suffix.lower() == ".twbx":
            with zipfile.ZipFile(src) as z:
                extras = [(i, z.read(i.filename)) for i in z.infolist()
                          if i.filename != twb_name and not i.is_dir()]
        elif out.exists():
            with zipfile.ZipFile(out) as z:  # keep the data of an earlier build
                extras = [(i, z.read(i.filename)) for i in z.infolist()
                          if not i.filename.lower().endswith(".twb") and not i.is_dir()]
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
            dst.writestr(member, out_xml)
            for info, body in extras:
                dst.writestr(info, body)
        plan["output"] = {"twbx": out.as_posix(), "twb": twb_path.as_posix()}

    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if plan["leftover_references"] or warnings:
        sys.exit(2)


if __name__ == "__main__":
    main()
