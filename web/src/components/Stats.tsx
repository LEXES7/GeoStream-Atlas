import { motion } from "framer-motion";
import { useCountUp } from "../hooks/useCountUp";
import { fmt } from "../api";
import type { Stats } from "../types";

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0 },
};

function StatCard({
  value,
  label,
  className = "",
}: {
  value: string | number | null | undefined;
  label: string;
  className?: string;
}) {
  return (
    <motion.article variants={item} className={`card stat ${className}`}>
      <span className="stat-num">{value === null || value === undefined ? "—" : value}</span>
      <span className="stat-lbl">{label}</span>
    </motion.article>
  );
}

export default function StatGrid({ stats }: { stats: Stats }) {
  const cities = useCountUp(stats.city_count, 1000, 0);
  const countries = useCountUp(stats.country_count, 1000, 0);
  const avg = useCountUp(stats.avg_temp_c, 1200, 1);

  return (
    <motion.div
      className="stat-grid"
      variants={{ show: { transition: { staggerChildren: 0.07 } } }}
      initial="hidden"
      animate="show"
    >
      <StatCard value={cities} label="Cities tracked" />
      <StatCard value={countries} label="Countries" />
      <StatCard value={avg} label="Avg temp (°C)" />
      <StatCard
        value={stats.hottest ? `${fmt(stats.hottest.temp_c, 0)}°` : null}
        label={stats.hottest ? `Hottest · ${stats.hottest.city}` : "Hottest"}
        className="hot"
      />
      <StatCard
        value={stats.coldest ? `${fmt(stats.coldest.temp_c, 0)}°` : null}
        label={stats.coldest ? `Coldest · ${stats.coldest.city}` : "Coldest"}
        className="cold"
      />
    </motion.div>
  );
}
