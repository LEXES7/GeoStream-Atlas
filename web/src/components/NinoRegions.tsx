import { motion } from "framer-motion";
import { fmt } from "../api";
import type { RegionAnomaly } from "../types";

const NICE: Record<string, string> = {
  Nino_1_2: "Niño 1+2",
  Nino_3: "Niño 3",
  Nino_3_4: "Niño 3.4",
  Nino_4: "Niño 4",
};

function barWidth(a: number | null) {
  if (a === null) return 50;
  const clamped = Math.max(-3, Math.min(3, a));
  return ((clamped + 3) / 6) * 100;
}

export default function NinoRegions({ regions }: { regions: RegionAnomaly[] }) {
  return (
    <motion.section
      className="card regions-card"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      <div className="card-head">
        <h2>Pacific monitoring regions</h2>
        <span className="hint">Sea-surface temperature anomaly</span>
      </div>
      <div className="regions-grid">
        {regions.map((r, i) => (
          <motion.div
            key={r.name}
            className="region"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15 + i * 0.06 }}
          >
            <div className="region-top">
              <span className="region-name">{NICE[r.name] ?? r.name}</span>
              <span className={`region-anom ${r.phase}`}>
                {r.anomaly_c === null ? "—" : `${r.anomaly_c > 0 ? "+" : ""}${fmt(r.anomaly_c, 2)}°`}
              </span>
            </div>
            <div className="region-track">
              <span className="region-zero" />
              <motion.span
                className={`region-fill ${r.phase}`}
                initial={{ width: "50%" }}
                animate={{ width: `${barWidth(r.anomaly_c)}%` }}
                transition={{ type: "spring", stiffness: 50, damping: 14, delay: 0.2 + i * 0.06 }}
              />
            </div>
            <div className="region-sst">SST {fmt(r.observed_sst_c, 1)} °C</div>
          </motion.div>
        ))}
      </div>
    </motion.section>
  );
}
