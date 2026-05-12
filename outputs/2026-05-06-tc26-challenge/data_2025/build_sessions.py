"""Build sessions.csv from TC25 Schedule + Session catalogue CSVs.

Join key: "Session Code". Outputs columns matching sessions.csv:
id, title, date, start_time, end_time, session_slot, topic, description
"""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
SCHEDULE_CSV = HERE / "Tableau Conference 2025 Session Catalogue - Public - Schedule.csv"
SESSION_CSV = HERE / "Tableau Conference 2025 Session Catalogue - Public - Session.csv"
OUTPUT_CSV = HERE / "sessions_2025.csv"

EXCLUDE_DATES = {"2025-04-14"}


def fmt_time_24(value: str) -> str:
    return datetime.strptime(value.strip(), "%I:%M %p").strftime("%H:%M")


def fmt_slot(start_24: str, end_24: str) -> str:
    def strip_leading_zero(t: str) -> str:
        h, m = t.split(":")
        return f"{int(h)}:{m}"

    return f"{strip_leading_zero(start_24)} - {strip_leading_zero(end_24)}"


def fmt_date(value: str) -> str:
    return datetime.strptime(value.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")


def normalize_topic(raw: str) -> str:
    if not raw:
        return ""
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return ", ".join(parts)


def load_sessions() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with SESSION_CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            code = row["Session Code"].strip()
            rows[code] = {
                "title": row["Title"].strip(),
                "topic": normalize_topic(row.get("Topic", "")),
                "description": row.get("Abstract", "").strip(),
            }
    return rows


def load_schedule() -> dict[str, list[dict]]:
    by_code: dict[str, list[dict]] = defaultdict(list)
    with SCHEDULE_CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            date_iso = fmt_date(row["Date"])
            if date_iso in EXCLUDE_DATES:
                continue
            code = row["Session Code"].strip()
            start_24 = fmt_time_24(row["Start Time"])
            end_24 = fmt_time_24(row["End Time"])
            by_code[code].append(
                {
                    "date": date_iso,
                    "start_time": start_24,
                    "end_time": end_24,
                    "session_slot": fmt_slot(start_24, end_24),
                    "_sort": (fmt_date(row["Date"]), start_24),
                }
            )
    for slots in by_code.values():
        slots.sort(key=lambda s: s["_sort"])
    return by_code


def build() -> list[dict]:
    sessions = load_sessions()
    schedule = load_schedule()
    out: list[dict] = []
    for code, meta in sessions.items():
        slots = schedule.get(code, [])
        if not slots:
            continue
        multi = len(slots) > 1
        for i, slot in enumerate(slots):
            row_id = f"{code}_slot{i}" if multi else code
            out.append(
                {
                    "id": row_id,
                    "title": meta["title"],
                    "date": slot["date"],
                    "start_time": slot["start_time"],
                    "end_time": slot["end_time"],
                    "session_slot": slot["session_slot"],
                    "topic": meta["topic"],
                    "description": meta["description"],
                }
            )
    out.sort(key=lambda r: (r["title"].lower(), r["id"]))
    return out


def main() -> None:
    rows = build()
    fieldnames = [
        "id",
        "title",
        "date",
        "start_time",
        "end_time",
        "session_slot",
        "topic",
        "description",
    ]
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
