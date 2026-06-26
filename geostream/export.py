"""Builds the static JSON feed the dashboard reads.

The dashboard is a static site, so instead of parsing the whole dataset in the
browser we precompute a compact summary here and write it to web/data/. This
keeps the page fast and the frontend simple.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import forecast
from .analysis import EnsoSnapshot
from .models import CityObservation, NinoObservation

WEB_DATA = Path(__file__).resolve().parent.parent / "web" / "public" / "data"


def build(
    data_dir: Path,
    date: str,
    iso_date: str,
    cities: list[CityObservation],
    nino: list[NinoObservation],
    enso: EnsoSnapshot,
    web_data: Path | None = None,
) -> None:
    web_data = web_data or WEB_DATA
    web_data.mkdir(parents=True, exist_ok=True)

    fc = forecast.build(data_dir)

    latest = {
        "date": date,
        "iso_date": iso_date,
        "enso": enso.to_dict(),
        "forecast": {
            "current_oni": fc.current_oni,
            "current_phase": fc.current_phase,
            "trend_per_month": fc.trend_per_month,
            "note": fc.note,
        },
        "stats": _stats(cities),
        "cities": [
            {
                "city": c.city, "country": c.country,
                "latitude": c.latitude, "longitude": c.longitude,
                "temperature_c": c.temperature_c,
                "apparent_temperature_c": c.apparent_temperature_c,
                "humidity_pct": c.humidity_pct,
                "precipitation_mm": c.precipitation_mm,
                "cloud_cover_pct": c.cloud_cover_pct,
                "wind_speed_kmh": c.wind_speed_kmh,
                "weather_code": c.weather_code,
            }
            for c in sorted(cities, key=lambda x: (x.country, x.city))
        ],
        "nino_regions": [n.to_dict() for n in nino],
    }
    (web_data / "latest.json").write_text(json.dumps(latest, indent=2), encoding="utf-8")

    timeseries = {
        "anomaly": [p.to_dict() for p in fc.anomaly_series],
        "rolling": [p.to_dict() for p in fc.rolling_series],
        "projection": [p.to_dict() for p in fc.projection],
        "note": fc.note,
    }
    (web_data / "enso_timeseries.json").write_text(
        json.dumps(timeseries, indent=2), encoding="utf-8"
    )


def _stats(cities: list[CityObservation]) -> dict:
    temps = [c.temperature_c for c in cities if c.temperature_c is not None]
    if not temps:
        return {"city_count": len(cities), "country_count": 0}
    hottest = max(cities, key=lambda c: (c.temperature_c is not None, c.temperature_c or -999))
    coldest = min(cities, key=lambda c: (c.temperature_c is None, c.temperature_c or 999))
    return {
        "city_count": len(cities),
        "country_count": len({c.country for c in cities}),
        "avg_temp_c": round(sum(temps) / len(temps), 1),
        "hottest": {
            "city": hottest.city, "country": hottest.country, "temp_c": hottest.temperature_c,
        },
        "coldest": {
            "city": coldest.city, "country": coldest.country, "temp_c": coldest.temperature_c,
        },
    }
