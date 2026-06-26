"""Settings from env vars and locations from locations.json."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .models import Location, ValidationError

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCATIONS = ROOT / "locations.json"
DATA_DIR = ROOT / "data"


@dataclass(frozen=True, slots=True)
class Settings:
    max_workers: int = 8
    request_timeout_s: int = 30
    max_retries: int = 3
    data_dir: Path = DATA_DIR

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            max_workers=int(os.environ.get("GEOSTREAM_MAX_WORKERS", "8")),
            request_timeout_s=int(os.environ.get("GEOSTREAM_TIMEOUT", "30")),
            max_retries=int(os.environ.get("GEOSTREAM_RETRIES", "3")),
            data_dir=Path(os.environ.get("GEOSTREAM_DATA_DIR", str(DATA_DIR))),
        )


def load_locations(path: Path | None = None) -> tuple[list[Location], list[Location]]:
    path = path or DEFAULT_LOCATIONS
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    cities = [
        Location(
            name=c["city"], country=c.get("country", ""),
            latitude=float(c["latitude"]), longitude=float(c["longitude"]),
        )
        for c in raw.get("cities", [])
    ]
    nino = [
        Location(
            name=n["name"], region=n.get("region", ""),
            latitude=float(n["latitude"]), longitude=float(n["longitude"]),
        )
        for n in raw.get("nino_regions", [])
    ]
    if not cities and not nino:
        raise ValidationError(f"No locations configured in {path}")
    return cities, nino
