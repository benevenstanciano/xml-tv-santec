from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dateutil import parser as dtparser
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Programme:
    start: datetime
    stop: datetime
    title: str
    desc: str | None = None


def _norm(s: str) -> str:
    return (s or "").strip()


def _parse_duration_hms(s: str) -> timedelta | None:
    s = _norm(s)
    if not s:
        return None
    try:
        parts = s.split(":")
        if len(parts) != 3:
            return None
        h = int(parts[0])
        m = int(parts[1])
        sec = int(parts[2])
        return timedelta(hours=h, minutes=m, seconds=sec)
    except Exception:
        return None


def parse_csv_file(
    path: Path,
    start_datetime_col: str,
    duration_col: str,
    title_col: str,
    desc_col: str,
) -> list[Programme]:
    raw = path.read_bytes()

    text = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except Exception:
            continue
    if text is None:
        text = raw.decode("utf-8", errors="replace")

    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
    except Exception:
        dialect = csv.get_dialect("excel")

    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    if not reader.fieldnames:
        return []

    programmes: list[Programme] = []
    for row in reader:
        start_raw = _norm(row.get(start_datetime_col, ""))
        dur_raw = _norm(row.get(duration_col, ""))
        title = _norm(row.get(title_col, ""))
        desc = _norm(row.get(desc_col, ""))

        if not start_raw or not title:
            continue

        try:
            start_dt = dtparser.parse(start_raw, dayfirst=True, fuzzy=True)
        except Exception:
            continue

        # Treat CSV times as Europe/Berlin local time, then convert to UTC
        berlin_tz = ZoneInfo("Europe/Berlin")

        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=berlin_tz)

        start_dt = start_dt.astimezone(timezone.utc)

        dur = _parse_duration_hms(dur_raw) or timedelta(minutes=60)
        stop_dt = start_dt + dur

        programmes.append(
            Programme(
                start=start_dt,
                stop=stop_dt,
                title=title,
                desc=desc or None,
            )
        )

    programmes.sort(key=lambda p: p.start)
    return programmes
