import type { City } from "../types";

const ORDER = ["All", "Asia", "Europe", "Africa", "North America", "South America", "Oceania"];

export default function RegionFilter({
  cities,
  active,
  onChange,
}: {
  cities: City[];
  active: string;
  onChange: (c: string) => void;
}) {
  const counts = new Map<string, number>();
  for (const c of cities) {
    const k = c.continent ?? "Other";
    counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  const present = ORDER.filter((c) => c === "All" || counts.has(c));

  return (
    <div className="region-filter">
      {present.map((c) => (
        <button
          key={c}
          className={`region-chip ${active === c ? "active" : ""}`}
          onClick={() => onChange(c)}
        >
          {c}
          <span className="region-count">{c === "All" ? cities.length : counts.get(c)}</span>
        </button>
      ))}
    </div>
  );
}
