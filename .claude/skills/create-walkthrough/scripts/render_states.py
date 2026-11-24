#!/usr/bin/env python3
"""Render one published view under several filter states, for walkthrough figures and check values.

Reuses the publish-to-cloud sign-in (.env + cached OAuth session, or PAT) and the
workbook id that publish-to-cloud wrote to publish-result.json: the finished workbook's
(refine/publish-result.json, the default) or the verification workbook's (--publish-result).

Each --state is "label" or "label|Field=Value[,Value...]|Field=Value...".
A state without filters renders the view as saved in the workbook.

Usage:
  python render_states.py --theme-dir outputs/2026-01-01-theme --view Dashboard \
      --state "all" --state "sds|Ship Mode=Same Day|Region=South"
  python render_states.py --theme-dir outputs/2026-01-01-theme --view "Link 0-1"       --publish-result tmp/walkthrough/sheets/refine/publish-result.json       --out-dir tmp/walkthrough/figs --prefix sheet-link01- --state "all" --state "sds|Ship Mode=Same Day|Region=South"
Output: <out-dir>/<prefix><label>.png (default <theme>/refine/render/guide/<label>.png),
plus <prefix>states.json listing label, filters and file.
"""

import argparse
import json
import sys
from pathlib import Path

import tableauserverclient as TSC

PUBLISH_SCRIPTS = Path(__file__).resolve().parents[2] / "publish-to-cloud" / "scripts"
sys.path.insert(0, str(PUBLISH_SCRIPTS))
from tableau_auth import REPO_ROOT, signed_in_server  # noqa: E402

# 1 minute is the smallest maxAge the REST API accepts; keeps renders fresh after a re-publish.
IMAGE_MAX_AGE_MINUTES = 1


def parse_state(text: str) -> dict:
    parts = [p.strip() for p in text.split("|") if p.strip()]
    if not parts:
        raise SystemExit(f"Empty --state: {text!r}")
    filters = []
    for part in parts[1:]:
        if "=" not in part:
            raise SystemExit(f"Filter must be Field=Value in --state {text!r}: {part!r}")
        field, value = part.split("=", 1)
        filters.append({"field": field.strip(), "value": value.strip()})
    label = parts[0]
    if not label.replace("-", "").replace("_", "").isalnum():
        raise SystemExit(f"State label must be letters, digits, - or _: {label!r}")
    return {"label": label, "filters": filters}


def resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme-dir", required=True, help="outputs/{theme} (absolute or relative to repo root)")
    ap.add_argument("--view", required=True, help="view (dashboard or sheet) name to render")
    ap.add_argument("--state", action="append", required=True, help='"label" or "label|Field=V1,V2|Field2=V"')
    ap.add_argument("--workbook-id", help="defaults to workbookId in the publish result")
    ap.add_argument("--publish-result", default="refine/publish-result.json", help="relative to the theme folder")
    ap.add_argument("--out-dir", default="refine/render/guide", help="relative to the theme folder")
    ap.add_argument("--prefix", default="", help="prepended to every output file name")
    args = ap.parse_args()

    theme = resolve(args.theme_dir)
    workbook_id = args.workbook_id
    if not workbook_id:
        result_path = theme / args.publish_result
        if not result_path.exists():
            raise SystemExit(f"{result_path} not found. Publish first (publish-to-cloud) or pass --workbook-id.")
        workbook_id = json.loads(result_path.read_text(encoding="utf-8"))["workbookId"]
    states = [parse_state(s) for s in args.state]

    out_dir = theme / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    with signed_in_server() as server:
        workbook = server.workbooks.get_by_id(workbook_id)
        server.workbooks.populate_views(workbook)
        views = {v.name: v for v in workbook.views}
        if args.view not in views:
            raise SystemExit(f"View {args.view!r} not found. Available: {sorted(views)}")
        view = views[args.view]
        for state in states:
            options = TSC.ImageRequestOptions(
                imageresolution=TSC.ImageRequestOptions.Resolution.High,
                maxage=IMAGE_MAX_AGE_MINUTES,
            )
            for f in state["filters"]:
                options.vf(f["field"], f["value"])
            server.views.populate_image(view, options)
            target = out_dir / f"{args.prefix}{state['label']}.png"
            target.write_bytes(view.image)
            written.append({**state, "file": str(target.relative_to(theme)).replace("\\", "/")})
            print(f"{state['label']}: {target}")
    (out_dir / f"{args.prefix}states.json").write_text(json.dumps(written, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
