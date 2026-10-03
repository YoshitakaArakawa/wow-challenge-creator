#!/usr/bin/env python3
"""Publish a .twbx workbook to Tableau Cloud (OAuth browser sign-in, or PAT if configured), with retries, pre-backup on overwrite,
and optional server-side rendering of every view to PNG (--render) for a fast edit → publish → look loop.
--text-table also saves each view as SVG and extracts its text runs (position, colour, size, weight) into a TSV,
so text formatting can be checked from a few hundred tokens instead of reading the image."""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import tableauserverclient as TSC

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tableau_auth import REPO_ROOT, signed_in_server  # noqa: E402  (loads .env, OAuth or PAT)

# Every artifact of the publish/refine loop lives in <theme>/refine/ (gitignored).
REFINE_DIR_NAME = "refine"
RETRY_BASE_SECONDS = 2
MAX_RETRIES = 3
# Cloud caches rendered images; 1 minute is the smallest maxAge the REST API accepts,
# so a re-publish within the same minute could still return the previous render.
IMAGE_MAX_AGE_MINUTES = 1
# Right after publish the workbook may not be queryable yet; poll briefly instead of failing.
RENDER_READY_RETRIES = 5
RENDER_READY_WAIT_SECONDS = 3
# Query View Image accepts format=svg from REST API 3.29 (Tableau Cloud June 2026 / Server 2026.2).
SVG_MIN_API_VERSION = (3, 29)
SVG_NS = "{http://www.w3.org/2000/svg}"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Publish a workbook to Tableau Cloud.")
    p.add_argument("--twbx", required=True, help="Path to the .twbx file (absolute or relative to repo root).")
    p.add_argument(
        "--output-dir",
        required=True,
        help="Theme folder (outputs/{theme}); refine/publish-result.json, refine/render/ and refine/backup/ are written under it.",
    )
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing workbook of the same name.")
    p.add_argument("--project", default=None, help="Project name. Defaults to TABLEAU_PROJECT_NAME env.")
    p.add_argument("--name", default=None, help="Workbook display name. Defaults to file stem.")
    p.add_argument(
        "--render",
        action="store_true",
        help="After publishing, download a PNG of every view into <output-dir>/refine/render/ (High resolution).",
    )
    p.add_argument(
        "--views",
        default=None,
        help="Comma-separated view names to render (default: all views). Only with --render.",
    )
    p.add_argument(
        "--text-table",
        action="store_true",
        help="With --render, also save each view as SVG and write its text runs to <view>.text.tsv (needs REST API 3.29+).",
    )
    return p.parse_args()


def require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing env var {key}. Configure {REPO_ROOT / '.env'}")
    return value


def find_project(server: TSC.Server, project_name: str) -> TSC.ProjectItem:
    options = TSC.RequestOptions()
    options.filter.add(TSC.Filter(TSC.RequestOptions.Field.Name, TSC.RequestOptions.Operator.Equals, project_name))
    projects, _ = server.projects.get(options)
    if not projects:
        raise RuntimeError(f"Project not found: {project_name}")
    return projects[0]


def find_workbook_by_name(server: TSC.Server, name: str, project_id: str) -> Optional[TSC.WorkbookItem]:
    options = TSC.RequestOptions(pagesize=100)
    options.filter.add(TSC.Filter(TSC.RequestOptions.Field.Name, TSC.RequestOptions.Operator.Equals, name))
    workbooks, _ = server.workbooks.get(options)
    return next((wb for wb in workbooks if wb.project_id == project_id), None)


def backup_existing(server: TSC.Server, existing: TSC.WorkbookItem, output_dir: Path) -> Path:
    backup_dir = output_dir / REFINE_DIR_NAME / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    # TSC names the file itself (<workbook name>.twbx) when given a directory.
    saved = server.workbooks.download(existing.id, filepath=str(backup_dir), include_extract=True)
    return Path(saved)


def safe_file_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_") or "view"


def _parse_matrix(transform: Optional[str]) -> tuple:
    """SVG transform="matrix(a,b,c,d,e,f)" -> affine tuple; anything else is treated as identity."""
    m = re.match(r"\s*matrix\(([^)]*)\)", transform or "")
    if not m:
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    return tuple(float(v) for v in re.split(r"[ ,]+", m.group(1).strip()))


def _compose(outer: tuple, inner: tuple) -> tuple:
    a, b, c, d, e, f = outer
    a2, b2, c2, d2, e2, f2 = inner
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2, a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def svg_text_rows(svg: bytes) -> list:
    """Every <text> in a Tableau view SVG as {x, y, fill, size, weight, text}, x/y in page pixels, top to bottom."""
    rows = []

    def walk(node, matrix):
        matrix = _compose(matrix, _parse_matrix(node.get("transform")))
        if node.tag == SVG_NS + "text":
            text = "".join(node.itertext()).strip()
            if text:
                x, y = float(node.get("x", 0)), float(node.get("y", 0))
                a, b, c, d, e, f = matrix
                rows.append({
                    "x": round(a * x + c * y + e),
                    "y": round(b * x + d * y + f),
                    "fill": node.get("fill", ""),
                    "size": node.get("font-size", ""),
                    "weight": node.get("font-weight", ""),
                    "text": text,
                })
            return
        for child in node:
            walk(child, matrix)

    walk(ET.fromstring(svg), (1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    return sorted(rows, key=lambda r: (r["y"], r["x"]))


def fetch_view_svg(server: TSC.Server, view_id: str) -> bytes:
    """TSC's populate_image has no format option, so call Query View Image directly."""
    url = f"{server.baseurl}/sites/{server.site_id}/views/{view_id}/image?format=svg&maxAge={IMAGE_MAX_AGE_MINUTES}"
    request = urllib.request.Request(url, headers={"X-Tableau-Auth": server.auth_token})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def supports_svg(server: TSC.Server) -> bool:
    return tuple(int(p) for p in str(server.version).split(".")[:2]) >= SVG_MIN_API_VERSION


def render_views(server: TSC.Server, workbook_id: str, output_dir: Path, only: Optional[set], text_table: bool = False) -> list:
    """Download a PNG per view (plus SVG and a text table with text_table).
    Returns [{viewName, viewId, filePath[, svgPath, textTablePath]}] for the views rendered."""
    render_dir = output_dir / REFINE_DIR_NAME / "render"
    render_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.png", "*.svg", "*.text.tsv"):
        for stale in render_dir.glob(pattern):
            stale.unlink()
    if text_table and not supports_svg(server):
        print(f"--text-table skipped: server REST API {server.version} is older than 3.29 (no SVG view images).", file=sys.stderr)
        text_table = False

    workbook = None
    for attempt in range(RENDER_READY_RETRIES):
        try:
            workbook = server.workbooks.get_by_id(workbook_id)
            server.workbooks.populate_views(workbook)
            if workbook.views:
                break
        except TSC.ServerResponseError as err:
            print(f"views not ready yet ({err}); retrying...", file=sys.stderr)
        time.sleep(RENDER_READY_WAIT_SECONDS)
    if workbook is None or not workbook.views:
        raise RuntimeError("Workbook published but its views could not be listed for rendering.")

    options = TSC.ImageRequestOptions(
        imageresolution=TSC.ImageRequestOptions.Resolution.High,
        maxage=IMAGE_MAX_AGE_MINUTES,
    )
    rendered = []
    skipped = []
    for view in workbook.views:
        if only is not None and view.name not in only:
            skipped.append(view.name)
            continue
        server.views.populate_image(view, options)
        target = render_dir / f"{safe_file_name(view.name)}.png"
        target.write_bytes(view.image)
        entry = {"viewName": view.name, "viewId": view.id, "filePath": str(target)}
        if text_table:
            try:
                svg = fetch_view_svg(server, view.id)
            except urllib.error.HTTPError as err:
                print(f"SVG for {view.name} failed ({err.code}); PNG only.", file=sys.stderr)
            else:
                svg_path = render_dir / f"{safe_file_name(view.name)}.svg"
                svg_path.write_bytes(svg)
                table_path = render_dir / f"{safe_file_name(view.name)}.text.tsv"
                columns = ["x", "y", "fill", "size", "weight", "text"]
                lines = ["\t".join(columns)] + [
                    "\t".join(str(r[c]) for c in columns) for r in svg_text_rows(svg)
                ]
                table_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                entry.update({"svgPath": str(svg_path), "textTablePath": str(table_path)})
        rendered.append(entry)
    if only is not None:
        missing = sorted(only - {r["viewName"] for r in rendered})
        if missing:
            print(f"--views names not found in workbook: {missing}. Available: {skipped + [r['viewName'] for r in rendered]}", file=sys.stderr)
    return rendered


def write_result(output_dir: Path, payload: dict) -> Path:
    refine = output_dir / REFINE_DIR_NAME
    refine.mkdir(parents=True, exist_ok=True)
    out = refine / "publish-result.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def resolve_path(p: str) -> Path:
    candidate = Path(p)
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / p).resolve()
    return candidate


def publish_with_retry(server: TSC.Server, wb_item: TSC.WorkbookItem, twbx_path: Path, mode) -> TSC.WorkbookItem:
    last_err: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            return server.workbooks.publish(wb_item, str(twbx_path), mode)
        except TSC.ServerResponseError as err:
            last_err = err
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_SECONDS * (2 ** attempt)
                print(f"publish attempt {attempt + 1} failed: {err}. Retrying in {delay}s...", file=sys.stderr)
                time.sleep(delay)
                continue
            raise
    raise last_err  # type: ignore[misc]


def main() -> int:
    args = parse_args()
    twbx_path = resolve_path(args.twbx)
    output_dir = resolve_path(args.output_dir)

    if not twbx_path.exists():
        raise RuntimeError(f"TWBX not found: {twbx_path}")

    workbook_name = args.name or twbx_path.stem

    try:
        project_name = args.project or require_env("TABLEAU_PROJECT_NAME")

        with signed_in_server() as server:
            project = find_project(server, project_name)
            existing = find_workbook_by_name(server, workbook_name, project.id)

            overwrote = False
            backup_path: Optional[Path] = None
            if existing:
                if not args.overwrite:
                    raise RuntimeError(
                        f'Workbook "{workbook_name}" already exists in "{project_name}". '
                        "Re-run with --overwrite to replace it."
                    )
                backup_path = backup_existing(server, existing, output_dir)
                overwrote = True

            wb_item = TSC.WorkbookItem(project_id=project.id, name=workbook_name)
            mode = TSC.Server.PublishMode.Overwrite if existing else TSC.Server.PublishMode.CreateNew
            new_wb = publish_with_retry(server, wb_item, twbx_path, mode)

            renders = None
            if args.render:
                only = {v.strip() for v in args.views.split(",") if v.strip()} if args.views else None
                renders = render_views(server, new_wb.id, output_dir, only, text_table=args.text_table)

            payload = {
                "ok": True,
                "workbookId": new_wb.id,
                "workbookName": new_wb.name,
                "projectName": project_name,
                "webpageUrl": new_wb.webpage_url,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "overwrote": overwrote,
                "backupPath": str(backup_path) if backup_path else None,
                "source": str(twbx_path),
                "renders": renders,
            }
            out = write_result(output_dir, payload)
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            print(f"\nResult written to {out}", file=sys.stderr)
            return 0
    except Exception as err:
        payload = {
            "ok": False,
            "error": str(err),
            "errorType": type(err).__name__,
            "source": str(twbx_path),
            "attemptedAt": datetime.now(timezone.utc).isoformat(),
        }
        write_result(output_dir, payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
