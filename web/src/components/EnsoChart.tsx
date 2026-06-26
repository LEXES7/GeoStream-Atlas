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
} from "chart.js";
import "chartjs-adapter-date-fns";
import type { SeriesPoint, TimeSeries } from "../types";

ChartJS.register(LineElement, PointElement, LinearScale, TimeScale, Tooltip, Legend, Filler);

const toXY = (arr: SeriesPoint[]) => arr.map((p) => ({ x: p.date, y: p.value }));

const options: ChartOptions<"line"> = {
  responsive: true,
  maintainAspectRatio: true,
  interaction: { mode: "index", intersect: false },
  scales: {
    x: {
      type: "time",
      time: { unit: "month" },
      grid: { color: "rgba(255,255,255,0.05)" },
      ticks: { color: "#8a96ab" },
    },
    y: {
      grid: { color: "rgba(255,255,255,0.05)" },
      ticks: { color: "#8a96ab" },
      title: { display: true, text: "°C anomaly", color: "#8a96ab" },
    },
  },
  plugins: {
    legend: { labels: { color: "#e7ecf5", boxWidth: 12, font: { size: 12 } } },
  },
};

export default function EnsoChart({ ts }: { ts: TimeSeries }) {
  const data = {
    datasets: [
      {
        label: "Daily anomaly",
        data: toXY(ts.anomaly),
        borderColor: "rgba(79,157,255,0.35)",
        borderWidth: 1,
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: "30-day index (ONI)",
        data: toXY(ts.rolling),
        borderColor: "#38e0c4",
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.3,
      },
      {
        label: "Projection",
        data: toXY(ts.projection),
        borderColor: "#ffb454",
        borderWidth: 2,
        borderDash: [6, 5],
        pointRadius: 0,
        tension: 0.3,
      },
    ],
  };
  return <Line options={options} data={data} height={110} />;
}
