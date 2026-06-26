import { MapContainer, TileLayer, CircleMarker, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import { WMO, fmt, tempColor } from "../api";
import type { City, NinoRegion } from "../types";

const ninoIcon = L.divIcon({
  className: "",
  html: "<div style='color:#ffb454;font-size:18px;transform:translate(-9px,-9px)'>◆</div>",
});

export default function WorldMap({ cities, nino }: { cities: City[]; nino: NinoRegion[] }) {
  return (
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
          radius={6}
          pathOptions={{ color: "#0a0e17", weight: 1.5, fillColor: tempColor(c.temperature_c), fillOpacity: 0.95 }}
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
  );
}
