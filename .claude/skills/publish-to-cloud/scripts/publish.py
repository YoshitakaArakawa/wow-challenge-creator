#!/usr/bin/env python3
"""Publish a .twbx workbook to Tableau Cloud with PAT auth, retries, and pre-backup on overwrite."""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import tableauserverclient as TSC
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(REPO_ROOT / ".env")

RETRY_BASE_SECONDS = 2
MAX_RETRIES = 3


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Publish a workbook to Tableau Cloud.")
    p.add_argument("--twbx", required=True, help="Path to the .twbx file (absolute or relative to repo root).")
    p.add_argument("--output-dir", required=True, help="Theme folder; tmp/publish-result.json and backup/ live here.")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing workbook of the same name.")
    p.add_argument("--project", default=None, help="Project name. Defaults to TABLEAU_PROJECT_NAME env.")
    p.add_argument("--name", default=None, help="Workbook display name. Defaults to file stem.")
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
    backup_dir = output_dir / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"{existing.name}.twbx"
    server.workbooks.download(existing.id, filepath=str(target), include_extract=True, no_extract=False)
    return target


def write_result(output_dir: Path, payload: dict) -> Path:
    tmp = output_dir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    out = tmp / "publish-result.json"
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
    project_name = args.project or require_env("TABLEAU_PROJECT_NAME")

    server_url = require_env("TABLEAU_SERVER_URL")
    site_id = os.environ.get("TABLEAU_SITE_ID", "")
    pat_name = require_env("TABLEAU_PAT_NAME")
    pat_value = require_env("TABLEAU_PAT_VALUE")

    auth = TSC.PersonalAccessTokenAuth(pat_name, pat_value, site_id)
    server = TSC.Server(server_url, use_server_version=True)

    try:
        with server.auth.sign_in(auth):
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
