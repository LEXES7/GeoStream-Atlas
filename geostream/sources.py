"""Open-Meteo client. Free, key-less, stdlib-only, with backoff retries.

Locations are fetched in batches (Open-Meteo accepts many coordinates per call),
which keeps a run to a handful of requests even with hundreds of cities and stays
well inside the free rate limits.
"""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any

from .config import Settings
from .logging_setup import get_logger
from .models import CityObservation, Location, NinoObservation

log = get_logger(__name__)

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
MARINE_ARCHIVE_URL = "https://marine-api.open-meteo.com/v1/marine"
_USER_AGENT = "GeoStream-Atlas/1.0"
_BATCH = 100

CURRENT_VARS = (
    "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
    "cloud_cover,wind_speed_10m,wind_direction_10m,surface_pressure,"
    "pressure_msl,weather_code"
)
DAILY_VARS = "temperature_2m_max,temperature_2m_min,precipitation_sum,uv_index_max"
MARINE_CURRENT = "sea_surface_temperature,wave_height"
MARINE_DAILY = "sea_surface_temperature_max,sea_surface_temperature_min,wave_height_max"


class SourceError(RuntimeError):
    pass


def _get(url: str, params: dict, settings: Settings) -> Any:
    full = f"{url}?{urllib.parse.urlencode(params)}"
    last_err: Exception | None = None
    for attempt in range(1, settings.max_retries + 1):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": _USER_AGENT})
            with urllib.request.urlopen(req, timeout=settings.request_timeout_s) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as err:
            last_err = err
            backoff = min(2**attempt + random.uniform(0, 0.5), 20)
            log.warning(
                "upstream fetch failed, retrying",
                extra={"fields": {"url": url, "attempt": attempt, "backoff_s": round(backoff, 2)}},
            )
            if attempt < settings.max_retries:
                time.sleep(backoff)
    raise SourceError(f"{url} failed after {settings.max_retries} attempts: {last_err}")


def _as_list(resp: Any) -> list[dict]:
    return resp if isinstance(resp, list) else [resp]


def _first(daily: dict, key: str):
    vals = daily.get(key) or []
    return vals[0] if vals else None


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _city_from(loc: Location, date: str, iso_date: str, obj: dict) -> CityObservation:
    cur, daily = obj.get("current", {}), obj.get("daily", {})
    return CityObservation(
        date=date, iso_date=iso_date, country=loc.country, city=loc.name,
        latitude=loc.latitude, longitude=loc.longitude,
        temperature_c=cur.get("temperature_2m"),
        temperature_max_c=_first(daily, "temperature_2m_max"),
        temperature_min_c=_first(daily, "temperature_2m_min"),
        apparent_temperature_c=cur.get("apparent_temperature"),
        humidity_pct=cur.get("relative_humidity_2m"),
        precipitation_mm=_first(daily, "precipitation_sum"),
        cloud_cover_pct=cur.get("cloud_cover"),
        wind_speed_kmh=cur.get("wind_speed_10m"),
        wind_direction_deg=cur.get("wind_direction_10m"),
        surface_pressure_hpa=cur.get("surface_pressure"),
        pressure_msl_hpa=cur.get("pressure_msl"),
        uv_index_max=_first(daily, "uv_index_max"),
        weather_code=cur.get("weather_code"),
        observed_at=cur.get("time"),
    )


def _nino_from(loc: Location, date: str, iso_date: str, obj: dict) -> NinoObservation:
    cur, daily = obj.get("current", {}), obj.get("daily", {})
    return NinoObservation(
        date=date, iso_date=iso_date, name=loc.name, region=loc.region,
        latitude=loc.latitude, longitude=loc.longitude,
        sea_surface_temperature_c=cur.get("sea_surface_temperature"),
        sst_max_c=_first(daily, "sea_surface_temperature_max"),
        sst_min_c=_first(daily, "sea_surface_temperature_min"),
        wave_height_m=cur.get("wave_height"),
        observed_at=cur.get("time"),
    )


def fetch_cities(
    locs: list[Location], date: str, iso_date: str, settings: Settings
) -> tuple[list[CityObservation], list[str]]:
    out: list[CityObservation] = []
    errors: list[str] = []
    for chunk in _chunks(locs, _BATCH):
        try:
            resp = _get(WEATHER_URL, {
                "latitude": ",".join(str(c.latitude) for c in chunk),
                "longitude": ",".join(str(c.longitude) for c in chunk),
                "current": CURRENT_VARS, "daily": DAILY_VARS,
                "timezone": "auto", "forecast_days": 1,
            }, settings)
            for loc, obj in zip(chunk, _as_list(resp), strict=False):
                try:
                    out.append(_city_from(loc, date, iso_date, obj))
                except Exception as err:
                    errors.append(f"{loc.name}: {err}")
        except SourceError as err:
            errors.extend(f"{c.name}: {err}" for c in chunk)
    return out, errors


def fetch_ninos(
    locs: list[Location], date: str, iso_date: str, settings: Settings
) -> tuple[list[NinoObservation], list[str]]:
    out: list[NinoObservation] = []
    errors: list[str] = []
    for chunk in _chunks(locs, _BATCH):
        try:
            resp = _get(MARINE_URL, {
                "latitude": ",".join(str(c.latitude) for c in chunk),
                "longitude": ",".join(str(c.longitude) for c in chunk),
                "current": MARINE_CURRENT, "daily": MARINE_DAILY,
                "timezone": "auto", "forecast_days": 1,
            }, settings)
            for loc, obj in zip(chunk, _as_list(resp), strict=False):
                try:
                    out.append(_nino_from(loc, date, iso_date, obj))
                except Exception as err:
                    errors.append(f"{loc.name}: {err}")
        except SourceError as err:
            errors.extend(f"{c.name}: {err}" for c in chunk)
    return out, errors


def _mmddyyyy(iso: str) -> str:
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%m%d%Y")


def fetch_city_history(
    loc: Location, start: str, end: str, settings: Settings
) -> list[CityObservation]:
    """Daily history from the archive API. start/end are YYYY-MM-DD."""
    resp = _get(ARCHIVE_URL, {
        "latitude": loc.latitude, "longitude": loc.longitude,
        "start_date": start, "end_date": end,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto",
    }, settings)
    daily = resp.get("daily", {})
    times = daily.get("time", [])
    out: list[CityObservation] = []
    for i, iso in enumerate(times):
        tmax = daily.get("temperature_2m_max", [None] * len(times))[i]
        tmin = daily.get("temperature_2m_min", [None] * len(times))[i]
        mean = round((tmax + tmin) / 2, 1) if (tmax is not None and tmin is not None) else None
        out.append(CityObservation(
            date=_mmddyyyy(iso), iso_date=iso, country=loc.country, city=loc.name,
            latitude=loc.latitude, longitude=loc.longitude,
            temperature_c=mean, temperature_max_c=tmax, temperature_min_c=tmin,
            precipitation_mm=daily.get("precipitation_sum", [None] * len(times))[i],
            wind_speed_kmh=daily.get("wind_speed_10m_max", [None] * len(times))[i],
            observed_at=iso,
        ))
    return out


def fetch_nino_history(
    loc: Location, start: str, end: str, settings: Settings
) -> list[NinoObservation]:
    """Daily SST history for a Nino region. Best effort; marine archive may be limited."""
    resp = _get(MARINE_ARCHIVE_URL, {
        "latitude": loc.latitude, "longitude": loc.longitude,
        "start_date": start, "end_date": end,
        "daily": "sea_surface_temperature_max,sea_surface_temperature_min",
        "timezone": "auto",
    }, settings)
    daily = resp.get("daily", {})
    times = daily.get("time", [])
    out: list[NinoObservation] = []
    for i, iso in enumerate(times):
        smax = daily.get("sea_surface_temperature_max", [None] * len(times))[i]
        smin = daily.get("sea_surface_temperature_min", [None] * len(times))[i]
        mean = round((smax + smin) / 2, 2) if (smax is not None and smin is not None) else None
        out.append(NinoObservation(
            date=_mmddyyyy(iso), iso_date=iso, name=loc.name, region=loc.region,
            latitude=loc.latitude, longitude=loc.longitude,
            sea_surface_temperature_c=mean, sst_max_c=smax, sst_min_c=smin,
            observed_at=iso,
        ))
    return out
