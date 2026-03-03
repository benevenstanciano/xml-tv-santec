from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import requests

from .util import ensure_dir, sha256_bytes


@dataclass
class FetchResult:
    downloaded: list[Path]
    skipped_existing: list[Path]
    not_found: list[str]


def _load_state(state_file: Path) -> dict:
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return {"seen": {}}


def _save_state(state_file: Path, state: dict) -> None:
    ensure_dir(state_file.parent)
    state_file.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def fetch_weekly_csvs(
    base_url: str,
    csv_dir: Path,
    state_file: Path,
    timeout_seconds: int,
    user_agent: str,
    languages: list[str],
    kw_min: int = 1,
    kw_max: int = 52,
) -> FetchResult:
    ensure_dir(csv_dir)
    state = _load_state(state_file)
    seen: dict[str, str] = state.get("seen", {})

    headers = {"User-Agent": user_agent}
    session = requests.Session()

    downloaded: list[Path] = []
    skipped_existing: list[Path] = []
    not_found: list[str] = []

    for lang in languages:
        lang_upper = lang.upper()
        for kw in range(kw_min, kw_max + 1):
            url = base_url.format(lang=lang, lang_upper=lang_upper, kw=kw)
            key = f"{lang}:KW{kw:02d}"
            out = csv_dir / f"{lang}_KW{kw:02d}.csv"

            try:
                r = session.get(url, headers=headers, timeout=timeout_seconds)
            except Exception:
                not_found.append(key)
                continue

            if r.status_code == 404:
                not_found.append(key)
                continue

            if r.status_code != 200 or not r.content:
                not_found.append(key)
                continue

            content_hash = sha256_bytes(r.content)

            if seen.get(key) == content_hash and out.exists():
                skipped_existing.append(out)
                continue

            out.write_bytes(r.content)
            seen[key] = content_hash
            downloaded.append(out)

    state["seen"] = seen
    _save_state(state_file, state)
    return FetchResult(downloaded=downloaded, skipped_existing=skipped_existing, not_found=not_found)
