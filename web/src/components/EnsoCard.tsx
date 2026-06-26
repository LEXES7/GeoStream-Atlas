import { PHASE_LABEL, fmt } from "../api";
import type { Latest } from "../types";

export default function EnsoCard({ latest }: { latest: Latest }) {
  const f = latest.forecast;
  const phase = f.current_phase && f.current_phase !== "unknown" ? f.current_phase : latest.enso.phase;
  const oni = f.current_oni ?? latest.enso.nino34_anomaly_c;
  const trend = f.trend_per_month;
  const arrow =
    trend === null || trend === undefined ? "" : trend > 0.02 ? "▲ " : trend < -0.02 ? "▼ " : "→ ";

  return (
    <article className="card enso-card">
      <div className="enso-label">ENSO STATUS · Niño 3.4</div>
      <div className={`enso-phase ${phase}`}>{PHASE_LABEL[phase] ?? "—"}</div>
      <div className="enso-metrics">
        <div>
          <span className="big">{fmt(oni, 2)}</span>
          <small>30-day ONI (°C)</small>
        </div>
        <div>
          <span className="big">{arrow}{trend === null || trend === undefined ? "—" : fmt(trend, 2)}</span>
          <small>trend / month</small>
        </div>
      </div>
      <p className="enso-note">{f.note || latest.enso.note}</p>
    </article>
  );
}
