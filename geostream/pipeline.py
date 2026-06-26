"""Orchestrates a single day's collection run."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any

from . import analysis, quality, storage
from .config import Settings, load_locations
from .logging_setup import get_logger
from .models import CityObservation, Location, NinoObservation, RunManifest
from .sources import fetch_city, fetch_nino

log = get_logger(__name__)


def run(settings: Settings | None = None) -> RunManifest:
    settings = settings or Settings.from_env()
    started = datetime.now(UTC)
    date = started.strftime("%m%d%Y")
    iso_date = started.strftime("%Y-%m-%d")

    cities_cfg, nino_cfg = load_locations()
    log.info(
        "run started",
        extra={"fields": {"date": date, "cities": len(cities_cfg), "nino": len(nino_cfg)}},
    )

    errors: list[str] = []
    cities: list[CityObservation] = []
    nino: list[NinoObservation] = []

    with ThreadPoolExecutor(max_workers=settings.max_workers) as pool:
        futures: dict[Future[Any], Location] = {}
        for loc in cities_cfg:
            futures[pool.submit(fetch_city, loc, date, iso_date, settings)] = loc
        for loc in nino_cfg:
            futures[pool.submit(fetch_nino, loc, date, iso_date, settings)] = loc

        for fut in as_completed(futures):
            loc = futures[fut]
            try:
                result = fut.result()
                (nino if isinstance(result, NinoObservation) else cities).append(result)
            except Exception as err:  # one bad location must not fail the run
                errors.append(f"{loc.name}: {err}")
                log.warning(
                    "location failed",
                    extra={"fields": {"location": loc.name, "error": str(err)}},
                )

    report = quality.evaluate(cities, nino)
    enso = analysis.analyze(date, iso_date, nino)

    if not report.passed:
        log.error("quality gate failed", extra={"fields": {"failures": report.failures}})
        raise RuntimeError(f"Quality gate failed: {report.failures}")

    finished = datetime.now(UTC)
    manifest = RunManifest(
        date=date, iso_date=iso_date,
        started_utc=started.isoformat(), finished_utc=finished.isoformat(),
        cities_requested=len(cities_cfg), cities_ok=len(cities),
        nino_requested=len(nino_cfg), nino_ok=len(nino),
        quality_passed=report.passed, errors=errors,
    )

    storage.write_day(settings.data_dir, date, iso_date, cities, nino, enso, manifest)
    log.info("run finished", extra={"fields": {
        "date": date, "cities_ok": len(cities), "nino_ok": len(nino),
        "enso_phase": enso.phase, "nino34_anomaly_c": enso.nino34_anomaly_c,
    }})
    return manifest
