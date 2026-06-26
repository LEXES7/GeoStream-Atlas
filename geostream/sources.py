"""Open-Meteo client. Free, key-less, stdlib-only, with backoff retries."""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request

from .config import Settings
from .logging_setup import get_logger
from .models import CityObservation, Location, NinoObservation

log = get_logger(__name__)

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
_USER_AGENT = "GeoStream-Atlas/1.0"


class SourceError(RuntimeError):
    pass


def _get_json(url: str, params: dict, settings: Settings) -> dict:
    full = f"{url}?{urllib.parse.urlencode(params)}"
    last_err: Exception | None = None
    for attempt in range(1, settings.max_retries + 1):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": _USER_AGENT})
            with urllib.request.urlopen(req, timeout=settings.request_timeout_s) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as err:
            last_err = err
            backoff = min(2 ** attempt + random.uniform(0, 0.5), 20)
            log.warning(
                "upstream fetch failed, retrying",
                extra={"fields": {"url": url, "attempt": attempt, "backoff_s": round(backoff, 2)}},
            )
            if attempt < settings.max_retries:
                time.sleep(backoff)
    raise SourceError(f"{url} failed after {settings.max_retries} attempts: {last_err}")


def _first(daily: dict, key: str):
    vals = daily.get(key) or []
    return vals[0] if vals else None


def fetch_city(loc: Location, date: str, iso_date: str, settings: Settings) -> CityObservation:
    data = _get_json(WEATHER_URL, {
        "latitude": loc.latitude, "longitude": loc.longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,precipitation,"
            "wind_speed_10m,surface_pressure"
        ),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto", "forecast_days": 1,
    }, settings)
    cur, daily = data.get("current", {}), data.get("daily", {})
    return CityObservation(
        date=date, iso_date=iso_date, country=loc.country, city=loc.name,
        latitude=loc.latitude, longitude=loc.longitude,
        temperature_c=cur.get("temperature_2m"),
        temperature_max_c=_first(daily, "temperature_2m_max"),
        temperature_min_c=_first(daily, "temperature_2m_min"),
        humidity_pct=cur.get("relative_humidity_2m"),
        precipitation_mm=_first(daily, "precipitation_sum"),
        wind_speed_kmh=cur.get("wind_speed_10m"),
        surface_pressure_hpa=cur.get("surface_pressure"),
        observed_at=cur.get("time"),
    )


def fetch_nino(loc: Location, date: str, iso_date: str, settings: Settings) -> NinoObservation:
    data = _get_json(MARINE_URL, {
        "latitude": loc.latitude, "longitude": loc.longitude,
        "current": "sea_surface_temperature",
        "daily": "sea_surface_temperature_max,sea_surface_temperature_min",
        "timezone": "auto", "forecast_days": 1,
    }, settings)
    cur, daily = data.get("current", {}), data.get("daily", {})
    return NinoObservation(
        date=date, iso_date=iso_date, name=loc.name, region=loc.region,
        latitude=loc.latitude, longitude=loc.longitude,
        sea_surface_temperature_c=cur.get("sea_surface_temperature"),
        sst_max_c=_first(daily, "sea_surface_temperature_max"),
        sst_min_c=_first(daily, "sea_surface_temperature_min"),
        observed_at=cur.get("time"),
    )
