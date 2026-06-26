"""Quality gate: a day's batch must pass before it is written."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import CityObservation, NinoObservation


@dataclass(slots=True)
class QualityReport:
    passed: bool = True
    checks: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(name)
        if not ok:
            self.passed = False
            self.failures.append(f"{name}: {detail}" if detail else name)


def evaluate(
    cities: list[CityObservation],
    nino: list[NinoObservation],
    min_city_fill: float = 0.5,
) -> QualityReport:
    report = QualityReport()
    report.add("non_empty", bool(cities or nino), "no observations collected")

    if cities:
        filled = sum(1 for c in cities if c.temperature_c is not None)
        ratio = filled / len(cities)
        report.add(
            "city_temperature_fill",
            ratio >= min_city_fill,
            f"only {filled}/{len(cities)} cities have temperature ({ratio:.0%})",
        )

    if nino:
        with_sst = sum(1 for n in nino if n.sea_surface_temperature_c is not None)
        report.add(
            "nino_sst_present",
            with_sst >= 1,
            f"{with_sst}/{len(nino)} Nino regions returned SST",
        )

    return report
