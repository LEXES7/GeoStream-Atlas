import pytest

from geostream.models import (
    CityObservation,
    Location,
    NinoObservation,
    ValidationError,
)


def test_location_rejects_bad_latitude():
    with pytest.raises(ValidationError):
        Location(name="x", latitude=200.0, longitude=0.0)


def test_location_requires_name():
    with pytest.raises(ValidationError):
        Location(name="", latitude=0.0, longitude=0.0)


def test_city_rejects_impossible_temperature():
    with pytest.raises(ValidationError):
        CityObservation(
            date="06262026", iso_date="2026-06-26", country="X", city="Y",
            latitude=0.0, longitude=0.0, temperature_c=999.0,
        )


def test_city_accepts_high_altitude_pressure():
    obs = CityObservation(
        date="06262026", iso_date="2026-06-26", country="Ecuador", city="Quito",
        latitude=-0.18, longitude=-78.46, surface_pressure_hpa=721.8,
    )
    assert obs.surface_pressure_hpa == 721.8


def test_nino_allows_none_values():
    obs = NinoObservation(
        date="06262026", iso_date="2026-06-26", name="Nino_3_4",
        region="Pacific", latitude=0.0, longitude=-170.0,
    )
    assert obs.sea_surface_temperature_c is None
