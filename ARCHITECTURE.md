# Architecture

GeoStream Atlas is a small batch ETL pipeline. It favours correctness,
reproducibility and operational simplicity over scale, because the workload — a
few hundred API calls once a day — does not need distributed infrastructure. The
design borrows the *principles* large data teams care about (data contracts,
idempotency, observability, quality gates) and applies them at a size that stays
free to run and trivial to maintain.

## Pipeline stages

```
config ─▶ sources ─▶ models ─▶ quality ─▶ analysis ─▶ storage ─▶ git commit
 load     fetch       validate   gate       ENSO        write       (Actions)
```

1. **config** — loads declarative locations and env-driven settings.
2. **sources** — fetches each location from Open-Meteo concurrently, with
   exponential backoff and bounded timeouts.
3. **models** — every reading becomes a frozen, range-validated dataclass.
   Physically impossible values are rejected at the boundary.
4. **quality** — the day's batch must pass completeness and signal-presence
   checks before anything is written.
5. **analysis** — computes the ENSO anomaly and phase from Niño-region SST.
6. **storage** — writes date-partitioned JSON and upserts the master CSV.
7. **git** — GitHub Actions commits and pushes the result.

## Key decisions

### GitHub Actions as the runtime
A scheduled workflow gives a free, secure, maintenance-free daily job that can
write back to the repository using the built-in `GITHUB_TOKEN`. There is no host
to secure and no standing secret. The `contents: write` permission is the only
scope granted, and a `concurrency` group prevents overlapping runs from racing on
the same files.

### Open-Meteo as the source
Free, key-less, global coverage, and a marine endpoint for sea-surface
temperature. Key-less is a security feature: there is no credential to store or
leak. The trade-off is the free tier's non-commercial terms.

### Zero runtime dependencies
The collector uses only the standard library. This shrinks the supply-chain
attack surface to nothing in the hot path, keeps CI fast, and means a clone runs
anywhere Python 3.11+ exists. Dev tooling (ruff, mypy, pytest) is isolated to the
`dev` extra.

### Idempotency
`storage.write_day` rewrites a date's rows in the CSV instead of appending, and
per-day JSON files are overwritten in place. Re-running a day — a retry, a
backfill, a manual `workflow_dispatch` — converges to the same state. This is
what makes the daily job safe to re-trigger without corrupting history.

### Data contracts and quality gate
Validation lives in the model layer, so no invalid record can exist in memory.
The quality gate is a second, batch-level guard: if an upstream outage returns
mostly nulls, the run fails loudly and commits nothing rather than poisoning the
dataset with empty rows.

### Observability
Logs are structured JSON (one object per line) and every run writes a
`_manifest.json` with counts, per-location errors and timing. A failed or partial
day is diagnosable from the committed artifacts alone.

## ENSO method and its limits

NOAA's operational El Niño / La Niña index (the ONI) is a 3-month running mean of
the Niño 3.4 SST anomaly relative to a 30-year base period. This repository, at
launch, has no history and no official base period, so it computes a daily
*instantaneous* anomaly against approximate climatological means
(`analysis.CLIMATOLOGY_C`). Treat the daily phase as an early indicator, not an
official classification.

As `observations.csv` accumulates, the right next step is to derive a rolling
mean from the committed history and, eventually, replace the approximate
baselines with a proper 1991–2020 base-period climatology. The thresholds
(±0.5 °C) already follow the NOAA convention, so only the smoothing and baseline
need to mature.

## Scale and the dashboard

### Batched fetching
`sources.py` sends many coordinates per Open-Meteo call (the API returns an
array aligned to the input order) and chunks at 100 locations. A full run of 74
cities plus 4 ocean regions is a handful of HTTP requests, not 78 — this keeps
the job inside the free rate limits and finishes in a couple of seconds.

### Backfill
`python -m geostream backfill` pulls daily history from Open-Meteo's archive API
so the rolling index and forecast are meaningful from day one. `--csv-only`
updates the time-series CSV without writing per-day JSON partitions, which avoids
committing thousands of historical files for a one-off seed.

### Forecast
`forecast.py` reads `observations.csv`, builds the Niño 3.4 anomaly series,
smooths it into a 30-day rolling index and projects a short horizon with
least-squares linear regression. It is a trend/persistence baseline, honest about
not being a dynamical climate model.

### Dashboard
The frontend (`web/`) is a Vite + React + TypeScript app — Leaflet for the map,
Chart.js for the ENSO chart. It is fully static: rather than parsing the dataset
in the browser, `export.py` precomputes a compact `latest.json` and
`enso_timeseries.json` into `web/public/data`. The daily job regenerates and
commits that feed, and a Pages workflow rebuilds and deploys on every change to
`web/`. Keeping the site static means it hosts free on GitHub Pages with no
backend to secure.

## Extending

- **More locations**: edit `locations.json`. No code change.
- **More variables**: add fields to the `*Observation` models, the Open-Meteo
  query in `sources.py`, and the CSV schema in `storage.py`.
- **Better ENSO**: implement a rolling ONI over `observations.csv` and surface it
  in `enso.json` alongside the instantaneous value.
- **Backfill**: Open-Meteo has a historical archive API; a backfill command could
  reuse the same models, quality gate and storage to populate past dates.
