"""Builds the static JSON feed the dashboard reads.

The dashboard is a static site, so instead of parsing the whole dataset in the
browser we precompute compact summaries here and write them to web/data/.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from . import forecast
from .analysis import EnsoSnapshot
from .models import CityObservation, NinoObservation

WEB_DATA = Path(__file__).resolve().parent.parent / "web" / "public" / "data"
INTRADAY_SLOTS = 48


def build(
    data_dir: Path,
    date: str,
    iso_date: str,
    slot: str,
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
        "slot": slot,
        "generated_utc": datetime.now(UTC).isoformat(),
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

    (web_data / "intraday.json").write_text(
        json.dumps(_intraday(data_dir), indent=2), encoding="utf-8"
    )

    (web_data / "city_history.json").write_text(
        json.dumps(_city_history(data_dir), separators=(",", ":")), encoding="utf-8"
    )


def _city_history(data_dir: Path, slots: int = 48) -> dict:
    """Recent temperature series per city, keyed by 'City|Country'."""
    path = data_dir / "observations.csv"
    series: dict[str, dict[str, float]] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("type") != "city" or not row.get("temp_c") or not row.get("slot"):
                    continue
                key = f"{row['location']}|{row['country']}"
                series.setdefault(key, {})[row["slot"]] = float(row["temp_c"])

    out: dict[str, list[dict]] = {}
    for key, points in series.items():
        recent = sorted(points)[-slots:]
        out[key] = [{"slot": s, "value": points[s]} for s in recent]
    return out


def _intraday(data_dir: Path) -> dict:
    """Per-slot global average temperature and Nino 3.4 SST over recent slots."""
    path = data_dir / "observations.csv"
    temps: dict[str, list[float]] = {}
    sst: dict[str, float] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                slot = row.get("slot") or ""
                if not slot:
                    continue
                if row.get("type") == "city" and row.get("temp_c"):
                    temps.setdefault(slot, []).append(float(row["temp_c"]))
                elif row.get("location") == "Nino_3_4" and row.get("sea_surface_temp_c"):
                    sst[slot] = float(row["sea_surface_temp_c"])

    slots = sorted(set(temps) | set(sst))[-INTRADAY_SLOTS:]
    return {
        "temp": [
            {"slot": s, "value": round(sum(temps[s]) / len(temps[s]), 2)}
            for s in slots
            if s in temps
        ],
        "sst": [{"slot": s, "value": sst[s]} for s in slots if s in sst],
    }


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
