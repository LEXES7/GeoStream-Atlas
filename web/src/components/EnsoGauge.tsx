import { motion } from "framer-motion";

const MIN = -3;
const MAX = 3;
const START = -120; // degrees
const SWEEP = 240;

function valueToAngle(v: number) {
  const clamped = Math.max(MIN, Math.min(MAX, v));
  return START + ((clamped - MIN) / (MAX - MIN)) * SWEEP;
}

function polar(cx: number, cy: number, r: number, deg: number) {
  const rad = ((deg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function arc(cx: number, cy: number, r: number, a0: number, a1: number) {
  const s = polar(cx, cy, r, a1);
  const e = polar(cx, cy, r, a0);
  const large = a1 - a0 <= 180 ? 0 : 1;
  return `M ${s.x} ${s.y} A ${r} ${r} 0 ${large} 0 ${e.x} ${e.y}`;
}

export default function EnsoGauge({ value }: { value: number | null }) {
  const cx = 120;
  const cy = 120;
  const r = 92;
  const v = value ?? 0;
  const needle = valueToAngle(v);

  const zones: [number, number, string][] = [
    [MIN, -0.5, "#5db8ff"],
    [-0.5, 0.5, "#38e0c4"],
    [0.5, MAX, "#ff6b5d"],
  ];

  return (
    <svg viewBox="0 0 240 170" className="gauge">
      {zones.map(([a, b, color], i) => (
        <path
          key={i}
          d={arc(cx, cy, r, valueToAngle(a), valueToAngle(b))}
          stroke={color}
          strokeWidth={14}
          strokeLinecap="round"
          fill="none"
          opacity={0.85}
        />
      ))}

      {[-3, -2, -1, 0, 1, 2, 3].map((t) => {
        const p1 = polar(cx, cy, r - 18, valueToAngle(t));
        const p2 = polar(cx, cy, r - 26, valueToAngle(t));
        const lbl = polar(cx, cy, r - 36, valueToAngle(t));
        return (
          <g key={t}>
            <line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} stroke="rgba(255,255,255,0.3)" strokeWidth={1.5} />
            <text x={lbl.x} y={lbl.y} className="gauge-tick" textAnchor="middle" dominantBaseline="middle">
              {t > 0 ? `+${t}` : t}
            </text>
          </g>
        );
      })}

      <motion.line
        x1={cx}
        y1={cy}
        x2={polar(cx, cy, r - 12, needle).x}
        y2={polar(cx, cy, r - 12, needle).y}
        stroke="#e7ecf5"
        strokeWidth={3}
        strokeLinecap="round"
        initial={{ x2: polar(cx, cy, r - 12, valueToAngle(0)).x, y2: polar(cx, cy, r - 12, valueToAngle(0)).y }}
        animate={{ x2: polar(cx, cy, r - 12, needle).x, y2: polar(cx, cy, r - 12, needle).y }}
        transition={{ type: "spring", stiffness: 60, damping: 12, delay: 0.2 }}
      />
      <circle cx={cx} cy={cy} r={6} fill="#e7ecf5" />
      <text x={cx} y={cy + 34} className="gauge-value" textAnchor="middle">
        {value === null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(2)} °C`}
      </text>
    </svg>
  );
}
