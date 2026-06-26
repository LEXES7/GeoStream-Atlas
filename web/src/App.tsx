import { useEffect, useState } from "react";
import { loadLatest, loadTimeSeries } from "./api";
import type { Latest, TimeSeries } from "./types";
import EnsoCard from "./components/EnsoCard";
import StatGrid from "./components/Stats";
import WorldMap from "./components/WorldMap";
import EnsoChart from "./components/EnsoChart";
import CityTable from "./components/CityTable";

const REPO = "https://github.com/LEXES7/GeoStream-Atlas";

export default function App() {
  const [latest, setLatest] = useState<Latest | null>(null);
  const [ts, setTs] = useState<TimeSeries | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadLatest(), loadTimeSeries()])
      .then(([l, t]) => {
        setLatest(l);
        setTs(t);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load data"));
  }, []);

  const updated =
    latest?.iso_date &&
    new Date(latest.iso_date).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });

  return (
    <>
      <div className="bg-grid" aria-hidden />
      <header className="topbar">
        <div className="brand">
          <div className="logo">🌊</div>
          <div>
            <h1>GeoStream Atlas</h1>
            <p className="tagline">Global climate &amp; El Niño monitor</p>
          </div>
        </div>
        <div className="topbar-right">
          <span className="updated">
            {error ? "Failed to load data" : updated ? `Updated ${updated}` : "Loading…"}
          </span>
          <a className="ghbtn" href={REPO} target="_blank" rel="noopener noreferrer">
            Repo ↗
          </a>
        </div>
      </header>

      <main>
        {latest && (
          <section className="hero">
            <EnsoCard latest={latest} />
            <StatGrid stats={latest.stats} />
          </section>
        )}

        {latest && (
          <section className="card map-card">
            <div className="card-head">
              <h2>Live conditions</h2>
              <span className="hint">Marker colour = temperature · ◆ = Niño ocean buoy</span>
            </div>
            <div className="map-host">
              <WorldMap cities={latest.cities} nino={latest.nino_regions} />
            </div>
          </section>
        )}

        {ts && (
          <section className="card chart-card">
            <div className="card-head">
              <h2>El Niño signal — Niño 3.4 anomaly</h2>
              <span className="hint">Daily anomaly, 30-day index &amp; trend projection</span>
            </div>
            <div className="chart-host">
              <EnsoChart ts={ts} />
            </div>
          </section>
        )}

        {latest && <CityTable cities={latest.cities} />}
      </main>

      <footer>
        <p>
          Data from{" "}
          <a href="https://open-meteo.com" target="_blank" rel="noopener noreferrer">
            Open-Meteo
          </a>{" "}
          (CC BY 4.0) · Updated daily by GitHub Actions · MIT licensed
        </p>
        <p className="muted">
          ENSO read-out is a daily indicator, not an official NOAA classification. See the repository
          for methodology.
        </p>
      </footer>
    </>
  );
}
