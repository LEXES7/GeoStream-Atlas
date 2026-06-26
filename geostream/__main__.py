"""CLI entrypoint: python -m geostream [collect|backfill|export]"""

from __future__ import annotations

import argparse
import os
import sys

from .config import Settings, load_locations
from .pipeline import backfill, run


def _emit_output(**values: object) -> None:
    target = os.environ.get("GITHUB_OUTPUT")
    if not target:
        return
    with open(target, "a", encoding="utf-8") as fh:
        for key, value in values.items():
            fh.write(f"{key}={value}\n")


def _collect() -> int:
    try:
        manifest = run()
    except Exception as err:
        print(f"collection failed: {err}", file=sys.stderr)
        return 1
    stamp = manifest.slot.replace("T", " ") + " UTC"
    _emit_output(
        slot=manifest.slot, stamp=stamp, cities_ok=manifest.cities_ok, nino_ok=manifest.nino_ok
    )
    return 0


def _backfill(start: str, end: str, csv_only: bool) -> int:
    try:
        days = backfill(start, end, csv_only=csv_only)
    except Exception as err:
        print(f"backfill failed: {err}", file=sys.stderr)
        return 1
    print(f"backfilled {days} day(s).")
    return 0


def _export() -> int:
    from datetime import UTC, datetime

    from . import analysis, export
    from .sources import fetch_cities, fetch_ninos

    settings = Settings.from_env()
    now = datetime.now(UTC)
    date, iso_date = now.strftime("%m%d%Y"), now.strftime("%Y-%m-%d")
    cities_cfg, nino_cfg = load_locations()
    cities, _ = fetch_cities(cities_cfg, date, iso_date, settings)
    nino, _ = fetch_ninos(nino_cfg, date, iso_date, settings)
    enso = analysis.analyze(date, iso_date, nino)
    export.build(settings.data_dir, date, iso_date, cities, nino, enso)
    print("dashboard data exported to web/public/data/.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="geostream")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("collect", help="collect today's data (default)")
    bf = sub.add_parser("backfill", help="populate historical dates")
    bf.add_argument("--start", required=True, help="start date YYYY-MM-DD")
    bf.add_argument("--end", required=True, help="end date YYYY-MM-DD")
    bf.add_argument(
        "--csv-only", action="store_true", help="update the CSV only, no JSON partitions"
    )
    sub.add_parser("export", help="rebuild dashboard data only")

    args = parser.parse_args()
    if args.command == "backfill":
        return _backfill(args.start, args.end, args.csv_only)
    if args.command == "export":
        return _export()
    return _collect()


if __name__ == "__main__":
    raise SystemExit(main())
