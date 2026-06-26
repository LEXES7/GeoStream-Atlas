# GeoStream Atlas

A daily, self-updating climate dataset for global weather and El Niño (ENSO)
monitoring. Every day a GitHub Actions job collects weather for a set of world
cities and sea-surface temperature for the Pacific Niño regions, validates it,
computes the current ENSO signal, and commits the results back to this
repository — partitioned by date, country and city.

No servers, no API keys, no manual steps. The repository *is* the dataset and the
pipeline that builds it.

## Why this design

- **GitHub Actions is the runtime.** A scheduled workflow is a free, secure,
  zero-maintenance way to run a daily job and write the results to git. There is
  no server to patch and no long-lived credential — only the built-in
  `GITHUB_TOKEN`, scoped to write contents.
- **Open-Meteo is the data source.** It is free, requires no API key, and covers
  global weather plus a marine endpoint for sea-surface temperature. No key means
  no secret to leak.
- **Stdlib only at runtime.** The collector has zero third-party dependencies, so
  there is nothing to audit or patch in the hot path and CI is fast.

## Data layout

```
data/
  MMDDYYYY/
    <Country>/<City>.json        per-city weather snapshot
    _nino_regions/<Region>.json  per-region sea-surface temperature
    enso.json                    daily El Niño / La Niña read-out
    _manifest.json               run metadata (counts, errors, timing)
  observations.csv               append-only long-format table of every day
```

Dates use the `MMDDYYYY` format. `observations.csv` is the analysis-ready
time series; the per-day JSON files are human-readable snapshots.

## ENSO signal

Sea-surface temperature in the Niño 3.4 region is the canonical El Niño / La Niña
indicator. Each day the pipeline computes the SST anomaly against a climatological
baseline and classifies the phase:

| Niño 3.4 anomaly | Phase    |
| ---------------- | -------- |
| ≥ +0.5 °C        | El Niño  |
| ≤ −0.5 °C        | La Niña  |
| otherwise        | Neutral  |

This is a daily instantaneous indicator, not the smoothed 3-month ONI that NOAA
publishes. See [ARCHITECTURE.md](ARCHITECTURE.md) for the full method and its
limits.

## Run it locally

```bash
pip install -e ".[dev]"
python -m geostream          # collect today's data into ./data
ruff check geostream tests   # lint
mypy geostream               # type check
pytest                       # tests
```

Re-running for the same day is safe: it overwrites that day's rows rather than
duplicating them.

## Add a location

Edit [locations.json](locations.json) and add an entry under `cities`:

```json
{ "city": "Tokyo", "country": "Japan", "latitude": 35.6762, "longitude": 139.6503 }
```

The next run picks it up automatically. No code change needed.

## Configuration

| Variable                  | Default | Purpose                          |
| ------------------------- | ------- | -------------------------------- |
| `GEOSTREAM_MAX_WORKERS`   | 8       | Concurrent API fetches           |
| `GEOSTREAM_TIMEOUT`       | 30      | Per-request timeout (seconds)    |
| `GEOSTREAM_RETRIES`       | 3       | Retry attempts with backoff      |
| `GEOSTREAM_DATA_DIR`      | ./data  | Output directory                 |

## Data source and license

Weather and marine data from [Open-Meteo](https://open-meteo.com) under
CC BY 4.0. Code in this repository is MIT licensed. The free Open-Meteo tier is
intended for non-commercial use; check their terms before commercial deployment.
