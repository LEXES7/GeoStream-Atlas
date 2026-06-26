import csv

from geostream.analysis import analyze
from geostream.models import CityObservation, NinoObservation, RunManifest
from geostream.storage import write_day


def _manifest(date="06262026"):
    return RunManifest(
        date=date, iso_date="2026-06-26", started_utc="t", finished_utc="t",
        cities_requested=1, cities_ok=1, nino_requested=1, nino_ok=1,
        quality_passed=True,
    )


def _city(date="06262026"):
    return CityObservation(
        date=date, iso_date="2026-06-26", country="Sri Lanka", city="Colombo",
        latitude=6.9, longitude=79.8, temperature_c=30.0,
    )


def _nino(date="06262026"):
    return NinoObservation(
        date=date, iso_date="2026-06-26", name="Nino_3_4", region="Pacific",
        latitude=0.0, longitude=-170.0, sea_surface_temperature_c=27.0,
    )


def _rowcount(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def test_write_day_is_idempotent(tmp_path):
    date = "06262026"
    enso = analyze(date, "2026-06-26", [_nino()])
    for _ in range(3):
        write_day(tmp_path, date, "2026-06-26", [_city()], [_nino()], enso, _manifest())

    csv_path = tmp_path / "observations.csv"
    assert _rowcount(csv_path) == 2  # 1 city + 1 nino, no duplicates
    assert (tmp_path / date / "Sri_Lanka" / "Colombo.json").exists()
    assert (tmp_path / date / "enso.json").exists()


def test_write_day_appends_distinct_dates(tmp_path):
    for date in ("06262026", "06272026"):
        enso = analyze(date, "2026-06-26", [_nino(date)])
        write_day(tmp_path, date, "2026-06-26", [_city(date)], [_nino(date)], enso, _manifest(date))
    assert _rowcount(tmp_path / "observations.csv") == 4
