import { fmt } from "../api";
import type { Stats } from "../types";

export default function StatGrid({ stats }: { stats: Stats }) {
  return (
    <div className="stat-grid">
      <article className="card stat">
        <span className="stat-num">{stats.city_count ?? "—"}</span>
        <span className="stat-lbl">Cities tracked</span>
      </article>
      <article className="card stat">
        <span className="stat-num">{stats.country_count ?? "—"}</span>
        <span className="stat-lbl">Countries</span>
      </article>
      <article className="card stat">
        <span className="stat-num">{fmt(stats.avg_temp_c, 1)}</span>
        <span className="stat-lbl">Avg temp (°C)</span>
      </article>
      <article className="card stat hot">
        <span className="stat-num">{stats.hottest ? `${fmt(stats.hottest.temp_c, 0)}°` : "—"}</span>
        <span className="stat-lbl">{stats.hottest ? `Hottest · ${stats.hottest.city}` : "Hottest"}</span>
      </article>
      <article className="card stat cold">
        <span className="stat-num">{stats.coldest ? `${fmt(stats.coldest.temp_c, 0)}°` : "—"}</span>
        <span className="stat-lbl">{stats.coldest ? `Coldest · ${stats.coldest.city}` : "Coldest"}</span>
      </article>
    </div>
  );
}
