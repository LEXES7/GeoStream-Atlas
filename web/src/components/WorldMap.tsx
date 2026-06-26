import { useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import { WMO, fmt, tempColor } from "../api";
import type { City, NinoRegion } from "../types";

type Metric = "temp" | "humidity" | "wind";

const ninoIcon = L.divIcon({
  className: "",
  html: "<div class='nino-marker'>◆</div>",
});

function rampColor(v: number | null, stops: [number, string][]) {
  if (v === null || v === undefined) return "#6b7280";
  let c = stops[0][1];
  for (const [t, col] of stops) if (v >= t) c = col;
  return c;
}

const HUM: [number, string][] = [[0, "#f97316"], [30, "#fbbf24"], [50, "#a3e635"], [70, "#34d399"], [85, "#22d3ee"], [95, "#3b82f6"]];
const WIND: [number, string][] = [[0, "#34d399"], [15, "#a3e635"], [30, "#fbbf24"], [45, "#f97316"], [60, "#ef4444"]];

const METRICS: Record<Metric, { label: string; value: (c: City) => number | null; color: (c: City) => string; legend: string[] }> = {
  temp: { label: "Temperature", value: (c) => c.temperature_c, color: (c) => tempColor(c.temperature_c), legend: ["−10°", "10°", "28°", "45°"] },
  humidity: { label: "Humidity", value: (c) => c.humidity_pct, color: (c) => rampColor(c.humidity_pct, HUM), legend: ["dry", "50%", "95%"] },
  wind: { label: "Wind", value: (c) => c.wind_speed_kmh, color: (c) => rampColor(c.wind_speed_kmh, WIND), legend: ["calm", "30", "60+ km/h"] },
};

export default function WorldMap({ cities, nino }: { cities: City[]; nino: NinoRegion[] }) {
  const [metric, setMetric] = useState<Metric>("temp");
  const m = METRICS[metric];
  const hottest = cities.reduce<City | null>(
    (a, c) => (c.temperature_c !== null && (!a || (a.temperature_c ?? -99) < c.temperature_c) ? c : a),
    null,
  );

  return (
    <div className="map-shell">
      <div className="map-controls">
        {(Object.keys(METRICS) as Metric[]).map((k) => (
          <button key={k} className={`seg ${metric === k ? "active" : ""}`} onClick={() => setMetric(k)}>
            {METRICS[k].label}
          </button>
        ))}
      </div>

      <MapContainer center={[18, 10]} zoom={2} minZoom={2} worldCopyJump style={{ height: "100%" }}>
        <TileLayer
          attribution="© OpenStreetMap, © CARTO"
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
          maxZoom={10}
        />
        {cities.map((c) => (
          <CircleMarker
            key={`${c.country}-${c.city}`}
            center={[c.latitude, c.longitude]}
            radius={c === hottest ? 8 : 6}
            pathOptions={{
              color: "#0a0e17",
              weight: 1.5,
              fillColor: m.color(c),
              fillOpacity: 0.95,
              className: c === hottest ? "marker-pulse" : "",
            }}
          >
            <Popup>
              <b>{c.city}</b>, {c.country}
              <br />
              {fmt(c.temperature_c)} °C {c.weather_code !== null ? WMO[c.weather_code] ?? "" : ""}
              <br />
              <small>
                Feels {fmt(c.apparent_temperature_c)} °C · Humidity {fmt(c.humidity_pct, 0)}% · Wind{" "}
                {fmt(c.wind_speed_kmh, 0)} km/h
              </small>
            </Popup>
          </CircleMarker>
        ))}
        {nino.map((n) => (
          <Marker key={n.name} position={[n.latitude, n.longitude]} icon={ninoIcon}>
            <Popup>
              <b>{n.name}</b> (Pacific)
              <br />
              SST {fmt(n.sea_surface_temperature_c)} °C
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      <div className="map-legend">
        <span className="legend-label">{m.label}</span>
        <span className={`legend-bar ${metric}`} />
        <span className="legend-ticks">{m.legend.join("  ·  ")}</span>
      </div>
    </div>
  );
}
