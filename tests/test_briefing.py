from geostream.briefing import facts_from_latest, generate


def test_facts_from_latest_prefers_forecast_phase():
    latest = {
        "enso": {"phase": "neutral", "nino34_anomaly_c": 0.2},
        "forecast": {"current_phase": "el_nino", "current_oni": 0.8, "trend_per_month": 0.1},
        "stats": {"city_count": 74, "country_count": 57, "avg_temp_c": 23.0},
    }
    facts = facts_from_latest(latest)
    assert facts["enso_phase"] == "el_nino"
    assert facts["nino34_oni_c"] == 0.8
    assert facts["cities_tracked"] == 74


def test_generate_no_key_returns_none(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert generate({"enso_phase": "neutral"}) is None
