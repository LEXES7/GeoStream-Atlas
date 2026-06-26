"""Typed, validated records that flow through the pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


class ValidationError(ValueError):
    pass


def _check_range(name: str, value: float | None, low: float, high: float) -> None:
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
    temperature_c: float | None = None
    temperature_max_c: float | None = None
    temperature_min_c: float | None = None
    apparent_temperature_c: float | None = None
    humidity_pct: float | None = None
    precipitation_mm: float | None = None
    cloud_cover_pct: float | None = None
    wind_speed_kmh: float | None = None
    wind_direction_deg: float | None = None
    surface_pressure_hpa: float | None = None
    pressure_msl_hpa: float | None = None
    uv_index_max: float | None = None
    weather_code: int | None = None
    observed_at: str | None = None

    def __post_init__(self) -> None:
        _check_range("temperature_c", self.temperature_c, -90.0, 60.0)
        _check_range("temperature_max_c", self.temperature_max_c, -90.0, 60.0)
        _check_range("temperature_min_c", self.temperature_min_c, -90.0, 60.0)
        _check_range("apparent_temperature_c", self.apparent_temperature_c, -110.0, 70.0)
        _check_range("humidity_pct", self.humidity_pct, 0.0, 100.0)
        _check_range("precipitation_mm", self.precipitation_mm, 0.0, 2000.0)
        _check_range("cloud_cover_pct", self.cloud_cover_pct, 0.0, 100.0)
        _check_range("wind_speed_kmh", self.wind_speed_kmh, 0.0, 500.0)
        _check_range("wind_direction_deg", self.wind_direction_deg, 0.0, 360.0)
        _check_range("surface_pressure_hpa", self.surface_pressure_hpa, 450.0, 1100.0)
        _check_range("pressure_msl_hpa", self.pressure_msl_hpa, 850.0, 1100.0)
        _check_range("uv_index_max", self.uv_index_max, 0.0, 20.0)

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
    sea_surface_temperature_c: float | None = None
    sst_max_c: float | None = None
    sst_min_c: float | None = None
    wave_height_m: float | None = None
    observed_at: str | None = None

    def __post_init__(self) -> None:
        _check_range("sea_surface_temperature_c", self.sea_surface_temperature_c, -5.0, 40.0)
        _check_range("sst_max_c", self.sst_max_c, -5.0, 40.0)
        _check_range("sst_min_c", self.sst_min_c, -5.0, 40.0)
        _check_range("wave_height_m", self.wave_height_m, 0.0, 40.0)

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
