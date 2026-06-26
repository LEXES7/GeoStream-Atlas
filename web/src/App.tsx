import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  loadBriefingSafe,
  loadCityHistory,
  loadIntraday,
  loadLatest,
  loadTimeSeries,
  PHASE_LABEL,
  timeAgo,
} from "./api";
import type { Briefing, City, CityHistory, Intraday, Latest, TimeSeries } from "./types";
import EnsoCard from "./components/EnsoCard";
import StatGrid from "./components/Stats";
import BriefingCard from "./components/BriefingCard";
import NinoRegions from "./components/NinoRegions";
import IntradayCard from "./components/IntradayCard";
import WorldMap from "./components/WorldMap";
import EnsoChart from "./components/EnsoChart";
import CityTable from "./components/CityTable";
import CityDetail from "./components/CityDetail";
import RegionFilter from "./components/RegionFilter";

const REPO = "https://github.com/LEXES7/GeoStream-Atlas";
const REFRESH_MS = 5 * 60 * 1000;

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
  const [intraday, setIntraday] = useState<Intraday | null>(null);
  const [history, setHistory] = useState<CityHistory>({});
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [selected, setSelected] = useState<City | null>(null);
  const [region, setRegion] = useState("All");
  const [theme, setTheme] = useState<"dark" | "light">(
    () => (localStorage.getItem("geostream-theme") as "dark" | "light") || "dark",
  );
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("geostream-theme", theme);
  }, [theme]);

  const cities = useMemo(() => latest?.cities ?? [], [latest]);
  const filteredCities = useMemo(
    () => (region === "All" ? cities : cities.filter((c) => (c.continent ?? "Other") === region)),
    [cities, region],
  );

  // Deep link: open a city from ?city=&country= once data is loaded.
  useEffect(() => {
    if (!latest) return;
    const params = new URLSearchParams(window.location.search);
    const city = params.get("city");
    const country = params.get("country");
    if (city) {
      const match = latest.cities.find(
        (c) => c.city === city && (!country || c.country === country),
      );
      if (match) setSelected(match);
    }
  }, [latest]);

  // Reflect the open city in the URL so it can be shared.
  useEffect(() => {
    const url = new URL(window.location.href);
    if (selected) {
      url.searchParams.set("city", selected.city);
      url.searchParams.set("country", selected.country);
    } else {
      url.searchParams.delete("city");
      url.searchParams.delete("country");
    }
    window.history.replaceState({}, "", url);
  }, [selected]);

  useEffect(() => {
    const fetchAll = () =>
      Promise.all([loadLatest(), loadTimeSeries(), loadIntraday(), loadCityHistory(), loadBriefingSafe()])
        .then(([l, t, i, h, b]) => {
          setLatest(l);
          setTs(t);
          setIntraday(i);
          setHistory(h);
          setBriefing(b);
          setError(null);
        })
        .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load data"));

    fetchAll();
    const refresh = setInterval(fetchAll, REFRESH_MS);
    const tick = setInterval(() => setNow(Date.now()), 30000);
    return () => {
      clearInterval(refresh);
      clearInterval(tick);
    };
  }, []);

  const updated = latest?.generated_utc
    ? timeAgo(latest.generated_utc, now)
    : latest?.iso_date
      ? new Date(latest.iso_date).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
      : "";
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
            {error ? (
              "Failed to load data"
            ) : updated ? (
              <>
                <span className="live-dot" /> Updated {updated}
              </>
            ) : (
              "Loading…"
            )}
          </span>
          <button
            className="ghbtn theme-toggle"
            onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
            aria-label="Toggle theme"
          >
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
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

        {briefing && (
          <Section>
            <BriefingCard briefing={briefing} />
          </Section>
        )}

        {latest && (
          <Section>
            <NinoRegions regions={latest.enso.regions} />
          </Section>
        )}

        {intraday && (
          <Section>
            <IntradayCard intraday={intraday} />
          </Section>
        )}

        {latest && (
          <Section>
            <RegionFilter cities={cities} active={region} onChange={setRegion} />
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
                <WorldMap
                  cities={filteredCities}
                  nino={latest.nino_regions}
                  onSelect={setSelected}
                  dark={theme === "dark"}
                />
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
            <CityTable cities={filteredCities} onSelect={setSelected} />
          </Section>
        )}
      </main>

      <AnimatePresence>
        {selected && (
          <CityDetail
            city={selected}
            history={history[`${selected.city}|${selected.country}`] ?? []}
            onClose={() => setSelected(null)}
          />
        )}
      </AnimatePresence>

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
