import { useMemo, useState } from "react";
import { WMO, fmt, tempColor } from "../api";
import type { City } from "../types";

type Key = keyof City;
const COLUMNS: { k: Key; label: string; num?: boolean }[] = [
  { k: "city", label: "City" },
  { k: "country", label: "Country" },
  { k: "temperature_c", label: "Temp °C", num: true },
  { k: "apparent_temperature_c", label: "Feels °C", num: true },
  { k: "humidity_pct", label: "Humidity %", num: true },
  { k: "wind_speed_kmh", label: "Wind km/h", num: true },
  { k: "cloud_cover_pct", label: "Cloud %", num: true },
];

const icon = (code: number | null) =>
  code !== null && WMO[code] ? WMO[code].split(" ")[0] : "·";

export default function CityTable({
  cities,
  onSelect,
}: {
  cities: City[];
  onSelect: (c: City) => void;
}) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<Key>("temperature_c");
  const [sortDir, setSortDir] = useState(-1);

  const rows = useMemo(() => {
    const q = query.toLowerCase();
    return cities
      .filter((c) => c.city.toLowerCase().includes(q) || c.country.toLowerCase().includes(q))
      .sort((a, b) => {
        const av = a[sortKey];
        const bv = b[sortKey];
        if (typeof av === "string" && typeof bv === "string") return av.localeCompare(bv) * sortDir;
        return (((av as number) ?? -999) - ((bv as number) ?? -999)) * sortDir;
      });
  }, [cities, query, sortKey, sortDir]);

  const onSort = (k: Key) => {
    if (k === sortKey) setSortDir((d) => d * -1);
    else {
      setSortKey(k);
      setSortDir(k === "city" || k === "country" ? 1 : -1);
    }
  };

  const indicator = (k: Key) => (k === sortKey ? (sortDir === 1 ? " ↑" : " ↓") : "");

  return (
    <section className="card table-card">
      <div className="card-head">
        <h2>
          Cities <span className="count-pill">{rows.length}</span>
        </h2>
        <input
          className="search"
          type="search"
          placeholder="Filter city or country…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th aria-label="condition" />
              {COLUMNS.map((col) => (
                <th key={col.k} className={col.num ? "num" : ""} onClick={() => onSort(col.k)}>
                  {col.label}
                  {indicator(col.k)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={`${c.country}-${c.city}`} className="row-click" onClick={() => onSelect(c)}>
                <td className="wx">{icon(c.weather_code)}</td>
                <td className="city-cell">{c.city}</td>
                <td className="muted-cell">{c.country}</td>
                <td className="num">
                  <span className="temp-chip" style={{ background: `${tempColor(c.temperature_c)}22`, color: tempColor(c.temperature_c) }}>
                    {fmt(c.temperature_c)}
                  </span>
                </td>
                <td className="num">{fmt(c.apparent_temperature_c)}</td>
                <td className="num">{fmt(c.humidity_pct, 0)}</td>
                <td className="num">{fmt(c.wind_speed_kmh, 0)}</td>
                <td className="num">{fmt(c.cloud_cover_pct, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
