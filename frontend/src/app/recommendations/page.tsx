"use client";

import { useEffect, useState } from "react";
import { Sparkles, Eye, X, ChevronDown, ChevronUp } from "lucide-react";
import {
  getRecommendations,
  generateRecommendations,
  updateRecommendation,
} from "@/lib/api";
import type { Recommendation, RecommendationsResponse } from "@/types";
import { PageLoader } from "@/components/ui/Spinner";
import { cn, priorityColor, categoryLabel, formatDate, parseActionSteps } from "@/lib/utils";

export default function RecommendationsPage() {
  const [data, setData] = useState<RecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [filterPriority, setFilterPriority] = useState<string>("all");

  const load = async () => {
    try {
      const result = await getRecommendations();
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      await generateRecommendations();
      await load();
    } catch (err: any) {
      setError(err.message ?? "Failed to generate recommendations");
    } finally {
      setGenerating(false);
    }
  };

  const handleMarkRead = async (rec: Recommendation) => {
    if (!rec.is_read) {
      await updateRecommendation(rec.id, { is_read: true });
      await load();
    }
  };

  const handleDismiss = async (rec: Recommendation) => {
    await updateRecommendation(rec.id, { is_dismissed: true });
    await load();
  };

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  if (loading) return <PageLoader />;

  const recs = data?.recommendations ?? [];
  const filtered =
    filterPriority === "all" ? recs : recs.filter((r) => r.priority === filterPriority);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Recommendations</h1>
          <p className="text-slate-500 text-sm mt-1">
            AI-powered insights to improve your Social Selling Index.
          </p>
        </div>
        <button onClick={handleGenerate} disabled={generating} className="btn-primary">
          <Sparkles className="w-4 h-4" />
          {generating ? "Generating..." : "Generate AI Recommendations"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Stats */}
      {data && (
        <div className="flex items-center gap-4">
          <div className="bg-white border border-slate-200 rounded-lg px-4 py-2 text-sm">
            <span className="text-slate-500">Total: </span>
            <span className="font-semibold">{data.total}</span>
          </div>
          {data.unread > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2 text-sm">
              <span className="text-blue-600 font-medium">{data.unread} unread</span>
            </div>
          )}
          {/* Priority filter */}
          <div className="flex gap-1 ml-auto">
            {["all", "high", "medium", "low"].map((p) => (
              <button
                key={p}
                onClick={() => setFilterPriority(p)}
                className={cn(
                  "px-3 py-1 rounded-full text-xs font-medium border transition-colors capitalize",
                  filterPriority === p
                    ? "bg-slate-800 text-white border-slate-800"
                    : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                )}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {filtered.length === 0 && !error && (
        <div className="card p-12 text-center">
          <Sparkles className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-500 font-medium">No recommendations yet</p>
          <p className="text-slate-400 text-sm mt-1">
            Click &quot;Generate AI Recommendations&quot; to get personalized insights.
          </p>
        </div>
      )}

      {/* Recommendation cards */}
      <div className="space-y-3">
        {filtered.map((rec) => {
          const isExpanded = expanded.has(rec.id);
          const steps = parseActionSteps(rec.action_steps);

          return (
            <div
              key={rec.id}
              className={cn(
                "card overflow-hidden transition-all",
                !rec.is_read && "ring-2 ring-blue-100"
              )}
              onClick={() => handleMarkRead(rec)}
            >
              <div className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1">
                    {!rec.is_read && (
                      <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0 mt-1.5" />
                    )}
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-1.5">
                        <span className={cn("badge", priorityColor(rec.priority))}>
                          {rec.priority.toUpperCase()}
                        </span>
                        <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                          {categoryLabel(rec.category)}
                        </span>
                        <span className="text-xs text-slate-400">
                          {rec.ai_provider} • {formatDate(rec.created_at)}
                        </span>
                      </div>
                      <h3 className="font-semibold text-slate-900">{rec.title}</h3>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={(e) => { e.stopPropagation(); toggleExpand(rec.id); }}
                      className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDismiss(rec); }}
                      className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-600"
                      title="Dismiss"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <p className="text-sm text-slate-600 mt-2 line-clamp-2">{rec.recommendation}</p>

                {isExpanded && (
                  <div className="mt-4 space-y-4 border-t border-slate-100 pt-4">
                    <div>
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                        Root Cause
                      </p>
                      <p className="text-sm text-slate-700">{rec.root_cause}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                        Full Recommendation
                      </p>
                      <p className="text-sm text-slate-700">{rec.recommendation}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                        Expected Impact
                      </p>
                      <p className="text-sm text-emerald-700 bg-emerald-50 px-3 py-2 rounded-lg">
                        {rec.expected_impact}
                      </p>
                    </div>
                    {steps.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                          Action Steps
                        </p>
                        <ol className="space-y-1.5">
                          {steps.map((step, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                              <span className="w-5 h-5 rounded-full bg-[#0077b5] text-white text-xs flex items-center justify-center shrink-0 mt-0.5">
                                {i + 1}
                              </span>
                              {step}
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
