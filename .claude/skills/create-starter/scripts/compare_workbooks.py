"""Compare two workbooks element by element: calculated fields, worksheets,
windows, dashboard zones and shared views.

Usage:
  python compare_workbooks.py <a.twbx|a.twb> <b.twbx|b.twb> [--sheets "A,B"]

Typical pairs:
- finished workbook vs starter, with --sheets set to the kept sheets: those
  worksheets and their calcs must be identical (only the starter's removals differ)
- an earlier starter vs a regenerated one: reports every difference

Each worksheet is compared as canonical XML (attribute order and whitespace
ignored). Exit code 0 when nothing differs within the compared scope, 1 otherwise.
"""
import argparse
import sys
import zipfile
from pathlib import Path

from lxml import etree


def load(path):
    p = Path(path)
    if p.suffix.lower() == ".twb":
        data = p.read_bytes()
    else:
        with zipfile.ZipFile(p) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".twb") and "/" not in n)
            data = z.read(name)
    parser = etree.XMLParser(remove_blank_text=True, huge_tree=True)
    return etree.fromstring(data, parser)


def canon(el):
    return etree.tostring(el, method="c14n").decode("utf-8") if el is not None else None


def calcs(root):
    out = {}
    for ds in root.findall("./datasources/datasource"):
        for col in ds.findall("./column"):
            c = col.find("calculation")
            if c is not None:
                out[col.get("caption") or col.get("name")] = canon(col)
    return out


def by_name(root, path):
    return {el.get("name"): canon(el) for el in root.findall(path)}


def zones(root):
    out = {}
    for dash in root.findall("./dashboards/dashboard"):
        for z in dash.iter("zone"):
            key = (dash.get("name"), z.get("name") or f"<{z.get('type-v2')}>", z.get("x"), z.get("y"))
            out[key] = {k: z.get(k) for k in ("w", "h", "fixed-size", "is-fixed", "type-v2", "param")}
    return out


def diff_maps(label, a, b, scope=None):
    keys = set(a) | set(b)
    if scope is not None:
        keys &= scope
    lines = []
    for k in sorted(keys, key=str):
        if k not in b:
            lines.append(f"  only in A: {k}")
        elif k not in a:
            lines.append(f"  only in B: {k}")
        elif a[k] != b[k]:
            lines.append(f"  differs:   {k}")
    print(f"{label}: {'same' if not lines else str(len(lines)) + ' difference(s)'}")
    for line in lines:
        print(line)
    return not lines


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--sheets", help="Compare only these worksheets (and their windows); "
                                    "calcs are compared only where both sides have them")
    args = p.parse_args()
    a, b = load(args.a), load(args.b)
    scope = {s.strip() for s in args.sheets.split(",")} if args.sheets else None

    ok = True
    ca, cb = calcs(a), calcs(b)
    ok &= diff_maps("calculated fields", ca, cb, (set(ca) & set(cb)) if scope else None)
    ok &= diff_maps("worksheets", by_name(a, "./worksheets/worksheet"), by_name(b, "./worksheets/worksheet"), scope)
    ok &= diff_maps("windows", by_name(a, "./windows/window"), by_name(b, "./windows/window"), scope)
    if scope is None:
        ok &= diff_maps("dashboard zones", zones(a), zones(b))
        ok &= diff_maps("shared views", by_name(a, "./shared-views/shared-view"),
                        by_name(b, "./shared-views/shared-view"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
