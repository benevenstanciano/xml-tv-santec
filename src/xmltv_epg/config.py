from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PathsConfig:
    data_dir: Path
    csv_dir: Path
    state_file: Path
    output_dir: Path


@dataclass(frozen=True)
class FetchConfig:
    timeout_seconds: int
    user_agent: str
    kw_min: int = 1
    kw_max: int = 52


@dataclass(frozen=True)
class ParserColumns:
    start_datetime: str
    duration: str
    title: str
    desc: str


@dataclass(frozen=True)
class ParserConfig:
    columns: ParserColumns


@dataclass(frozen=True)
class LanguageConfig:
    code: str
    channel_id: str
    display_name: str
    icon: str | None = None


@dataclass(frozen=True)
class AppConfig:
    base_url: str
    timezone: str
    paths: PathsConfig
    fetch: FetchConfig
    parser: ParserConfig
    languages: list[LanguageConfig]
    retention: RetentionConfig
    
@dataclass(frozen=True)
class RetentionConfig:
    keep_past_days: int = 7
    keep_future_days: int = 28

def load_config(path: str | Path) -> AppConfig:
    p = Path(path)
    raw: dict[str, Any]
    with p.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    paths = raw["paths"]
    cfg_paths = PathsConfig(
        data_dir=Path(paths["data_dir"]),
        csv_dir=Path(paths["csv_dir"]),
        state_file=Path(paths["state_file"]),
        output_dir=Path(paths["output_dir"]),
    )

    fetch = FetchConfig(**raw["fetch"])

    parser_cols = ParserColumns(**raw["parser"]["columns"])
    parser = ParserConfig(columns=parser_cols)

    languages = [LanguageConfig(**x) for x in raw["languages"]]

    retention = RetentionConfig(**raw.get("retention", {}))

    return AppConfig(
        base_url=raw["base_url"],
        timezone=raw.get("timezone", "UTC"),
        paths=cfg_paths,
        fetch=fetch,
        parser=parser,
        languages=languages,
        retention=retention,
    )
