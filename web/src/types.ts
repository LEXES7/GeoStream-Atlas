export type Phase = "el_nino" | "la_nina" | "neutral" | "unknown";

export interface RegionAnomaly {
  name: string;
  observed_sst_c: number | null;
  climatology_c: number | null;
  anomaly_c: number | null;
  phase: Phase;
}

export interface Enso {
  date: string;
  iso_date: string;
  regions: RegionAnomaly[];
  nino34_anomaly_c: number | null;
  phase: Phase;
  note: string;
}

export interface City {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  temperature_c: number | null;
  apparent_temperature_c: number | null;
  humidity_pct: number | null;
  precipitation_mm: number | null;
  cloud_cover_pct: number | null;
  wind_speed_kmh: number | null;
  weather_code: number | null;
}

export interface NinoRegion {
  name: string;
  region: string;
  latitude: number;
  longitude: number;
  sea_surface_temperature_c: number | null;
  wave_height_m: number | null;
}

export interface Extremum {
  city: string;
  country: string;
  temp_c: number | null;
}

export interface Stats {
  city_count: number;
  country_count: number;
  avg_temp_c?: number;
  hottest?: Extremum;
  coldest?: Extremum;
}

export interface Latest {
  date: string;
  iso_date: string;
  slot?: string;
  generated_utc?: string;
  enso: Enso;
  forecast: {
    current_oni: number | null;
    current_phase: Phase;
    trend_per_month: number | null;
    note: string;
  };
  stats: Stats;
  cities: City[];
  nino_regions: NinoRegion[];
}

export interface SeriesPoint {
  date: string;
  value: number;
}

export interface TimeSeries {
  anomaly: SeriesPoint[];
  rolling: SeriesPoint[];
  projection: SeriesPoint[];
  note: string;
}

export interface SlotPoint {
  slot: string;
  value: number;
}

export interface Intraday {
  temp: SlotPoint[];
  sst: SlotPoint[];
}
