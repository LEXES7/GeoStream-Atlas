"""Rolling ONI and a simple ENSO trend forecast from accumulated history.

Reads the committed observations.csv, builds the Nino 3.4 anomaly time series,
smooths it into a rolling index (the ONI is a running mean of this anomaly), and
projects a short horizon with least-squares linear regression. The forecast is a
trend/persistence baseline, not a dynamical climate model — honest about scope.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .analysis import classify


@dataclass(frozen=True, slots=True)
class Point:
    date: str  # YYYY-MM-DD
    value: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Forecast:
    anomaly_series: list[Point]
    rolling_series: list[Point]
    projection: list[Point]
    current_oni: float | None
    current_phase: str
    trend_per_month: float | None
    note: str

    def to_dict(self) -> dict:
        return asdict(self)


def read_nino34_series(data_dir: Path) -> list[Point]:
    path = data_dir / "observations.csv"
    if not path.exists():
        return []
    points: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("location") != "Nino_3_4":
                continue
            raw = row.get("sst_anomaly_c")
            if not raw:
                continue
            try:
                points[row["iso_date"]] = float(raw)
            except ValueError:
                continue
    return [Point(d, points[d]) for d in sorted(points)]


def rolling_mean(series: list[Point], window: int = 30) -> list[Point]:
    out: list[Point] = []
    for i in range(len(series)):
        lo = max(0, i - window + 1)
        chunk = series[lo : i + 1]
        avg = sum(p.value for p in chunk) / len(chunk)
        out.append(Point(series[i].date, round(avg, 3)))
    return out


def _linregress(xs: list[float], ys: list[float]) -> tuple[float, float]:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return 0.0, my
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / denom
    return slope, my - slope * mx


def project(series: list[Point], horizon_days: int = 30) -> tuple[list[Point], float | None]:
    """Short, damped trend from the recent slope.

    ENSO anomalies mean-revert, and naive linear extrapolation of a noisy series
    runs away, so the projection: (1) uses only the recent window, (2) damps the
    trend the further out it goes, and (3) clamps to a physically plausible band.
    """
    if len(series) < 7:
        return [], None

    recent = series[-28:]
    last = recent[-1]
    base = datetime.strptime(recent[0].date, "%Y-%m-%d")
    xs = [float((datetime.strptime(p.date, "%Y-%m-%d") - base).days) for p in recent]
    ys = [p.value for p in recent]
    slope, _ = _linregress(xs, ys)

    out: list[Point] = []
    for step in range(7, horizon_days + 1, 7):
        damp = 0.6 ** (step / 14)  # trend fades the further out we project
        raw = last.value + slope * step * damp
        bounded = max(last.value - 1.5, min(last.value + 1.5, raw))
        clamped = max(-3.0, min(3.0, bounded))
        d = (datetime.strptime(last.date, "%Y-%m-%d") + timedelta(days=step)).strftime("%Y-%m-%d")
        out.append(Point(d, round(clamped, 3)))
    return out, round(slope * 30, 3)


def build(data_dir: Path) -> Forecast:
    series = read_nino34_series(data_dir)
    rolling = rolling_mean(series)
    projection, trend = project(rolling)
    current = rolling[-1].value if rolling else None
    return Forecast(
        anomaly_series=series,
        rolling_series=rolling,
        projection=projection,
        current_oni=current,
        current_phase=classify(current),
        trend_per_month=trend,
        note="Rolling 30-day Nino 3.4 anomaly with a damped short-term trend. "
             "Indicative signal, not a dynamical forecast.",
    )
