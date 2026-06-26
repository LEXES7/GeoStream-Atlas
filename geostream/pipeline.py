"""Orchestrates a single day's collection run."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from . import analysis, briefing, export, quality, storage
from .config import Settings, load_locations
from .logging_setup import get_logger
from .models import CityObservation, NinoObservation, RunManifest
from .sources import (
    fetch_cities,
    fetch_city_history,
    fetch_nino_history,
    fetch_ninos,
)

log = get_logger(__name__)


def run(settings: Settings | None = None) -> RunManifest:
    settings = settings or Settings.from_env()
    started = datetime.now(UTC)
    date = started.strftime("%m%d%Y")
    iso_date = started.strftime("%Y-%m-%d")
    slot = started.strftime("%Y-%m-%dT%H:00")

    cities_cfg, nino_cfg = load_locations()
    log.info(
        "run started",
        extra={"fields": {"date": date, "cities": len(cities_cfg), "nino": len(nino_cfg)}},
    )

    cities, city_errors = fetch_cities(cities_cfg, date, iso_date, settings)
    nino, nino_errors = fetch_ninos(nino_cfg, date, iso_date, settings)
    errors = city_errors + nino_errors
    for msg in errors:
        log.warning("location failed", extra={"fields": {"error": msg}})

    report = quality.evaluate(cities, nino)
    enso = analysis.analyze(date, iso_date, nino)

    if not report.passed:
        log.error("quality gate failed", extra={"fields": {"failures": report.failures}})
        raise RuntimeError(f"Quality gate failed: {report.failures}")

    finished = datetime.now(UTC)
    manifest = RunManifest(
        date=date, iso_date=iso_date, slot=slot,
        started_utc=started.isoformat(), finished_utc=finished.isoformat(),
        cities_requested=len(cities_cfg), cities_ok=len(cities),
        nino_requested=len(nino_cfg), nino_ok=len(nino),
        quality_passed=report.passed, errors=errors,
    )

    storage.write_day(settings.data_dir, date, iso_date, slot, cities, nino, enso, manifest)
    export.build(settings.data_dir, date, iso_date, slot, cities, nino, enso)
    try:
        briefing.write(export.WEB_DATA)
    except Exception as err:  # an AI hiccup must never fail a collection
        log.warning("briefing step failed", extra={"fields": {"error": str(err)}})
    log.info("run finished", extra={"fields": {
        "slot": slot, "cities_ok": len(cities), "nino_ok": len(nino),
        "enso_phase": enso.phase, "nino34_anomaly_c": enso.nino34_anomaly_c,
    }})
    return manifest


def backfill(
    start: str, end: str, settings: Settings | None = None, csv_only: bool = False
) -> int:
    """Populate historical dates from the archive API. start/end are YYYY-MM-DD."""
    settings = settings or Settings.from_env()
    cities_cfg, nino_cfg = load_locations()
    log.info("backfill started", extra={"fields": {"start": start, "end": end}})

    cities_by_date: dict[str, list[CityObservation]] = defaultdict(list)
    nino_by_date: dict[str, list[NinoObservation]] = defaultdict(list)

    for loc in cities_cfg:
        try:
            for c_obs in fetch_city_history(loc, start, end, settings):
                cities_by_date[c_obs.iso_date].append(c_obs)
        except Exception as err:
            log.warning(
                "city history failed",
                extra={"fields": {"city": loc.name, "error": str(err)}},
            )

    for loc in nino_cfg:
        try:
            for n_obs in fetch_nino_history(loc, start, end, settings):
                nino_by_date[n_obs.iso_date].append(n_obs)
        except Exception as err:
            log.warning(
                "nino history failed",
                extra={"fields": {"region": loc.name, "error": str(err)}},
            )

    all_dates = sorted(set(cities_by_date) | set(nino_by_date))
    for iso_date in all_dates:
        date = datetime.strptime(iso_date, "%Y-%m-%d").strftime("%m%d%Y")
        slot = f"{iso_date}T00:00"
        cities = cities_by_date.get(iso_date, [])
        nino = nino_by_date.get(iso_date, [])
        enso = analysis.analyze(date, iso_date, nino)
        if csv_only:
            storage.upsert_rows(settings.data_dir, date, iso_date, slot, cities, nino, enso)
        else:
            manifest = RunManifest(
                date=date, iso_date=iso_date, slot=slot,
                started_utc=iso_date, finished_utc=iso_date,
                cities_requested=len(cities_cfg), cities_ok=len(cities),
                nino_requested=len(nino_cfg), nino_ok=len(nino),
                quality_passed=True, errors=[],
            )
            storage.write_day(settings.data_dir, date, iso_date, slot, cities, nino, enso, manifest)

    log.info("backfill finished", extra={"fields": {"days": len(all_dates)}})
    return len(all_dates)
