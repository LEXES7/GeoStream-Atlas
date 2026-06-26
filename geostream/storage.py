"""Idempotent writers. Re-running a date replaces that date's rows, never dupes."""

from __future__ import annotations

import csv
import json
from collections import OrderedDict
from pathlib import Path

from .analysis import EnsoSnapshot
from .models import CityObservation, NinoObservation, RunManifest

CSV_FIELDS = [
    "date", "iso_date", "type", "country", "location", "latitude", "longitude",
    "temp_c", "temp_max_c", "temp_min_c", "apparent_temp_c", "humidity_pct",
    "precip_mm", "cloud_pct", "wind_kmh", "wind_dir_deg", "pressure_hpa",
    "pressure_msl_hpa", "uv_index_max", "weather_code",
    "sea_surface_temp_c", "wave_height_m", "sst_anomaly_c", "enso_phase",
]


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip().replace(" ", "_")


def write_day(
    data_dir: Path,
    date: str,
    iso_date: str,
    cities: list[CityObservation],
    nino: list[NinoObservation],
    enso: EnsoSnapshot,
    manifest: RunManifest,
) -> None:
    day_dir = data_dir / date
    day_dir.mkdir(parents=True, exist_ok=True)

    for c in cities:
        country_dir = day_dir / _safe(c.country or "Unknown")
        country_dir.mkdir(parents=True, exist_ok=True)
        (country_dir / f"{_safe(c.city)}.json").write_text(
            json.dumps(c.to_dict(), indent=2), encoding="utf-8"
        )

    if nino:
        nino_dir = day_dir / "_nino_regions"
        nino_dir.mkdir(parents=True, exist_ok=True)
        for n in nino:
            (nino_dir / f"{_safe(n.name)}.json").write_text(
                json.dumps(n.to_dict(), indent=2), encoding="utf-8"
            )

    (day_dir / "enso.json").write_text(json.dumps(enso.to_dict(), indent=2), encoding="utf-8")
    (day_dir / "_manifest.json").write_text(
        json.dumps(manifest.to_dict(), indent=2), encoding="utf-8"
    )

    upsert_rows(data_dir, date, iso_date, cities, nino, enso)
    _write_commit_plan(data_dir, date, cities, nino)


def upsert_rows(
    data_dir: Path,
    date: str,
    iso_date: str,
    cities: list[CityObservation],
    nino: list[NinoObservation],
    enso: EnsoSnapshot,
) -> None:
    """Update only the master CSV for a date (no per-day JSON partitions)."""
    anomaly_by_region = {r.name: r for r in enso.regions}
    rows = _build_rows(date, iso_date, cities, nino, anomaly_by_region)
    _upsert_csv(data_dir / "observations.csv", date, rows)


def _write_commit_plan(
    data_dir: Path,
    date: str,
    cities: list[CityObservation],
    nino: list[NinoObservation],
) -> None:
    prefix = data_dir.name
    by_country: OrderedDict[str, int] = OrderedDict()
    for c in cities:
        by_country[c.country or "Unknown"] = by_country.get(c.country or "Unknown", 0) + 1

    lines: list[str] = []
    for country, count in by_country.items():
        path = f"{prefix}/{date}/{_safe(country)}"
        label = f"{count} location{'s' if count != 1 else ''}"
        lines.append(f"{path}\t{country} weather, {label} {date}")
    if nino:
        lines.append(f"{prefix}/{date}/_nino_regions\tPacific Nino regions SST {date}")

    (data_dir.parent / "commit_plan.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_rows(date, iso_date, cities, nino, anomaly_by_region) -> list[dict]:
    rows: list[dict] = []
    for c in cities:
        rows.append({
            "date": date, "iso_date": iso_date, "type": "city",
            "country": c.country, "location": c.city,
            "latitude": c.latitude, "longitude": c.longitude,
            "temp_c": c.temperature_c, "temp_max_c": c.temperature_max_c,
            "temp_min_c": c.temperature_min_c, "apparent_temp_c": c.apparent_temperature_c,
            "humidity_pct": c.humidity_pct, "precip_mm": c.precipitation_mm,
            "cloud_pct": c.cloud_cover_pct, "wind_kmh": c.wind_speed_kmh,
            "wind_dir_deg": c.wind_direction_deg, "pressure_hpa": c.surface_pressure_hpa,
            "pressure_msl_hpa": c.pressure_msl_hpa, "uv_index_max": c.uv_index_max,
            "weather_code": c.weather_code, "sea_surface_temp_c": "",
            "wave_height_m": "", "sst_anomaly_c": "", "enso_phase": "",
        })
    for n in nino:
        anom = anomaly_by_region.get(n.name)
        rows.append({
            "date": date, "iso_date": iso_date, "type": "nino_region",
            "country": "", "location": n.name,
            "latitude": n.latitude, "longitude": n.longitude,
            "temp_c": "", "temp_max_c": "", "temp_min_c": "", "apparent_temp_c": "",
            "humidity_pct": "", "precip_mm": "", "cloud_pct": "", "wind_kmh": "",
            "wind_dir_deg": "", "pressure_hpa": "", "pressure_msl_hpa": "",
            "uv_index_max": "", "weather_code": "",
            "sea_surface_temp_c": n.sea_surface_temperature_c,
            "wave_height_m": n.wave_height_m,
            "sst_anomaly_c": anom.anomaly_c if anom else "",
            "enso_phase": anom.phase if anom else "",
        })
    return rows


def _upsert_csv(path: Path, date: str, rows: list[dict]) -> None:
    existing: list[dict] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            existing = [r for r in csv.DictReader(fh) if r.get("date") != date]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(rows)
