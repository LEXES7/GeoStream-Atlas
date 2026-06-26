from geostream.analysis import analyze, classify
from geostream.models import NinoObservation


def test_classify_thresholds():
    assert classify(0.6) == "el_nino"
    assert classify(-0.6) == "la_nina"
    assert classify(0.1) == "neutral"
    assert classify(None) == "unknown"


def test_analyze_computes_nino34_anomaly():
    # Nino 3.4 baseline is 29.1 C, so 30.1 C is a +1.0 C anomaly.
    nino = [
        NinoObservation(
            date="06262026", iso_date="2026-06-26", name="Nino_3_4",
            region="Pacific", latitude=0.0, longitude=-170.0,
            sea_surface_temperature_c=30.1,
        )
    ]
    snap = analyze("06262026", "2026-06-26", nino)
    assert snap.nino34_anomaly_c == 1.0
    assert snap.phase == "el_nino"
