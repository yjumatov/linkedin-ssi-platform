import type {
  AnalyticsResponse,
  Recommendation,
  RecommendationsResponse,
  ScrapeRun,
  ScrapeRunResponse,
  SSIHistoryResponse,
  SSILatestResponse,
  TrendResponse,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

async function fetcher<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── SSI ───────────────────────────────────────────────────────────────────────
export const getLatestSSI = () => fetcher<SSILatestResponse>("/ssi/latest");

export const getSSIHistory = (page = 1, pageSize = 30) =>
  fetcher<SSIHistoryResponse>(`/ssi/history?page=${page}&page_size=${pageSize}`);

// ── Analytics ─────────────────────────────────────────────────────────────────
export const getAnalytics = () => fetcher<AnalyticsResponse>("/analytics");

export const getTrends = (days = 30) =>
  fetcher<TrendResponse>(`/analytics/trends?days=${days}`);

// ── Recommendations ───────────────────────────────────────────────────────────
export const getRecommendations = (includeDismissed = false) =>
  fetcher<RecommendationsResponse>(
    `/recommendations?include_dismissed=${includeDismissed}`
  );

export const generateRecommendations = () =>
  fetcher<RecommendationsResponse>("/recommendations/generate", { method: "POST" });

export const updateRecommendation = (
  id: string,
  body: { is_read?: boolean; is_dismissed?: boolean }
) =>
  fetcher<Recommendation>(`/recommendations/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });

// ── Scraping ──────────────────────────────────────────────────────────────────
export const triggerScrape = () =>
  fetcher<ScrapeRunResponse>("/scrape/run", { method: "POST" });

export const getScrapeRuns = (limit = 20) =>
  fetcher<ScrapeRun[]>(`/scrape/runs?limit=${limit}`);

export const getScrapeRun = (id: string) =>
  fetcher<ScrapeRun>(`/scrape/runs/${id}`);
