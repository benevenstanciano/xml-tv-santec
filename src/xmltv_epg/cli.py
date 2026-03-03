from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import load_config
from .fetcher import fetch_weekly_csvs
from .parser import parse_csv_file
from .util import ensure_dir
from .xmltv import Channel, build_xmltv_single_channel


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate per-language XMLTV from Radio Santec KW CSV files.")
    ap.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    ap.add_argument("--fetch-only", action="store_true", help="Only fetch CSVs, do not generate XMLTV")
    ap.add_argument("--no-fetch", action="store_true", help="Do not fetch, only generate from local CSVs")
    args = ap.parse_args()

    cfg = load_config(args.config)
    ensure_dir(cfg.paths.data_dir)
    ensure_dir(cfg.paths.csv_dir)
    ensure_dir(cfg.paths.output_dir)

    lang_codes = [l.code for l in cfg.languages]

    if not args.no_fetch:
        fr = fetch_weekly_csvs(
            base_url=cfg.base_url,
            csv_dir=cfg.paths.csv_dir,
            state_file=cfg.paths.state_file,
            timeout_seconds=cfg.fetch.timeout_seconds,
            user_agent=cfg.fetch.user_agent,
            languages=lang_codes,
            kw_min=cfg.fetch.kw_min,
            kw_max=cfg.fetch.kw_max,
        )
        print(
            f"Downloaded: {len(fr.downloaded)} | Skipped: {len(fr.skipped_existing)} | Not found: {len(fr.not_found)}"
        )

    if args.fetch_only:
        return

    total_all = 0

    for lang in cfg.languages:
        programmes = []

        for csv_path in sorted(cfg.paths.csv_dir.glob(f"{lang.code}_KW*.csv")):
            programmes.extend(
                parse_csv_file(
                    csv_path,
                    start_datetime_col=cfg.parser.columns.start_datetime,
                    duration_col=cfg.parser.columns.duration,
                    title_col=cfg.parser.columns.title,
                    desc_col=cfg.parser.columns.desc,
                )
            )

        programmes.sort(key=lambda p: p.start)

        # Retention window
        now = datetime.now(timezone.utc)
        start_cutoff = now - timedelta(days=cfg.retention.keep_past_days)
        end_cutoff = now + timedelta(days=cfg.retention.keep_future_days)

        programmes = [
            p for p in programmes
            if p.stop > start_cutoff and p.start < end_cutoff
        ]

        channel = Channel(
            id=lang.channel_id,
            display_name=lang.display_name,
            lang=lang.code,
            icon=lang.icon,
        )
        channel = Channel(
            id=lang.channel_id,
            display_name=lang.display_name,
            lang=lang.code,
            icon=lang.icon,
        )

        xml = build_xmltv_single_channel(channel=channel, programmes=programmes)

        out_path = cfg.paths.output_dir / f"xmltv_{lang.code}.xml"
        out_path.write_text(xml, encoding="utf-8")

        print(f"Wrote {out_path} ({len(programmes)} programmes)")
        total_all += len(programmes)

    print(f"Done. Total programmes written across languages: {total_all}")
