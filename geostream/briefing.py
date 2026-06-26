"""Optional AI briefing via Groq's free, OpenAI-compatible API.

Generates a short, factual natural-language summary of the current weather and
ENSO state from our own data. The API key is read from GROQ_API_KEY (a GitHub
Actions secret); if it is absent the whole feature is a no-op so the pipeline
keeps working without it. Stdlib only — no SDK to audit.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from .logging_setup import get_logger

log = get_logger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "You are the data assistant for GeoStream Atlas, a global climate monitor. "
    "Write a concise, factual briefing of 2-3 sentences about current world weather "
    "and the El Nino / La Nina (ENSO) state, using ONLY the numbers provided. "
    "Do not invent figures, do not use markdown, return plain text only."
)


def facts_from_latest(latest: dict) -> dict:
    enso = latest.get("enso", {})
    fc = latest.get("forecast", {})
    stats = latest.get("stats", {})
    return {
        "enso_phase": fc.get("current_phase") or enso.get("phase"),
        "nino34_oni_c": fc.get("current_oni"),
        "trend_per_month_c": fc.get("trend_per_month"),
        "cities_tracked": stats.get("city_count"),
        "countries": stats.get("country_count"),
        "avg_temp_c": stats.get("avg_temp_c"),
        "hottest": stats.get("hottest"),
        "coldest": stats.get("coldest"),
    }


def generate(facts: dict, *, timeout: int = 30) -> dict | None:
    """Call Groq and return {text, model, generated_utc}, or None if unavailable."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        log.info("briefing skipped: GROQ_API_KEY not set")
        return None

    model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
    payload = {
        "model": model,
        "temperature": 0.4,
        "max_tokens": 220,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(facts)},
        ],
    }
    req = urllib.request.Request(
        GROQ_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "GeoStream-Atlas/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip()
    except (
        urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, ValueError
    ) as err:
        log.warning("briefing failed", extra={"fields": {"error": str(err)}})
        return None

    return {"text": text, "model": model, "generated_utc": datetime.now(UTC).isoformat()}


def write(web_data: Path) -> bool:
    """Read latest.json, generate a briefing and write briefing.json. Best effort."""
    latest_path = web_data / "latest.json"
    if not latest_path.exists():
        return False
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    result = generate(facts_from_latest(latest))
    if result is None:
        return False
    (web_data / "briefing.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    log.info("briefing written", extra={"fields": {"model": result["model"]}})
    return True
