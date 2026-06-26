import { motion } from "framer-motion";
import { PHASE_LABEL, fmt } from "../api";
import EnsoGauge from "./EnsoGauge";
import type { Latest } from "../types";

export default function EnsoCard({ latest }: { latest: Latest }) {
  const f = latest.forecast;
  const phase =
    f.current_phase && f.current_phase !== "unknown" ? f.current_phase : latest.enso.phase;
  const oni = f.current_oni ?? latest.enso.nino34_anomaly_c;
  const trend = f.trend_per_month;
  const arrow =
    trend === null || trend === undefined ? "" : trend > 0.02 ? "▲" : trend < -0.02 ? "▼" : "→";
  const trendDir = trend === null || trend === undefined ? "" : trend > 0.02 ? "up" : trend < -0.02 ? "down" : "flat";

  return (
    <motion.article
      className="card enso-card"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="enso-head">
        <div>
          <div className="enso-label">ENSO STATUS · NIÑO 3.4</div>
          <div className={`enso-phase ${phase}`}>
            <span className={`pulse-dot ${phase}`} />
            {PHASE_LABEL[phase] ?? "—"}
          </div>
        </div>
      </div>

      <EnsoGauge value={oni} />

      <div className="enso-metrics">
        <div>
          <span className="big">{fmt(oni, 2)}</span>
          <small>30-day ONI (°C)</small>
        </div>
        <div>
          <span className={`big trend-${trendDir}`}>
            {arrow} {trend === null || trend === undefined ? "—" : fmt(Math.abs(trend), 2)}
          </span>
          <small>trend / month</small>
        </div>
      </div>
      <p className="enso-note">{f.note || latest.enso.note}</p>
    </motion.article>
  );
}
