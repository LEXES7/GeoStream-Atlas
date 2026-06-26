"""Typed, validated records that flow through the pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


class ValidationError(ValueError):
    pass


def _check_range(name: str, value: Optional[float], low: float, high: float) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be numeric, got {type(value).__name__}")
    if not (low <= value <= high):
        raise ValidationError(f"{name}={value} outside plausible range [{low}, {high}]")


@dataclass(frozen=True, slots=True)
class Location:
    name: str
    latitude: float
    longitude: float
    country: str = ""
    region: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValidationError("Location.name is required")
        _check_range("latitude", self.latitude, -90.0, 90.0)
        _check_range("longitude", self.longitude, -180.0, 180.0)


@dataclass(frozen=True, slots=True)
class CityObservation:
    date: str          # MMDDYYYY
    iso_date: str      # YYYY-MM-DD
    country: str
    city: str
    latitude: float
    longitude: float
    temperature_c: Optional[float] = None
    temperature_max_c: Optional[float] = None
    temperature_min_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    precipitation_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    surface_pressure_hpa: Optional[float] = None
    observed_at: Optional[str] = None

    def __post_init__(self) -> None:
        _check_range("temperature_c", self.temperature_c, -90.0, 60.0)
        _check_range("temperature_max_c", self.temperature_max_c, -90.0, 60.0)
        _check_range("temperature_min_c", self.temperature_min_c, -90.0, 60.0)
        _check_range("humidity_pct", self.humidity_pct, 0.0, 100.0)
        _check_range("precipitation_mm", self.precipitation_mm, 0.0, 2000.0)
        _check_range("wind_speed_kmh", self.wind_speed_kmh, 0.0, 500.0)
        _check_range("surface_pressure_hpa", self.surface_pressure_hpa, 450.0, 1100.0)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class NinoObservation:
    date: str
    iso_date: str
    name: str
    region: str
    latitude: float
    longitude: float
    sea_surface_temperature_c: Optional[float] = None
    sst_max_c: Optional[float] = None
    sst_min_c: Optional[float] = None
    observed_at: Optional[str] = None

    def __post_init__(self) -> None:
        _check_range("sea_surface_temperature_c", self.sea_surface_temperature_c, -5.0, 40.0)
        _check_range("sst_max_c", self.sst_max_c, -5.0, 40.0)
        _check_range("sst_min_c", self.sst_min_c, -5.0, 40.0)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RunManifest:
    date: str
    iso_date: str
    started_utc: str
    finished_utc: str
    cities_requested: int
    cities_ok: int
    nino_requested: int
    nino_ok: int
    quality_passed: bool
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
