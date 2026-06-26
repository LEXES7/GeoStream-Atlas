import { motion } from "framer-motion";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Filler,
  type ChartOptions,
  type ScriptableContext,
} from "chart.js";
import type { Intraday, SlotPoint } from "../types";

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Filler);

const sparkOptions: ChartOptions<"line"> = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 700 },
  plugins: { legend: { display: false }, tooltip: { enabled: false } },
  scales: { x: { display: false }, y: { display: false } },
  elements: { point: { radius: 0 } },
};

function Spark({ points, color }: { points: SlotPoint[]; color: string }) {
  const fill = (ctx: ScriptableContext<"line">) => {
    const { ctx: c, chartArea } = ctx.chart;
    if (!chartArea) return "transparent";
    const g = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
    g.addColorStop(0, `${color}55`);
    g.addColorStop(1, `${color}00`);
    return g;
  };
  return (
    <div className="spark">
      <Line
        options={sparkOptions}
        data={{
          labels: points.map((p) => p.slot),
          datasets: [
            { data: points.map((p) => p.value), borderColor: color, borderWidth: 2, tension: 0.4, fill: "origin", backgroundColor: fill },
          ],
        }}
      />
    </div>
  );
}

function last(points: SlotPoint[]): number | null {
  return points.length ? points[points.length - 1].value : null;
}

function delta(points: SlotPoint[]): number | null {
  if (points.length < 2) return null;
  return points[points.length - 1].value - points[0].value;
}

function Metric({ label, points, color, unit }: { label: string; points: SlotPoint[]; color: string; unit: string }) {
  const v = last(points);
  const d = delta(points);
  const arrow = d === null ? "" : d > 0.05 ? "▲" : d < -0.05 ? "▼" : "→";
  return (
    <div className="intraday-metric">
      <div className="intraday-top">
        <span className="intraday-label">{label}</span>
        <span className="intraday-val" style={{ color }}>
          {v === null ? "—" : v.toFixed(1)}
          <small>{unit}</small>
        </span>
      </div>
      <Spark points={points} color={color} />
      <span className="intraday-delta">
        {arrow} {d === null ? "—" : `${Math.abs(d).toFixed(1)} ${unit} over window`}
      </span>
    </div>
  );
}

export default function IntradayCard({ intraday }: { intraday: Intraday }) {
  if (!intraday.temp.length && !intraday.sst.length) return null;
  return (
    <motion.section
      className="card intraday-card"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="card-head">
        <h2>Global pulse</h2>
        <span className="hint">Last {Math.max(intraday.temp.length, intraday.sst.length)} readings</span>
      </div>
      <div className="intraday-grid">
        <Metric label="Avg city temperature" points={intraday.temp} color="#4f9dff" unit="°C" />
        <Metric label="Niño 3.4 sea-surface temp" points={intraday.sst} color="#38e0c4" unit="°C" />
      </div>
    </motion.section>
  );
}
