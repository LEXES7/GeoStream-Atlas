from geostream.models import CityObservation, NinoObservation
from geostream.quality import evaluate


def _city(temp):
    return CityObservation(
        date="06262026", iso_date="2026-06-26", country="X", city="Y",
        latitude=0.0, longitude=0.0, temperature_c=temp,
    )


def _nino(sst):
    return NinoObservation(
        date="06262026", iso_date="2026-06-26", name="Nino_3_4", region="P",
        latitude=0.0, longitude=-170.0, sea_surface_temperature_c=sst,
    )


def test_empty_batch_fails():
    assert evaluate([], []).passed is False


def test_low_fill_fails():
    cities = [_city(30.0), _city(None), _city(None)]
    assert evaluate(cities, []).passed is False


def test_good_batch_passes():
    cities = [_city(30.0), _city(28.0)]
    assert evaluate(cities, [_nino(27.0)]).passed is True
