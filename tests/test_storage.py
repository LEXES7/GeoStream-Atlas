import csv

from geostream.analysis import analyze
from geostream.models import CityObservation, NinoObservation, RunManifest
from geostream.storage import write_day

SLOT = "2026-06-26T08:00"


def _manifest(slot=SLOT):
    return RunManifest(
        date="06262026", iso_date="2026-06-26", slot=slot, started_utc="t", finished_utc="t",
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


def test_write_day_is_idempotent_within_slot(tmp_path):
    enso = analyze("06262026", "2026-06-26", [_nino()])
    for _ in range(3):
        write_day(tmp_path, "06262026", "2026-06-26", SLOT, [_city()], [_nino()], enso, _manifest())

    csv_path = tmp_path / "observations.csv"
    assert _rowcount(csv_path) == 2  # 1 city + 1 nino, no duplicates
    assert (tmp_path / "06262026" / "Sri_Lanka" / "Colombo.json").exists()
    assert (tmp_path / "06262026" / "enso.json").exists()


def test_intraday_slots_accumulate(tmp_path):
    enso = analyze("06262026", "2026-06-26", [_nino()])
    for slot in ("2026-06-26T08:00", "2026-06-26T10:00", "2026-06-26T12:00"):
        write_day(
            tmp_path, "06262026", "2026-06-26", slot,
            [_city()], [_nino()], enso, _manifest(slot),
        )
    # Same day, three slots -> three slots x 2 rows kept.
    assert _rowcount(tmp_path / "observations.csv") == 6
