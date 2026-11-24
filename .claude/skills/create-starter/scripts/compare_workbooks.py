"""Compare two workbooks element by element: calculated fields, datasource
filters/sets/drill paths, worksheets, windows, actions, dashboard zones and
shared views.

Usage:
  python compare_workbooks.py <a.twbx|a.twb> <b.twbx|b.twb> [--sheets "A,B"]

Typical pairs:
- finished workbook (A) vs starter (B), with --sheets set to the kept sheets:
  the kept worksheets, every calc the starter has, and the datasource filters,
  sets and shared views must be identical. Calcs only in A are the ones
  participants build and are listed for information
- an earlier starter vs a regenerated one: reports every difference

Elements are compared as canonical XML (attribute order and whitespace ignored).
Links to published copies (repository-location) are ignored. Exit code 0 when
nothing differs within the compared scope, 1 otherwise.
"""
import argparse
import sys
import zipfile
from pathlib import Path

from lxml import etree

# Datasource children compared as a whole (anything that changes the data or the
# sets participants see). Calcs are compared one by one.
DATASOURCE_TAGS = ("filter", "group", "drill-paths", "extract")


def load(path):
    p = Path(path)
    if p.suffix.lower() == ".twb":
        data = p.read_bytes()
    else:
        with zipfile.ZipFile(p) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".twb") and "/" not in n)
            data = z.read(name)
    root = etree.fromstring(data, etree.XMLParser(remove_blank_text=True, huge_tree=True))
    for rl in list(root.iter("repository-location")):
        rl.getparent().remove(rl)
    return root


def canon(el):
    return etree.tostring(el, method="c14n").decode("utf-8")


def calcs(root):
    out = {}
    for ds in root.findall("./datasources/datasource"):
        for col in ds.findall("./column"):
            if col.find("calculation") is not None:
                out[(ds.get("name"), col.get("caption") or col.get("name"))] = canon(col)
    return out


def datasource_parts(root):
    out = {}
    for ds in root.findall("./datasources/datasource"):
        for tag in DATASOURCE_TAGS:
            for i, el in enumerate(ds.findall(f"./{tag}")):
                out[(ds.get("name"), tag, el.get("name") or el.get("column") or str(i))] = canon(el)
    return out


def by_name(root, path):
    return {el.get("name"): canon(el) for el in root.findall(path)}


def zones(root):
    out = {}
    for dash in root.findall("./dashboards/dashboard"):
        for z in dash.iter("zone"):
            device = next((a.get("name") for a in z.iterancestors("devicelayout")), "")
            key = (dash.get("name"), device, z.get("name") or f"<{z.get('type-v2')}>", z.get("x"), z.get("y"))
            out[key] = {k: z.get(k) for k in ("w", "h", "fixed-size", "is-fixed", "type-v2", "param")}
    return out


def diff_maps(label, a, b, keys=None):
    keys = (set(a) | set(b)) if keys is None else keys
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
    p.add_argument("--sheets", help="A is the finished workbook and B the starter; compare only these "
                                    "worksheets, and every calc B has")
    args = p.parse_args()
    a, b = load(args.a), load(args.b)

    ok = True
    ca, cb = calcs(a), calcs(b)
    if args.sheets:
        scope = {s.strip() for s in args.sheets.split(",")}
        ok &= diff_maps("calculated fields in B", ca, cb, set(cb))
        only_a = sorted(k[1] for k in set(ca) - set(cb))
        print(f"calculated fields only in A (participants build): {len(only_a)}")
        for k in only_a:
            print(f"  {k}")
        ok &= diff_maps("datasource filters/sets/drill paths", datasource_parts(a), datasource_parts(b))
        ok &= diff_maps("worksheets", by_name(a, "./worksheets/worksheet"),
                        by_name(b, "./worksheets/worksheet"), scope)
        ok &= diff_maps("windows", by_name(a, "./windows/window"), by_name(b, "./windows/window"), scope)
        ok &= diff_maps("shared views", by_name(a, "./shared-views/shared-view"),
                        by_name(b, "./shared-views/shared-view"))
    else:
        ok &= diff_maps("calculated fields", ca, cb)
        ok &= diff_maps("datasource filters/sets/drill paths", datasource_parts(a), datasource_parts(b))
        ok &= diff_maps("worksheets", by_name(a, "./worksheets/worksheet"), by_name(b, "./worksheets/worksheet"))
        ok &= diff_maps("windows", by_name(a, "./windows/window"), by_name(b, "./windows/window"))
        ok &= diff_maps("actions", by_name(a, ".//actions/action"), by_name(b, ".//actions/action"))
        ok &= diff_maps("dashboard zones", zones(a), zones(b))
        ok &= diff_maps("shared views", by_name(a, "./shared-views/shared-view"),
                        by_name(b, "./shared-views/shared-view"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
