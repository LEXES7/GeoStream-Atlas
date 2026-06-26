import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Tooltip,
  Legend,
  Filler,
  type ChartOptions,
  type ScriptableContext,
} from "chart.js";
import annotationPlugin from "chartjs-plugin-annotation";
import "chartjs-adapter-date-fns";
import type { SeriesPoint, TimeSeries } from "../types";

ChartJS.register(LineElement, PointElement, LinearScale, TimeScale, Tooltip, Legend, Filler, annotationPlugin);

const toXY = (arr: SeriesPoint[]) => arr.map((p) => ({ x: p.date, y: p.value }));

function fill(ctx: ScriptableContext<"line">) {
  const { chart } = ctx;
  const { ctx: c, chartArea } = chart;
  if (!chartArea) return "rgba(56,224,196,0.1)";
  const g = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  g.addColorStop(0, "rgba(56,224,196,0.35)");
  g.addColorStop(1, "rgba(56,224,196,0)");
  return g;
}

const band = (yMin: number, yMax: number, color: string, label: string) => ({
  type: "box" as const,
  yMin,
  yMax,
  backgroundColor: color,
  borderWidth: 0,
  label: { display: true, content: label, position: "start" as const, color: "rgba(255,255,255,0.35)", font: { size: 10 } },
});

const options: ChartOptions<"line"> = {
  responsive: true,
  maintainAspectRatio: true,
  animation: { duration: 1100, easing: "easeOutQuart" },
  interaction: { mode: "index", intersect: false },
  scales: {
    x: { type: "time", time: { unit: "month" }, grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#8a96ab" } },
    y: {
      grid: { color: "rgba(255,255,255,0.05)" },
      ticks: { color: "#8a96ab" },
      title: { display: true, text: "°C anomaly", color: "#8a96ab" },
    },
  },
  plugins: {
    legend: { labels: { color: "#e7ecf5", boxWidth: 12, font: { size: 12 }, usePointStyle: true } },
    tooltip: {
      backgroundColor: "rgba(16,22,36,0.95)",
      borderColor: "rgba(255,255,255,0.1)",
      borderWidth: 1,
      padding: 10,
      callbacks: { label: (i) => ` ${i.dataset.label}: ${Number(i.parsed.y).toFixed(2)} °C` },
    },
    annotation: {
      annotations: {
        elnino: band(0.5, 3, "rgba(255,107,93,0.08)", "El Niño"),
        lanina: band(-3, -0.5, "rgba(93,184,255,0.08)", "La Niña"),
      },
    },
  },
};

export default function EnsoChart({ ts }: { ts: TimeSeries }) {
  const data = {
    datasets: [
      { label: "Daily anomaly", data: toXY(ts.anomaly), borderColor: "rgba(79,157,255,0.3)", borderWidth: 1, pointRadius: 0, tension: 0.3 },
      { label: "30-day index (ONI)", data: toXY(ts.rolling), borderColor: "#38e0c4", borderWidth: 2.5, pointRadius: 0, tension: 0.3, fill: "origin", backgroundColor: fill },
      { label: "Projection", data: toXY(ts.projection), borderColor: "#ffb454", borderWidth: 2, borderDash: [6, 5], pointRadius: 0, tension: 0.3 },
    ],
  };
  return <Line options={options} data={data} height={110} />;
}
