"""ENSO signal analysis from Nino-region sea-surface temperature.

NOAA classifies El Nino / La Nina from the SST anomaly in the Nino 3.4 region:
anomaly >= +0.5 C is El Nino, <= -0.5 C is La Nina, otherwise neutral. We compute
the anomaly against a baseline calibrated to the mean SST that this dataset's own
source (Open-Meteo) reports for each region, so the anomaly is centred and
realistic. A true ONI uses a 3-month running mean over a fixed 30-year base
period and removes the seasonal cycle; treat this as an indicative signal.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import NinoObservation

# Calibrated to the source's observed period-mean SST per region (deg C).
CLIMATOLOGY_C = {
    "Nino_1_2": 27.9,
    "Nino_3": 28.1,
    "Nino_3_4": 29.1,
    "Nino_4": 30.6,
}

EL_NINO_THRESHOLD = 0.5
LA_NINA_THRESHOLD = -0.5


def classify(anomaly: float | None) -> str:
    if anomaly is None:
        return "unknown"
    if anomaly >= EL_NINO_THRESHOLD:
        return "el_nino"
    if anomaly <= LA_NINA_THRESHOLD:
        return "la_nina"
    return "neutral"


@dataclass(frozen=True, slots=True)
class RegionAnomaly:
    name: str
    observed_sst_c: float | None
    climatology_c: float | None
    anomaly_c: float | None
    phase: str


@dataclass(frozen=True, slots=True)
class EnsoSnapshot:
    date: str
    iso_date: str
    regions: list[RegionAnomaly]
    nino34_anomaly_c: float | None
    phase: str
    note: str

    def to_dict(self) -> dict:
        return asdict(self)


def analyze(date: str, iso_date: str, nino: list[NinoObservation]) -> EnsoSnapshot:
    regions: list[RegionAnomaly] = []
    nino34_anomaly: float | None = None

    for obs in nino:
        clim = CLIMATOLOGY_C.get(obs.name)
        sst = obs.sea_surface_temperature_c
        anomaly = round(sst - clim, 2) if (sst is not None and clim is not None) else None
        regions.append(RegionAnomaly(
            name=obs.name, observed_sst_c=sst, climatology_c=clim,
            anomaly_c=anomaly, phase=classify(anomaly),
        ))
        if obs.name == "Nino_3_4":
            nino34_anomaly = anomaly

    return EnsoSnapshot(
        date=date, iso_date=iso_date, regions=regions,
        nino34_anomaly_c=nino34_anomaly, phase=classify(nino34_anomaly),
        note="Daily anomaly vs the source's period-mean SST, not the official smoothed ONI.",
    )
