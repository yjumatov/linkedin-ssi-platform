// ── SSI Snapshots ──────────────────────────────────────────────────────────────
export interface SSISnapshot {
  id: string;
  user_id: string;
  snapshot_date: string;
  total_score: number;
  professional_brand_score: number;
  find_right_people_score: number;
  engage_with_insights_score: number;
  build_relationships_score: number;
  industry_avg_score: number | null;
  network_avg_score: number | null;
  screenshot_path: string | null;
  delta_1d: number | null;
  delta_7d: number | null;
  delta_30d: number | null;
  created_at: string;
}

export interface SSILatestResponse {
  snapshot: SSISnapshot;
  previous: SSISnapshot | null;
}

export interface SSIHistoryResponse {
  snapshots: SSISnapshot[];
  total: number;
  page: number;
  page_size: number;
}

// ── Analytics ──────────────────────────────────────────────────────────────────
export interface ComponentAnalytics {
  current: number;
  delta_1d: number | null;
  delta_7d: number | null;
  delta_30d: number | null;
  avg_7d: number | null;
  avg_30d: number | null;
  trend: "up" | "down" | "stable";
  velocity: number | null;
}

export interface AnalyticsResponse {
  as_of_date: string;
  total: ComponentAnalytics;
  professional_brand: ComponentAnalytics;
  find_right_people: ComponentAnalytics;
  engage_with_insights: ComponentAnalytics;
  build_relationships: ComponentAnalytics;
  industry_avg: number | null;
  network_avg: number | null;
  data_points: number;
  weakest_component: string | null;
  strongest_component: string | null;
  insights: string[];
}

export interface TrendPoint {
  date: string;
  total_score: number;
  professional_brand_score: number;
  find_right_people_score: number;
  engage_with_insights_score: number;
  build_relationships_score: number;
}

export interface TrendResponse {
  points: TrendPoint[];
  period_days: number;
}

// ── Recommendations ────────────────────────────────────────────────────────────
export interface Recommendation {
  id: string;
  user_id: string;
  snapshot_id: string | null;
  category: string;
  priority: "high" | "medium" | "low";
  title: string;
  root_cause: string;
  recommendation: string;
  expected_impact: string;
  action_steps: string | null;
  ai_provider: string;
  ai_model: string | null;
  is_read: boolean;
  is_dismissed: boolean;
  created_at: string;
}

export interface RecommendationsResponse {
  recommendations: Recommendation[];
  total: number;
  unread: number;
}

// ── Scraping ───────────────────────────────────────────────────────────────────
export interface ScrapeRun {
  id: string;
  status: "running" | "success" | "failed";
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  retry_count: number;
  trigger: string;
}

export interface ScrapeRunResponse {
  run: ScrapeRun;
  message: string;
}

// ── UI helpers ─────────────────────────────────────────────────────────────────
export type TrendDirection = "up" | "down" | "stable";
export type Priority = "high" | "medium" | "low";
