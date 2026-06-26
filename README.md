# GeoStream Atlas

A daily, self-updating climate dataset and live dashboard for global weather and
El Niño (ENSO) monitoring. Every day a GitHub Actions job collects weather for
cities worldwide plus sea-surface temperature for the Pacific Niño regions,
validates it, computes the current ENSO signal and a trend forecast, commits the
results back to this repository, and redeploys a React dashboard.

No servers, no API keys, no manual steps. The repository *is* the dataset, the
pipeline that builds it, and the site that visualises it.

**Live dashboard:** https://lexes7.github.io/GeoStream-Atlas/

## Why this design

- **GitHub Actions is the runtime.** A scheduled workflow is a free, secure,
  zero-maintenance way to run a daily job and write results to git. No server to
  patch, no long-lived credential — only the built-in `GITHUB_TOKEN`.
- **Open-Meteo is the data source.** Free, no API key, global weather plus a
  marine endpoint for sea-surface temperature. No key means no secret to leak.
- **Stdlib only at runtime.** The collector has zero third-party dependencies, so
  there is nothing to audit or patch in the hot path and CI is fast.
- **Batched requests.** Hundreds of locations are fetched in a handful of calls,
  staying well inside the free rate limits.

## What it tracks

- **74 cities across 57 countries** (all continents) — temperature, apparent
  temperature, humidity, precipitation, cloud cover, wind, pressure, UV.
- **4 Pacific Niño regions** — sea-surface temperature and wave height.
- **ENSO signal** — daily Niño 3.4 anomaly, a 30-day rolling index (ONI-style)
  and a linear-trend projection.

## Data layout

```
data/
  MMDDYYYY/
    <Country>/<City>.json        per-city weather snapshot
    _nino_regions/<Region>.json  per-region sea-surface temperature
    enso.json                    daily El Niño / La Niña read-out
    _manifest.json               run metadata (counts, errors, timing)
  observations.csv               append-only long-format table of every day
web/public/data/
  latest.json                    compact snapshot the dashboard reads
  enso_timeseries.json           anomaly, rolling index and projection
```

Dates use the `MMDDYYYY` format. `observations.csv` is the analysis-ready time
series; the per-day JSON files are human-readable snapshots.

## ENSO signal

Sea-surface temperature in the Niño 3.4 region is the canonical El Niño / La Niña
indicator. Each day the pipeline computes the SST anomaly against a climatological
baseline and classifies the phase:

| Niño 3.4 anomaly | Phase    |
| ---------------- | -------- |
| ≥ +0.5 °C        | El Niño  |
| ≤ −0.5 °C        | La Niña  |
| otherwise        | Neutral  |

The dashboard shows the 30-day rolling index and a trend projection. See
[ARCHITECTURE.md](ARCHITECTURE.md) for the method and its limits.

## Run it locally

```bash
pip install -e ".[dev]"
python -m geostream                 # collect today's data into ./data
python -m geostream export          # rebuild the dashboard feed only
python -m geostream backfill --start 2026-03-01 --end 2026-06-01 --csv-only

ruff check geostream tests          # lint
mypy geostream                      # type check
pytest                              # tests
```

Re-running a day is safe: it overwrites that day's rows rather than duplicating
them.

### Dashboard

```bash
cd web
npm install
npm run dev      # local dev server
npm run build    # production build into web/dist
```

The dashboard (Vite + React + TypeScript, Leaflet map, Chart.js) reads the static
JSON in `web/public/data`. It is rebuilt and deployed to GitHub Pages on every
push that touches `web/`.

## Add a location

Edit [locations.json](locations.json) and add an entry under `cities`:

```json
{ "city": "Tokyo", "country": "Japan", "latitude": 35.6762, "longitude": 139.6503 }
```

The next run picks it up automatically. No code change needed.

## Configuration

| Variable                | Default | Purpose                       |
| ----------------------- | ------- | ----------------------------- |
| `GEOSTREAM_MAX_WORKERS` | 8       | Reserved for parallel work    |
| `GEOSTREAM_TIMEOUT`     | 30      | Per-request timeout (seconds) |
| `GEOSTREAM_RETRIES`     | 3       | Retry attempts with backoff   |
| `GEOSTREAM_DATA_DIR`    | ./data  | Output directory              |

## Data source and license

Weather and marine data from [Open-Meteo](https://open-meteo.com) under CC BY 4.0.
Code in this repository is MIT licensed. The free Open-Meteo tier is intended for
non-commercial use; check their terms before commercial deployment.
