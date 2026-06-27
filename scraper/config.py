from __future__ import annotations

import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import SourceSpec


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCRAPER_", env_file=".env", extra="ignore")

    min_interval: float = 1.0
    respect_robots: bool = True
    user_agent: str = "RoviDevBot/1.0 (+https://rovidev.com)"
    state_dir: str = "data/state"
    timeout: float = 10.0

    google_credentials: str = ""
    sheet_id: str = ""


def load_sources(path: str | Path) -> list[SourceSpec]:
    """Read one or more :class:`SourceSpec` definitions from a JSON file.

    The file may contain a single object or a list of objects.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = raw if isinstance(raw, list) else [raw]
    return [SourceSpec.model_validate(entry) for entry in entries]


def get_settings() -> Settings:
    return Settings()
