#!/usr/bin/env python3
"""Extract what a walkthrough needs from a finished Tableau workbook (.twb or .twbx).

Reads the workbook XML and writes a JSON spec plus a compact Markdown summary:
- data sources: connections, tables, relationship expressions, data files inside the .twbx
- calculated fields: caption, readable formula, kind (row / agg / tc / tc-derived / lod), references,
  the sheets that need it
- parameters
- worksheets: mark type, Rows/Columns pills, Marks-card encodings (in card order),
  nested table-calc settings per pill (ordering-type and the fields in order), sorts, filters,
  fixed axes, hidden headers, mark opacity, custom labels,
  pane formats (mark colour, borders, label colour), the dimensions in the view,
  the component tree (pill or sort -> calcs it references, recursively)
  and the calcs the sheet needs, leaves first
- data-source-wide filters (filters applied to all sheets that use the data source)
- elements listed but not interpreted: reference lines, sets and groups, dashboard actions, extensions
- color assignments
- dashboards: size and every zone with its share of the dashboard width/height

Usage:
  python extract_twb.py <workbook.twb|.twbx> [--json out.json] [--md out.md]
Without --md the Markdown summary goes to stdout.
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

# Tableau zone coordinates are expressed in 1/100000 of the dashboard.
ZONE_UNITS = 100000
# mark-transparency is an alpha byte: 255 = opaque, 128 = 50 %.
ALPHA_MAX = 255

TC_FUNCS = {
    "TOTAL", "INDEX", "FIRST", "LAST", "SIZE", "LOOKUP", "PREVIOUS_VALUE",
    "RANK", "RANK_DENSE", "RANK_MODIFIED", "RANK_PERCENTILE", "RANK_UNIQUE",
}
TC_PREFIXES = ("RUNNING_", "WINDOW_", "SCRIPT_", "MODEL_")
AGG_FUNCS = {
    "SUM", "AVG", "MIN", "MAX", "COUNT", "COUNTD", "MEDIAN", "ATTR", "STDEV", "STDEVP",
    "VAR", "VARP", "PERCENTILE", "COLLECT", "CORR", "COVAR", "COVARP",
}
# MIN/MAX with two or more arguments compare values row by row instead of aggregating.
ROW_WHEN_MULTI_ARG = {"MIN", "MAX"}

DERIVATION_LABEL = {
    "none": None, "usr": None, "sum": "SUM", "avg": "AVG", "min": "MIN", "max": "MAX",
    "cnt": "CNT", "ctd": "CNTD", "med": "MEDIAN", "attr": "ATTR", "stdev": "STDEV",
    "var": "VAR", "yr": "YEAR", "qr": "QUARTER", "mn": "MONTH", "wk": "WEEK", "dy": "DAY",
    "tyr": "YEAR", "tqr": "QUARTER", "tmn": "MONTH", "twk": "WEEK", "tdy": "DAY",
}
# Labels of the "Compute Using" choice that ordering-type stores.
ORDERING_LABEL = {
    "Field": "特定のディメンション",
    "Rows": "表（下）",
    "Columns": "表（横）",
    "Table": "表（横、下）",
    "Cell": "セル",
}
# Pane formats that a reader does not need to set by hand.
PANE_STYLE_SKIP = {"mark-labels-show", "mark-labels-cull", "aspect", "size", "mark-labels-mode"}
ENCODING_SHELF = {
    "color": "Color", "size": "Size", "text": "Label", "lod": "Detail", "tooltip": "Tooltip",
    "path": "Path", "shape": "Shape", "wedge-size": "Angle", "geometry": "Geometry",
}

INSTANCE_RE = re.compile(r"\[(?:(?P<ds>[^\]]+)\]\.\[)?(?P<deriv>[a-z]+):(?P<name>.+?):(?P<type>[noq]k)(?::\d+)?\]")
FIELD_REF_RE = re.compile(r"\[([^\[\]]+)\]")
FUNC_RE = re.compile(r"\b([A-Z_]+)\s*\(", re.IGNORECASE)


def read_workbook(path: Path) -> tuple[ET.Element, list[str]]:
    if path.suffix.lower() == ".twbx":
        with zipfile.ZipFile(path) as z:
            twbs = [n for n in z.namelist() if n.lower().endswith(".twb") and "/" not in n.strip("/")]
            if not twbs:
                twbs = [n for n in z.namelist() if n.lower().endswith(".twb")]
            if not twbs:
                raise SystemExit(f"No .twb inside {path.name}")
            data_files = [n for n in z.namelist() if not n.lower().endswith(".twb") and not n.endswith("/")]
            return ET.fromstring(z.read(twbs[0])), data_files
    return ET.parse(path).getroot(), []


def strip_brackets(name: str) -> str:
    return name[1:-1] if name.startswith("[") and name.endswith("]") else name


def strip_comments_and_strings(formula: str) -> str:
    out = re.sub(r"//[^\n]*", "", formula)
    out = re.sub(r"'(?:[^']|'')*'", "''", out)
    return re.sub(r'"(?:[^"]|"")*"', '""', out)


def strip_lod_bodies(code: str) -> str:
    """Remove {...} LOD bodies so aggregations inside them do not count as the outer level."""
    out, depth = [], 0
    for ch in code:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def top_level_arg_count(code: str, open_idx: int) -> int:
    depth, args = 0, 1
    for ch in code[open_idx:]:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return args
        elif ch == "," and depth == 1:
            args += 1
    return args


def own_function_kinds(formula: str) -> set[str]:
    code = strip_comments_and_strings(formula)
    kinds = set()
    if re.search(r"\{\s*(FIXED|INCLUDE|EXCLUDE)\b", code, re.IGNORECASE) or re.search(r"\{\s*(SUM|AVG|MIN|MAX|COUNT)", code, re.IGNORECASE):
        kinds.add("lod")
    outer = strip_lod_bodies(code)
    for m in FUNC_RE.finditer(outer):
        fn = m.group(1).upper()
        if fn in TC_FUNCS or fn.startswith(TC_PREFIXES):
            kinds.add("tc")
        elif fn in AGG_FUNCS:
            if fn in ROW_WHEN_MULTI_ARG and top_level_arg_count(outer, m.end() - 1) > 1:
                continue
            kinds.add("agg")
    return kinds


class Workbook:
    def __init__(self, root: ET.Element, data_files: list[str]):
        self.root = root
        self.data_files = data_files
        self.captions: dict[str, str] = {}      # internal name -> caption
        self.calcs: dict[str, dict] = {}
        self.params: list[dict] = []
        self.datasources: list[dict] = []
        self.colors: list[dict] = []
        self._collect_datasources()

    # ----- naming -----
    def caption(self, name: str) -> str:
        return self.captions.get(strip_brackets(name), strip_brackets(name))

    def readable(self, formula: str) -> str:
        def repl(m):
            inner = m.group(1)
            return f"[{self.captions.get(inner, inner)}]"
        text = re.sub(r"\[Parameters\]\.", "", formula)
        return FIELD_REF_RE.sub(repl, text).replace("\r\n", "\n").replace("\r", "\n")

    def pill(self, instance: str) -> dict:
        m = INSTANCE_RE.search(instance)
        if not m:
            # Instances outside the derivation:name:type form, e.g. [ds].[:Measure Names].
            name = instance.rsplit("].[", 1)[-1].strip("[]").lstrip(":")
            return {"label": name, "field": self.caption(name), "raw": instance}
        name, deriv = m.group("name"), m.group("deriv")
        cap = self.caption(name)
        agg = DERIVATION_LABEL.get(deriv, deriv.upper())
        calc = self.calcs.get(name)
        kind = calc.get("kind") if calc else None
        return {
            "label": f"{agg}({cap})" if agg else cap,
            "field": cap,
            "derivation": deriv,
            "continuous": m.group("type") == "qk",
            "table_calc": kind in ("tc", "tc-derived"),
            "raw": instance,
        }

    def pills(self, shelf_text: str | None) -> list[dict]:
        if not shelf_text:
            return []
        return [self.pill(m.group(0)) for m in INSTANCE_RE.finditer(shelf_text)]

    # ----- data sources and calcs -----
    def _collect_datasources(self):
        ds_nodes = self.root.findall("./datasources/datasource")
        for ds in ds_nodes:
            for col in ds.findall("column"):
                if col.get("caption"):
                    self.captions[strip_brackets(col.get("name", ""))] = col.get("caption")
        # Ad-hoc calcs typed on a shelf (e.g. INDEX()) are defined only inside the worksheet.
        for col in self.root.iter("column"):
            if col.get("caption"):
                self.captions.setdefault(strip_brackets(col.get("name", "")), col.get("caption"))
        for ds in ds_nodes:
            if ds.get("name") == "Parameters":
                for col in ds.findall("column"):
                    calc = col.find("calculation")
                    self.params.append({
                        "caption": col.get("caption") or strip_brackets(col.get("name", "")),
                        "datatype": col.get("datatype"),
                        "value": calc.get("formula") if calc is not None else col.get("value"),
                        "domain": col.get("param-domain-type"),
                        "members": [m.get("value") for m in col.findall("./members/member")],
                    })
                continue
            self.datasources.append(self._datasource_info(ds))
            for col in ds.findall("column"):
                calc = col.find("calculation")
                if calc is None or calc.get("class") not in (None, "tableau") or calc.get("formula") is None:
                    continue
                name = strip_brackets(col.get("name", ""))
                self.calcs[name] = {
                    "id": name,
                    "caption": col.get("caption") or name,
                    "datatype": col.get("datatype"),
                    "role": col.get("role"),
                    "default_format": col.get("default-format"),
                    "formula_raw": calc.get("formula"),
                    "own": sorted(own_function_kinds(calc.get("formula"))),
                    "refs": [r for r in dict.fromkeys(FIELD_REF_RE.findall(calc.get("formula")))],
                }
        for c in self.calcs.values():
            c["formula"] = self.readable(c.pop("formula_raw"))
            c["refs"] = [r for r in c["refs"] if r in self.calcs]
        for c in self.calcs.values():
            c["kind"] = self._kind(c["id"], set())
            c["ref_captions"] = [self.calcs[r]["caption"] for r in c["refs"]]
        used_by = {k: [] for k in self.calcs}
        for c in self.calcs.values():
            for r in c["refs"]:
                used_by[r].append(c["caption"])
        for k, c in self.calcs.items():
            c["used_by"] = used_by[k]
        for ds in ds_nodes:
            if ds.get("name") != "Parameters":
                self._collect_colors(ds)

    def _kind(self, name: str, seen: set) -> str:
        """tc: own table-calc function. tc-derived: no own table calc but builds on one.
        lod: LOD expression at the outer level. agg: aggregates (directly or via a calc). row: row level."""
        c = self.calcs[name]
        if "tc" in c["own"]:
            return "tc"
        seen = seen | {name}
        ref_kinds = {self._kind(r, seen) for r in c["refs"] if r not in seen}
        if ref_kinds & {"tc", "tc-derived"}:
            return "tc-derived"
        if "agg" in c["own"] or "agg" in ref_kinds:
            return "agg"
        if "lod" in c["own"]:
            return "lod"
        return "row"

    def _datasource_info(self, ds: ET.Element) -> dict:
        conns = [{
            "caption": nc.get("caption"),
            "class": (nc.find("connection").get("class") if nc.find("connection") is not None else None),
            "file": (Path(nc.find("connection").get("filename", "")).name if nc.find("connection") is not None else None) or None,
        } for nc in ds.findall("./connection/named-connections/named-connection")]
        tables = list(dict.fromkeys(r.get("name") for r in ds.iter("relation") if r.get("type") == "table"))
        rels = []
        for rel in ds.findall("./object-graph/relationships/relationship"):
            expr = rel.find("expression")
            ends = [rel.find("first-end-point"), rel.find("second-end-point")]
            rels.append({
                "expression": self._expr(expr) if expr is not None else None,
                "between": [self._object_caption(ds, e.get("object-id")) for e in ends if e is not None],
            })
        joins = []
        for r in ds.iter("relation"):
            if r.get("type") == "join":
                clause = r.find("./clause/expression")
                joins.append({"join": r.get("join"), "on": self._expr(clause) if clause is not None else None})
        return {"caption": ds.get("caption") or ds.get("name"), "connections": conns, "tables": tables,
                "relationships": rels, "joins": joins}

    @staticmethod
    def _object_caption(ds: ET.Element, object_id: str | None) -> str | None:
        for obj in ds.findall("./object-graph/objects/object"):
            if obj.get("id") == object_id:
                return obj.get("caption") or object_id
        return object_id

    def _expr(self, e: ET.Element) -> str:
        kids = list(e.findall("expression"))
        op = e.get("op", "")
        if len(kids) == 2:
            return f"{self._expr(kids[0])} {op} {self._expr(kids[1])}"
        if kids:
            return f"{op}({', '.join(self._expr(k) for k in kids)})"
        return self.readable(op)

    def _collect_colors(self, node: ET.Element, sheet: str | None = None):
        for enc in node.findall("./style/style-rule/encoding"):
            if enc.get("attr") != "color":
                continue
            mapping = []
            for m in enc.findall("map"):
                for b in m.findall("bucket"):
                    mapping.append({"value": (b.text or "").strip('"'), "color": m.get("to")})
            entry = {"field": self.pill(enc.get("field", ""))["field"] if INSTANCE_RE.search(enc.get("field", "")) else enc.get("field"),
                     "palette": enc.get("palette"), "map": mapping}
            if sheet:
                entry["sheet"] = sheet
            self.colors.append(entry)

    # ----- worksheets -----
    def worksheets(self) -> list[dict]:
        out = []
        for ws in self.root.findall("./worksheets/worksheet"):
            table = ws.find("table")
            view = table.find("view")
            info = {
                "name": ws.get("name"),
                "rows": self.pills(table.findtext("rows")),
                "cols": self.pills(table.findtext("cols")),
                "panes": [],
                "table_calcs": [],
                "sorts": [],
                "filters": [],
                "axes": [],
                "hidden_headers": [],
                "format": [],
            }
            for pane in table.findall("./panes/pane"):
                mark = pane.find("mark")
                p = {"id": pane.get("id"), "y_axis": pane.get("y-axis-name"), "x_axis": pane.get("x-axis-name"),
                     "mark": mark.get("class") if mark is not None else None, "encodings": []}
                enc_root = pane.find("encodings")
                for enc in (list(enc_root) if enc_root is not None else []):
                    shelf = ENCODING_SHELF.get(enc.tag, enc.tag)
                    if enc.tag == "text" and p["mark"] == "Text":
                        shelf = "Text"
                    p["encodings"].append({"shelf": shelf, **self.pill(enc.get("column", ""))})
                p["style"] = {}
                for rule in pane.findall("./style/style-rule"):
                    for fmt in rule.findall("format"):
                        attr = fmt.get("attr")
                        if attr == "mark-transparency":
                            p["opacity_pct"] = round(int(fmt.get("value")) / ALPHA_MAX * 100)
                        elif attr not in PANE_STYLE_SKIP:
                            p["style"][f"{rule.get('element')}.{attr}"] = fmt.get("value")
                label = pane.find("customized-label")
                if label is not None:
                    p["custom_label"] = self._runs(label)
                info["panes"].append(p)
            deps = view.find("datasource-dependencies") if view is not None else None
            for inst in (deps.findall("column-instance") if deps is not None else []):
                tcs = inst.findall("table-calc")
                if not tcs:
                    continue
                pill = self.pill(inst.get("name", ""))
                nested = []
                for tc in tcs:
                    fld = tc.get("field")
                    calc_id = strip_brackets(fld.split("].[")[-1].strip("[]")) if fld else None
                    if calc_id is None:
                        m = INSTANCE_RE.search(inst.get("name", ""))
                        calc_id = m.group("name") if m else None
                    # Several fields are stored as <order> children; a single field as the ordering-field attribute.
                    order = [self.pill(o.get("field", ""))["field"] for o in tc.findall("order")]
                    if not order and tc.get("ordering-field"):
                        order = [self.pill(tc.get("ordering-field"))["field"]]
                    nested.append({
                        # A quick table calc on a pill has an internal id but no calc of its own: show the pill.
                        "calc": self.caption(calc_id) if calc_id in self.calcs or calc_id in self.captions else pill["label"],
                        "kind": self.calcs[calc_id]["kind"] if calc_id in self.calcs else None,
                        "outer": fld is None,
                        "ordering_type": tc.get("ordering-type"),
                        "compute_using": ORDERING_LABEL.get(tc.get("ordering-type"), tc.get("ordering-type")),
                        "order": order,
                        **{k: v for k, v in tc.attrib.items() if k not in ("field", "ordering-type", "ordering-field")},
                    })
                info["table_calcs"].append({"pill": pill["label"], "nested": nested})
            for s in (view.findall("manual-sort") if view is not None else []):
                info["sorts"].append({"kind": "manual", "field": self.pill(s.get("column", ""))["field"],
                                      "order": [(b.text or "").strip('"') for b in s.iter("bucket")]})
            for s in (view.findall("computed-sort") if view is not None else []):
                info["sorts"].append({"kind": "computed", "field": self.pill(s.get("column", ""))["field"],
                                      "direction": s.get("direction"), "using": self.pill(s.get("using", ""))["label"],
                                      "using_raw": s.get("using", "")})
            for s in (view.findall("natural-sort") if view is not None else []):
                info["sorts"].append({"kind": "natural", "field": self.pill(s.get("column", ""))["field"],
                                      "direction": s.get("direction")})
            for f in (view.findall("filter") if view is not None else []):
                members = [g.get("member", "").strip('"') for g in f.iter("groupfilter") if g.get("function") == "member"]
                info["filters"].append({
                    "field": self.pill(f.get("column", ""))["field"], "class": f.get("class"), "raw": f.get("column", ""),
                    "filter_group": f.get("filter-group"),
                    "saved_members": members, "min": f.findtext("min"), "max": f.findtext("max"),
                })
            for rule in table.findall("./style/style-rule"):
                for enc in rule.findall("encoding"):
                    if enc.get("type") == "space" and enc.get("range-type") == "fixed":
                        info["axes"].append({"field": self.pill(enc.get("field", ""))["label"], "scope": enc.get("scope"),
                                             "min": enc.get("min"), "max": enc.get("max"),
                                             "reversed": enc.get("reverse") == "true"})
                for fmt in rule.findall("format"):
                    if fmt.get("attr") == "display" and fmt.get("value") == "false":
                        info["hidden_headers"].append({"element": rule.get("element"),
                                                       "field": self.pill(fmt.get("field", ""))["label"] if fmt.get("field") else None})
                    elif fmt.get("attr") in ("line-visibility", "stroke-size"):
                        info["format"].append({"element": rule.get("element"), fmt.get("attr"): fmt.get("value")})
            self._collect_colors(table, ws.get("name"))
            self._add_tree(info)
            out.append(info)
        return out

    # ----- per-sheet component tree -----
    def _calc_node(self, calc_id: str, seen: frozenset) -> dict:
        c = self.calcs[calc_id]
        node = {"calc": c["caption"], "kind": c["kind"], "children": []}
        if calc_id in seen:  # a cycle cannot happen in Tableau, but stay safe
            return node
        for r in c["refs"]:
            node["children"].append(self._calc_node(r, seen | {calc_id}))
        return node

    def _add_tree(self, info: dict):
        """Roots = every pill on Columns, Rows and the Marks card. Children = the calcs each one references."""
        roots, dims = [], []
        shelves = [("Columns", p) for p in info["cols"]] + [("Rows", p) for p in info["rows"]]
        for pane in info["panes"]:
            shelves += [(e["shelf"], e) for e in pane["encodings"]]
        seen_roots = set()
        for shelf, p in shelves:
            m = INSTANCE_RE.search(p.get("raw", ""))
            name = m.group("name") if m else None
            key = (shelf, p.get("label"))
            if key in seen_roots:
                continue
            seen_roots.add(key)
            root = {"shelf": shelf, "label": p.get("label"), "continuous": p.get("continuous"),
                    "table_calc": p.get("table_calc"), "children": []}
            if name in self.calcs:
                root.update(self._calc_node(name, frozenset()))
                root["label"] = p.get("label")
            roots.append(root)
            if p.get("derivation") == "none" and p.get("field") not in dims:
                dims.append(p.get("field"))
        for flt in info["filters"]:
            m = INSTANCE_RE.search(flt.get("raw") or "")
            if m and m.group("name") in self.calcs:
                root = {"shelf": "Filter", "label": flt["field"], "children": []}
                root.update(self._calc_node(m.group("name"), frozenset()))
                roots.append(root)
            elif (flt.get("raw") or "").endswith(":Measure Names]"):
                for member in flt["saved_members"]:
                    mm = INSTANCE_RE.search(member)
                    if mm and mm.group("name") in self.calcs:
                        root = {"shelf": "Measure Values", "label": self.pill(member)["label"], "children": []}
                        root.update(self._calc_node(mm.group("name"), frozenset()))
                        root["label"] = self.pill(member)["label"]
                        roots.append(root)
        for srt in info["sorts"]:
            m = INSTANCE_RE.search(srt.get("using_raw") or "")
            if m and m.group("name") in self.calcs:
                root = {"shelf": f"Sort {srt['field']}", "label": srt["using"], "children": []}
                root.update(self._calc_node(m.group("name"), frozenset()))
                root["label"] = srt["using"]
                roots.append(root)
        info["tree"] = roots
        info["dimensions"] = dims
        needed: list[str] = []

        def post(n: dict):
            for ch in n.get("children", []):
                post(ch)
            if n.get("calc") and n["calc"] not in needed:
                needed.append(n["calc"])

        for r in roots:
            post(r)
        info["calcs_needed"] = needed  # leaves first: the order a reader would create them

    # ----- elements listed but not interpreted -----
    def other_elements(self) -> list[dict]:
        """Things a reader must build that this script does not model: reference lines, sets and
        groups, dashboard actions, extensions. Listed so that no part of the workbook goes unseen."""
        out = []
        for ws in self.root.findall("./worksheets/worksheet"):
            for rl in ws.iter("reference-line"):
                out.append({"kind": "reference line", "where": ws.get("name"),
                            "detail": f"axis {self.pill(rl.get('axis-column', ''))['label']}, "
                                      f"{rl.get('formula')} of {self.pill(rl.get('value-column', ''))['label'] if rl.get('value-column') else '(axis)'}, "
                                      f"scope {rl.get('scope')}"})
            for el in ws.iter():
                if el.tag.endswith("add-in") and el.get("add-in-id"):
                    out.append({"kind": "viz extension", "where": ws.get("name"), "detail": el.get("add-in-id")})
        for ds in self.root.findall("./datasources/datasource"):
            for g in ds.findall("group"):
                if g.get("user:auto-column") == "sheet_link" or g.get("{http://www.tableausoftware.com/xml/user}auto-column") == "sheet_link":
                    continue  # created automatically by a filter action
                out.append({"kind": "set / group", "where": ds.get("caption") or ds.get("name"),
                            "detail": g.get("caption") or strip_brackets(g.get("name", ""))})
        for act in self.root.findall("./actions/*"):
            src = act.find("source")
            out.append({"kind": f"action ({act.tag})", "where": (src.get("worksheet") or src.get("dashboard")) if src is not None else None,
                        "detail": act.get("caption")})
        return out

    # ----- data-source-wide filters -----
    def datasource_filters(self) -> list[dict]:
        """Filters applied to every sheet that uses the data source (Apply to Worksheets > All Using This Data Source)."""
        out = []
        for sv in self.root.findall("./shared-views/shared-view"):
            for f in sv.findall("filter"):
                gf = f.find("groupfilter")
                members = [g.get("member", "").strip('"') for g in f.iter("groupfilter") if g.get("function") == "member"]
                out.append({
                    "field": self.pill(f.get("column", ""))["field"],
                    "class": f.get("class"),
                    "all": gf is not None and gf.get("function") == "level-members",
                    "saved_members": members,
                })
        return out

    def _runs(self, node: ET.Element) -> str:
        text = "".join(r.text or "" for r in node.iter("run"))
        text = text.replace("Æ\n", "\n").replace("Æ", "")
        return INSTANCE_RE.sub(lambda m: self.pill(m.group(0))["label"], text).replace("<[", "<").replace("]>", ">")

    # ----- dashboards -----
    def dashboards(self) -> list[dict]:
        out = []
        for db in self.root.findall("./dashboards/dashboard"):
            size = db.find("size")
            zones = []
            root_zone = db.find("zones")

            def walk(z: ET.Element, depth: int):
                entry = {
                    "depth": depth,
                    "type": z.get("type-v2") or z.get("type") or ("sheet" if z.get("name") else None),
                    "name": z.get("name"),
                    "layout": z.get("param") if z.get("type-v2") == "layout-flow" else None,
                    "x_pct": round(int(z.get("x", 0)) / ZONE_UNITS * 100, 2),
                    "y_pct": round(int(z.get("y", 0)) / ZONE_UNITS * 100, 2),
                    "w_pct": round(int(z.get("w", 0)) / ZONE_UNITS * 100, 2),
                    "h_pct": round(int(z.get("h", 0)) / ZONE_UNITS * 100, 2),
                }
                if z.get("type-v2") == "filter":
                    entry["filter_field"] = self.pill(z.get("param", ""))["field"]
                    entry["mode"] = z.get("mode")
                if z.get("show-title") == "false":
                    entry["title_hidden"] = True
                ft = z.find("formatted-text")
                if ft is not None:
                    entry["text"] = self._runs(ft)
                zones.append(entry)
                for child in z.findall("zone"):
                    walk(child, depth + 1)

            for z in (root_zone.findall("zone") if root_zone is not None else []):
                walk(z, 0)
            out.append({"name": db.get("name"),
                        "size": {k: size.get(k) for k in ("sizing-mode", "minwidth", "minheight", "maxwidth", "maxheight")} if size is not None else None,
                        "zones": zones})
        return out


def build_spec(path: Path) -> dict:
    root, data_files = read_workbook(path)
    wb = Workbook(root, data_files)
    sheets = wb.worksheets()
    dashboards = wb.dashboards()
    calcs = list(wb.calcs.values())
    for c in calcs:
        c["sheets"] = [ws["name"] for ws in sheets if c["caption"] in ws["calcs_needed"]]
    return {
        "source": path.name,
        "counts": {
            "worksheets": len(sheets),
            "dashboards": len(dashboards),
            "calcs": len(calcs),
            "table_calcs": sum(c["kind"] == "tc" for c in calcs),
            "lod": sum("lod" in c["own"] for c in calcs),
            "parameters": len(wb.params),
        },
        "datasources": wb.datasources,
        "data_files": data_files,
        "parameters": wb.params,
        "calcs": calcs,
        "colors": wb.colors,
        "datasource_filters": wb.datasource_filters(),
        "other_elements": wb.other_elements(),
        "worksheets": sheets,
        "dashboards": dashboards,
    }


def pill_md(p: dict) -> str:
    kind = "連続" if p.get("continuous") else "不連続"
    return f"`{p['label']}`({kind}{', △' if p.get('table_calc') else ''})"


def tree_md(node: dict, depth: int, shown: set, shelf: str | None = None) -> list[str]:
    """One line per node. A calc whose subtree was already printed for this sheet is marked and not expanded."""
    head = f"{shelf}: " if shelf else ""
    tc = " △" if node.get("kind") in ("tc", "tc-derived") else ""
    kind = f" [{node['kind']}]" if node.get("kind") else ""
    calc = node.get("calc")
    repeat = calc in shown and node.get("children")
    out = [f"{'  ' * depth}- {head}{node.get('label') or calc}{tc}{kind}{' (上に既出)' if repeat else ''}"]
    if repeat:
        return out
    if calc:
        shown.add(calc)
    for ch in node.get("children", []):
        out += tree_md(ch, depth + 1, shown)
    return out


def to_markdown(spec: dict) -> str:
    c = spec["counts"]
    lines = [f"# {spec['source']}", "",
             f"シート {c['worksheets']} / ダッシュボード {c['dashboards']} / 計算フィールド {c['calcs']}"
             f"（うち表計算 {c['table_calcs']}、LOD {c['lod']}）/ パラメーター {c['parameters']}", ""]
    lines.append("## データ")
    for ds in spec["datasources"]:
        lines.append(f"- {ds['caption']}: テーブル {', '.join(ds['tables'])}")
        for conn in ds["connections"]:
            lines.append(f"  - 接続 {conn['caption']} ({conn['class']}, {conn['file']})")
        for r in ds["relationships"]:
            lines.append(f"  - リレーションシップ {' ↔ '.join(x or '?' for x in r['between'])}: `{r['expression']}`")
        for j in ds["joins"]:
            lines.append(f"  - 結合 {j['join']}: `{j['on']}`")
    if spec["data_files"]:
        lines.append(f"- 同梱ファイル: {', '.join(spec['data_files'])}")
    if spec["parameters"]:
        lines += ["", "## パラメーター"]
        for p in spec["parameters"]:
            lines.append(f"- {p['caption']} ({p['datatype']}) = {p['value']}" + (f" / {p['members']}" if p["members"] else ""))
    lines += ["", "## 計算フィールド（kind: row=行レベル, agg=集計, tc=表計算, tc-derived=表計算を参照, lod=LOD）"]
    for calc in spec["calcs"]:
        lines.append(f"### {calc['caption']} [{calc['kind']}]")
        lines.append("```")
        lines.append(calc["formula"])
        lines.append("```")
        if calc.get("default_format"):
            lines.append(f"既定の数値書式: `{calc['default_format']}`")
        if calc["ref_captions"]:
            lines.append(f"参照: {', '.join(calc['ref_captions'])}")
        if calc["used_by"]:
            lines.append(f"被参照: {', '.join(calc['used_by'])}")
    if spec["colors"]:
        lines += ["", "## 色の割り当て"]
        for col in spec["colors"]:
            where = f"（シート {col['sheet']}）" if col.get("sheet") else ""
            lines.append(f"- {col['field']}{where}: " + ", ".join(f"{m['value']}={m['color']}" for m in col["map"]))
    lines += ["", "## シート"]
    for ws in spec["worksheets"]:
        lines.append(f"### {ws['name']}")
        lines.append(f"- Columns: {' '.join(pill_md(p) for p in ws['cols']) or '（なし）'}")
        lines.append(f"- Rows: {' '.join(pill_md(p) for p in ws['rows']) or '（なし）'}")
        for pane in ws["panes"]:
            head = f"- Marks{'（pane ' + pane['id'] + '）' if pane['id'] else ''}: {pane['mark']}"
            if pane.get("opacity_pct") is not None:
                head += f", 不透明度 {pane['opacity_pct']}%"
            lines.append(head)
            for e in pane["encodings"]:
                lines.append(f"  - {e['shelf']}: {pill_md(e)}")
            if pane.get("custom_label"):
                lines.append(f"  - ラベルの編集: {pane['custom_label']!r}")
            if pane.get("style"):
                lines.append("  - 書式: " + ", ".join(f"{k}={v}" for k, v in pane["style"].items()))
        for tc in ws["table_calcs"]:
            lines.append(f"- 表計算 `{tc['pill']}`:")
            for n in tc["nested"]:
                order = f" 順序: {' → '.join(n['order'])}" if n["order"] else ""
                tag = "（ピル自身）" if n["outer"] else ""
                extra = {k: v for k, v in n.items() if k not in ("calc", "kind", "outer", "ordering_type", "compute_using", "order")}
                lines.append(f"  - {n['calc']}{tag} [{n['kind']}]: {n['compute_using']} [{n['ordering_type']}]{order}{' ' + str(extra) if extra else ''}")
        for s in ws["sorts"]:
            if s["kind"] == "manual":
                lines.append(f"- 並べ替え {s['field']}: 手動 {' → '.join(s['order'])}")
            else:
                lines.append(f"- 並べ替え {s['field']}: {s['kind']} {s.get('direction')} {s.get('using') or ''}".rstrip())
        for f in ws["filters"]:
            saved = f" 保存時の値: {', '.join(f['saved_members'])}" if f["saved_members"] else ""
            group = f" 共有グループ {f['filter_group']}" if f.get("filter_group") else ""
            lines.append(f"- フィルター {f['field']} ({f['class']}){group}{saved}")
        for a in ws["axes"]:
            lines.append(f"- 軸固定 {a['field']} ({a['scope']}): {a['min']}〜{a['max']}{'、反転' if a.get('reversed') else ''}")
        if ws["hidden_headers"]:
            lines.append(f"- 非表示: {', '.join((h['field'] or h['element']) for h in ws['hidden_headers'])}")
        lines.append(f"- ディメンション: {', '.join(ws['dimensions']) or '（なし）'}")
        lines.append(f"- 要る計算（葉から）: {', '.join(ws['calcs_needed']) or '（なし）'}")
        lines.append("- 部品の木:")
        shown: set = set()
        for r in ws["tree"]:
            lines += tree_md(r, 1, shown, r["shelf"])
    if spec["other_elements"]:
        lines += ["", "## 抽出していない要素（TWB を直接見て、どの章で作るかを決める）"]
        for e in spec["other_elements"]:
            lines.append(f"- {e['kind']}（{e['where']}）: {e['detail']}")
    if spec["datasource_filters"]:
        lines += ["", "## データソース全体のフィルター（このデータソースを使う全シートに効く）"]
        for f in spec["datasource_filters"]:
            state = "すべて" if f["all"] else ", ".join(f["saved_members"])
            lines.append(f"- {f['field']} ({f['class']}): 保存時 {state}")
    groups = {}
    for ws in spec["worksheets"]:
        for f in ws["filters"]:
            if f.get("filter_group"):
                groups.setdefault((f["field"], f["filter_group"]), []).append(ws["name"])
    if groups:
        lines += ["", "## 共有フィルター（同じ filter-group を持つシート = 適用先）"]
        for (field, gid), sheets in groups.items():
            lines.append(f"- {field}（グループ {gid}）: {', '.join(sheets)}")
    lines += ["", "## ダッシュボード"]
    for db in spec["dashboards"]:
        lines.append(f"### {db['name']} {db['size']}")
        for z in db["zones"]:
            label = z.get("filter_field") or z["name"] or z.get("text") or z["layout"] or ""
            label = label.replace("\n", " ")[:60]
            extra = " filter" if z["type"] == "filter" else ""
            lines.append(f"{'  ' * z['depth']}- {z['type']}{extra} {label!r} x={z['x_pct']} y={z['y_pct']} w={z['w_pct']} h={z['h_pct']}"
                         + (" (title hidden)" if z.get("title_hidden") else ""))
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workbook", type=Path)
    ap.add_argument("--json", type=Path, help="write the full spec as JSON here")
    ap.add_argument("--md", type=Path, help="write the Markdown summary here instead of stdout")
    args = ap.parse_args()
    if not args.workbook.exists():
        print(f"Workbook not found: {args.workbook}", file=sys.stderr)
        return 1
    spec = build_spec(args.workbook)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    md = to_markdown(spec)
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(md, encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
