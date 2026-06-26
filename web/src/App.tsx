import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { loadLatest, loadTimeSeries, PHASE_LABEL } from "./api";
import type { Latest, TimeSeries } from "./types";
import EnsoCard from "./components/EnsoCard";
import StatGrid from "./components/Stats";
import NinoRegions from "./components/NinoRegions";
import WorldMap from "./components/WorldMap";
import EnsoChart from "./components/EnsoChart";
import CityTable from "./components/CityTable";

const REPO = "https://github.com/LEXES7/GeoStream-Atlas";

function Section({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, delay }}
    >
      {children}
    </motion.div>
  );
}

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
    new Date(latest.iso_date).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  const phase = latest?.forecast?.current_phase && latest.forecast.current_phase !== "unknown"
    ? latest.forecast.current_phase
    : latest?.enso.phase;

  return (
    <>
      <div className="aurora" aria-hidden>
        <span className="blob b1" />
        <span className="blob b2" />
        <span className="blob b3" />
      </div>
      <div className="bg-grid" aria-hidden />

      <header className="topbar">
        <div className="brand">
          <motion.div
            className="logo"
            initial={{ rotate: -20, scale: 0.6, opacity: 0 }}
            animate={{ rotate: 0, scale: 1, opacity: 1 }}
            transition={{ type: "spring", stiffness: 120, damping: 10 }}
          >
            🌊
          </motion.div>
          <div>
            <h1>GeoStream Atlas</h1>
            <p className="tagline">Global climate &amp; El Niño monitor</p>
          </div>
        </div>
        <div className="topbar-right">
          {phase && (
            <span className={`status-pill ${phase}`}>
              <span className={`pulse-dot ${phase}`} /> {PHASE_LABEL[phase]}
            </span>
          )}
          <span className="updated">
            {error ? "Failed to load data" : updated ? `Updated ${updated}` : "Loading…"}
          </span>
          <a className="ghbtn" href={REPO} target="_blank" rel="noopener noreferrer">
            Repo ↗
          </a>
        </div>
      </header>

      <main>
        {!latest && !error && (
          <div className="hero">
            <div className="card skeleton sk-tall" />
            <div className="stat-grid">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="card skeleton sk-stat" />
              ))}
            </div>
          </div>
        )}

        {latest && (
          <section className="hero">
            <EnsoCard latest={latest} />
            <StatGrid stats={latest.stats} />
          </section>
        )}

        {latest && (
          <Section>
            <NinoRegions regions={latest.enso.regions} />
          </Section>
        )}

        {latest && (
          <Section>
            <section className="card map-card">
              <div className="card-head">
                <h2>Live conditions</h2>
                <span className="hint">◆ = Niño ocean buoy · click a marker for detail</span>
              </div>
              <div className="map-host">
                <WorldMap cities={latest.cities} nino={latest.nino_regions} />
              </div>
            </section>
          </Section>
        )}

        {ts && (
          <Section>
            <section className="card chart-card">
              <div className="card-head">
                <h2>El Niño signal — Niño 3.4 anomaly</h2>
                <span className="hint">Daily anomaly, 30-day index &amp; trend projection</span>
              </div>
              <div className="chart-host">
                <EnsoChart ts={ts} />
              </div>
            </section>
          </Section>
        )}

        {latest && (
          <Section>
            <CityTable cities={latest.cities} />
          </Section>
        )}
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
          ENSO read-out is a daily indicator, not an official NOAA classification. See the repository for methodology.
        </p>
      </footer>
    </>
  );
}
