"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Play, AlertCircle, Calendar } from "lucide-react";
import { getLatestSSI, getAnalytics, getTrends, triggerScrape } from "@/lib/api";
import type { SSILatestResponse, AnalyticsResponse, TrendResponse } from "@/types";
import SSIGauge from "@/components/dashboard/SSIGauge";
import ComponentCard from "@/components/dashboard/ComponentCard";
import TrendChart from "@/components/dashboard/TrendChart";
import DeltaBadge from "@/components/ui/DeltaBadge";
import { PageLoader } from "@/components/ui/Spinner";
import { formatDate } from "@/lib/utils";

const COMPONENTS = [
  { key: "professional_brand" as const, label: "Professional Brand", icon: "🏆" },
  { key: "find_right_people" as const, label: "Find the Right People", icon: "🔍" },
  { key: "engage_with_insights" as const, label: "Engage with Insights", icon: "💡" },
  { key: "build_relationships" as const, label: "Build Relationships", icon: "🤝" },
];

export default function DashboardPage() {
  const [latest, setLatest] = useState<SSILatestResponse | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [trends, setTrends] = useState<TrendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scraping, setScraping] = useState(false);
  const [scrapeMsg, setScrapeMsg] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [latestData, analyticsData, trendsData] = await Promise.allSettled([
        getLatestSSI(),
        getAnalytics(),
        getTrends(30),
      ]);
      if (latestData.status === "fulfilled") setLatest(latestData.value);
      if (analyticsData.status === "fulfilled") setAnalytics(analyticsData.value);
      if (trendsData.status === "fulfilled") setTrends(trendsData.value);

      if (latestData.status === "rejected" && analyticsData.status === "rejected") {
        setError("No SSI data found. Run your first scrape to get started.");
      }
    } catch {
      setError("Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleScrape = async () => {
    setScraping(true);
    setScrapeMsg(null);
    try {
      const result = await triggerScrape();
      setScrapeMsg(result.message);
      setTimeout(loadData, 5000);
    } catch (err: any) {
      setScrapeMsg(err.message ?? "Scrape failed");
    } finally {
      setScraping(false);
    }
  };

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6 animate-[fadeIn_0.3s_ease-in-out]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">SSI Dashboard</h1>
          {latest && (
            <div className="flex items-center gap-1.5 mt-1 text-sm text-slate-500">
              <Calendar className="w-4 h-4" />
              Last updated: {formatDate(latest.snapshot.snapshot_date)}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={loadData} className="btn-secondary">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button onClick={handleScrape} disabled={scraping} className="btn-primary">
            <Play className="w-4 h-4" />
            {scraping ? "Scraping..." : "Run Scrape"}
          </button>
        </div>
      </div>

      {scrapeMsg && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm text-blue-700">
          {scrapeMsg}
        </div>
      )}

      {error && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-amber-500 shrink-0" />
            <div>
              <p className="font-medium text-amber-800">{error}</p>
              <p className="text-sm text-amber-600 mt-1">
                Configure your LinkedIn credentials in Settings, then click &quot;Run Scrape&quot; above.
              </p>
            </div>
          </div>
        </div>
      )}

      {latest && analytics && (
        <>
          {/* Main score card */}
          <div className="card p-6">
            <div className="flex flex-col md:flex-row items-center gap-8">
              <SSIGauge score={latest.snapshot.total_score} size="lg" />
              <div className="flex-1 space-y-3">
                <div>
                  <h2 className="text-xl font-semibold text-slate-900">Social Selling Index</h2>
                  <p className="text-slate-500 text-sm mt-0.5">
                    Your LinkedIn SSI measures how effectively you establish your professional brand,
                    find the right people, engage with insights, and build relationships.
                  </p>
                </div>
                <div className="flex flex-wrap gap-4 pt-1">
                  {[
                    { label: "Today", delta: analytics.total.delta_1d },
                    { label: "7 Days", delta: analytics.total.delta_7d },
                    { label: "30 Days", delta: analytics.total.delta_30d },
                  ].map(({ label, delta }) => (
                    <div key={label} className="bg-slate-50 rounded-lg px-4 py-2 text-center">
                      <p className="text-xs text-slate-500 mb-1">{label}</p>
                      <DeltaBadge delta={delta} />
                    </div>
                  ))}
                  {analytics.industry_avg && (
                    <div className="bg-slate-50 rounded-lg px-4 py-2 text-center">
                      <p className="text-xs text-slate-500 mb-1">vs Industry</p>
                      <DeltaBadge delta={latest.snapshot.total_score - analytics.industry_avg} />
                    </div>
                  )}
                </div>
                {analytics.insights.slice(0, 2).map((insight, i) => (
                  <p key={i} className="text-sm text-slate-600 flex items-start gap-2">
                    <span className="text-[#0077b5] mt-0.5">•</span>
                    {insight}
                  </p>
                ))}
              </div>
            </div>
          </div>

          {/* Component cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {COMPONENTS.map(({ key, label, icon }) => (
              <ComponentCard
                key={key}
                label={label}
                icon={icon}
                analytics={analytics[key]}
                isWeakest={analytics.weakest_component === key}
              />
            ))}
          </div>

          {/* Trend chart */}
          {trends && trends.points.length > 1 && (
            <div className="card">
              <div className="card-header flex items-center justify-between">
                <h3 className="font-semibold text-slate-900">Score Trend (30 Days)</h3>
                <span className="text-xs text-slate-400">{trends.points.length} data points</span>
              </div>
              <div className="card-body">
                <TrendChart data={trends.points} />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
