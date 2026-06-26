"""ENSO signal analysis from Nino-region sea-surface temperature.

NOAA classifies El Nino / La Nina from the SST anomaly in the Nino 3.4 region:
anomaly >= +0.5 C is El Nino, <= -0.5 C is La Nina, otherwise neutral. This
module computes a daily instantaneous anomaly as an early indicator. A true ONI
needs a 3-month running mean over a 30-year base period; the baselines below are
approximate and meant to be replaced once enough committed history exists.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

from .models import NinoObservation

CLIMATOLOGY_C = {
    "Nino_1_2": 24.0,
    "Nino_3": 25.5,
    "Nino_3_4": 26.5,
    "Nino_4": 28.5,
}

EL_NINO_THRESHOLD = 0.5
LA_NINA_THRESHOLD = -0.5


def classify(anomaly: Optional[float]) -> str:
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
    observed_sst_c: Optional[float]
    climatology_c: Optional[float]
    anomaly_c: Optional[float]
    phase: str


@dataclass(frozen=True, slots=True)
class EnsoSnapshot:
    date: str
    iso_date: str
    regions: list[RegionAnomaly]
    nino34_anomaly_c: Optional[float]
    phase: str
    note: str

    def to_dict(self) -> dict:
        return asdict(self)


def analyze(date: str, iso_date: str, nino: list[NinoObservation]) -> EnsoSnapshot:
    regions: list[RegionAnomaly] = []
    nino34_anomaly: Optional[float] = None

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
        note="Instantaneous daily anomaly vs approximate climatology, not a smoothed ONI.",
    )
