import type { Briefing, CityHistory, Intraday, Latest, TimeSeries } from "./types";

const base = import.meta.env.BASE_URL;

async function loadJSON<T>(name: string): Promise<T> {
  const res = await fetch(`${base}data/${name}?v=${Date.now()}`);
  if (!res.ok) throw new Error(`${name}: ${res.status}`);
  return (await res.json()) as T;
}

export function loadLatest(): Promise<Latest> {
  return loadJSON<Latest>("latest.json");
}

export function loadTimeSeries(): Promise<TimeSeries> {
  return loadJSON<TimeSeries>("enso_timeseries.json");
}

export function loadIntraday(): Promise<Intraday> {
  return loadJSON<Intraday>("intraday.json");
}

export function loadCityHistory(): Promise<CityHistory> {
  return loadJSON<CityHistory>("city_history.json");
}

// Briefing is optional (only exists if a GROQ_API_KEY is configured).
export async function loadBriefingSafe(): Promise<Briefing | null> {
  try {
    return await loadJSON<Briefing>("briefing.json");
  } catch {
    return null;
  }
}

export function timeAgo(iso: string | undefined, now: number): string {
  if (!iso) return "";
  const diff = Math.max(0, now - new Date(iso).getTime());
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ${mins % 60}m ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export const PHASE_LABEL: Record<string, string> = {
  el_nino: "El Niño",
  la_nina: "La Niña",
  neutral: "Neutral",
  unknown: "No data",
};

export const WMO: Record<number, string> = {
  0: "☀️ Clear", 1: "🌤️ Mainly clear", 2: "⛅ Partly cloudy", 3: "☁️ Overcast",
  45: "🌫️ Fog", 48: "🌫️ Rime fog", 51: "🌦️ Light drizzle", 53: "🌦️ Drizzle",
  55: "🌧️ Dense drizzle", 61: "🌧️ Light rain", 63: "🌧️ Rain", 65: "🌧️ Heavy rain",
  71: "🌨️ Light snow", 73: "🌨️ Snow", 75: "❄️ Heavy snow", 80: "🌦️ Showers",
  81: "🌧️ Showers", 82: "⛈️ Violent showers", 95: "⛈️ Thunderstorm", 96: "⛈️ Storm + hail",
};

export function tempColor(t: number | null | undefined): string {
  if (t === null || t === undefined) return "#6b7280";
  const stops: [number, string][] = [
    [-10, "#3b82f6"], [0, "#22d3ee"], [10, "#34d399"], [20, "#a3e635"],
    [28, "#fbbf24"], [35, "#f97316"], [45, "#ef4444"],
  ];
  let c = stops[0][1];
  for (const [v, col] of stops) if (t >= v) c = col;
  return c;
}

export function fmt(v: number | null | undefined, d = 1): string {
  return v === null || v === undefined ? "—" : Number(v).toFixed(d);
}
