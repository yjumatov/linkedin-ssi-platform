"use client";

import { useEffect, useState } from "react";
import { getAnalytics, getTrends } from "@/lib/api";
import type { AnalyticsResponse, TrendResponse } from "@/types";
import TrendChart from "@/components/dashboard/TrendChart";
import DeltaBadge from "@/components/ui/DeltaBadge";
import { PageLoader } from "@/components/ui/Spinner";
import { cn, trendColor, trendIcon } from "@/lib/utils";

const PERIODS = [7, 14, 30, 90] as const;

const COMPONENT_CONFIG = [
  { key: "professional_brand" as const, label: "Professional Brand", icon: "🏆", color: "#0077b5" },
  { key: "find_right_people" as const, label: "Find Right People", icon: "🔍", color: "#7c3aed" },
  { key: "engage_with_insights" as const, label: "Engage with Insights", icon: "💡", color: "#059669" },
  { key: "build_relationships" as const, label: "Build Relationships", icon: "🤝", color: "#d97706" },
];

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [trends, setTrends] = useState<TrendResponse | null>(null);
  const [period, setPeriod] = useState<number>(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getAnalytics(), getTrends(period)])
      .then(([a, t]) => {
        setAnalytics(a);
        setTrends(t);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [period]);

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Analytics</h1>
        <p className="text-slate-500 text-sm mt-1">
          Deep dive into your SSI trends and component performance.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {analytics && (
        <>
          {/* Period selector + trend chart */}
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">Historical Trends</h3>
              <div className="flex gap-1">
                {PERIODS.map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={cn(
                      "px-3 py-1 rounded-md text-xs font-medium transition-colors",
                      period === p
                        ? "bg-[#0077b5] text-white"
                        : "text-slate-600 hover:bg-slate-100"
                    )}
                  >
                    {p}d
                  </button>
                ))}
              </div>
            </div>
            <div className="card-body">
              {trends && <TrendChart data={trends.points} />}
            </div>
          </div>

          {/* Component breakdown */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-semibold text-slate-900">Component Analysis</h3>
            </div>
            <div className="card-body">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500 border-b border-slate-100">
                      <th className="pb-3 font-medium">Component</th>
                      <th className="pb-3 font-medium text-right">Score</th>
                      <th className="pb-3 font-medium text-right">1 Day</th>
                      <th className="pb-3 font-medium text-right">7 Days</th>
                      <th className="pb-3 font-medium text-right">30 Days</th>
                      <th className="pb-3 font-medium text-right">7d Avg</th>
                      <th className="pb-3 font-medium text-right">Trend</th>
                      <th className="pb-3 font-medium text-right">Velocity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {[
                      { key: "total" as const, label: "Total SSI", icon: "📊", max: 100 },
                      ...COMPONENT_CONFIG.map((c) => ({ ...c, max: 25 })),
                    ].map(({ key, label, icon, max }) => {
                      const comp = analytics[key];
                      return (
                        <tr key={key} className="hover:bg-slate-50/50">
                          <td className="py-3 font-medium text-slate-800">
                            <span className="mr-2">{icon}</span>
                            {label}
                            {analytics.weakest_component === key && (
                              <span className="ml-2 text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">
                                Focus
                              </span>
                            )}
                          </td>
                          <td className="py-3 text-right font-semibold">
                            {comp.current.toFixed(1)}/{max}
                          </td>
                          <td className="py-3 text-right">
                            <DeltaBadge delta={comp.delta_1d} size="sm" />
                          </td>
                          <td className="py-3 text-right">
                            <DeltaBadge delta={comp.delta_7d} size="sm" />
                          </td>
                          <td className="py-3 text-right">
                            <DeltaBadge delta={comp.delta_30d} size="sm" />
                          </td>
                          <td className="py-3 text-right text-slate-500">
                            {comp.avg_7d?.toFixed(1) ?? "—"}
                          </td>
                          <td className={cn("py-3 text-right font-medium", trendColor(comp.trend))}>
                            {trendIcon(comp.trend)} {comp.trend}
                          </td>
                          <td className={cn("py-3 text-right text-xs", comp.velocity && comp.velocity > 0 ? "text-emerald-600" : "text-red-500")}>
                            {comp.velocity != null ? `${comp.velocity > 0 ? "+" : ""}${comp.velocity.toFixed(2)} /wk` : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Component chart */}
          <div className="card">
            <div className="card-header">
              <h3 className="font-semibold text-slate-900">Component Trends</h3>
            </div>
            <div className="card-body">
              {trends && <TrendChart data={trends.points} showComponents />}
            </div>
          </div>

          {/* Insights */}
          {analytics.insights.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="font-semibold text-slate-900">Key Insights</h3>
              </div>
              <div className="card-body space-y-2">
                {analytics.insights.map((insight, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 rounded-lg bg-blue-50/50 border border-blue-100"
                  >
                    <span className="text-[#0077b5] text-lg mt-0.5">•</span>
                    <p className="text-sm text-slate-700">{insight}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
