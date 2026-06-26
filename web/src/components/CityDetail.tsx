import { motion } from "framer-motion";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Filler,
  type ChartOptions,
  type ScriptableContext,
} from "chart.js";
import "chartjs-adapter-date-fns";
import { WMO, fmt } from "../api";
import type { City, SlotPoint } from "../types";

ChartJS.register(LineElement, PointElement, LinearScale, TimeScale, Tooltip, Filler);

const options: ChartOptions<"line"> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "index", intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: "rgba(16,22,36,0.95)",
      borderColor: "rgba(255,255,255,0.1)",
      borderWidth: 1,
      callbacks: { label: (i) => ` ${Number(i.parsed.y).toFixed(1)} °C` },
    },
  },
  scales: {
    x: { type: "time", time: { unit: "day" }, grid: { display: false }, ticks: { color: "#8a96ab", maxTicksLimit: 6 } },
    y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#8a96ab" } },
  },
  elements: { point: { radius: 0 } },
};

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-stat">
      <span className="detail-stat-val">{value}</span>
      <span className="detail-stat-lbl">{label}</span>
    </div>
  );
}

export default function CityDetail({
  city,
  history,
  onClose,
}: {
  city: City;
  history: SlotPoint[];
  onClose: () => void;
}) {
  const code = city.weather_code !== null ? WMO[city.weather_code] ?? "" : "";
  const fill = (ctx: ScriptableContext<"line">) => {
    const { ctx: c, chartArea } = ctx.chart;
    if (!chartArea) return "transparent";
    const g = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
    g.addColorStop(0, "rgba(79,157,255,0.35)");
    g.addColorStop(1, "rgba(79,157,255,0)");
    return g;
  };

  return (
    <motion.div
      className="modal-backdrop"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="modal card"
        initial={{ opacity: 0, scale: 0.94, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 10 }}
        transition={{ type: "spring", stiffness: 200, damping: 22 }}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="modal-close" onClick={onClose} aria-label="Close">
          ✕
        </button>
        <div className="modal-head">
          <div>
            <h3>{city.city}</h3>
            <p className="modal-sub">{city.country}</p>
          </div>
          <div className="modal-now">
            <span className="modal-temp">{fmt(city.temperature_c)}°</span>
            <span className="modal-cond">{code}</span>
          </div>
        </div>

        <div className="detail-stats">
          <Stat label="Feels like" value={`${fmt(city.apparent_temperature_c)}°`} />
          <Stat label="Humidity" value={`${fmt(city.humidity_pct, 0)}%`} />
          <Stat label="Wind" value={`${fmt(city.wind_speed_kmh, 0)} km/h`} />
          <Stat label="Cloud" value={`${fmt(city.cloud_cover_pct, 0)}%`} />
          <Stat label="Rain" value={`${fmt(city.precipitation_mm, 1)} mm`} />
        </div>

        <div className="detail-chart-label">Temperature · recent readings</div>
        <div className="detail-chart">
          {history.length > 1 ? (
            <Line
              options={options}
              data={{
                datasets: [
                  {
                    data: history.map((p) => ({ x: p.slot, y: p.value })),
                    borderColor: "#4f9dff",
                    borderWidth: 2.5,
                    tension: 0.35,
                    fill: "origin",
                    backgroundColor: fill,
                  },
                ],
              }}
            />
          ) : (
            <p className="detail-empty">Not enough history yet — fills in as data collects.</p>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
