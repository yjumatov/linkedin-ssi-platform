"use client";

import { useEffect, useState, useCallback } from "react";
import { ChevronLeft, ChevronRight, Camera } from "lucide-react";
import { getSSIHistory } from "@/lib/api";
import type { SSIHistoryResponse, SSISnapshot } from "@/types";
import DeltaBadge from "@/components/ui/DeltaBadge";
import { PageLoader } from "@/components/ui/Spinner";
import { formatDate, cn } from "@/lib/utils";

const PAGE_SIZE = 20;

function ScoreBar({ score, max }: { score: number; max: number }) {
  const pct = (score / max) * 100;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden min-w-12">
        <div
          className="h-full bg-[#0077b5] rounded-full"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium text-slate-700 w-6 text-right">
        {Math.round(score)}
      </span>
    </div>
  );
}

export default function HistoryPage() {
  const [data, setData] = useState<SSIHistoryResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (p: number) => {
    setLoading(true);
    try {
      const result = await getSSIHistory(p, PAGE_SIZE);
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(page);
  }, [page, load]);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">History</h1>
        <p className="text-slate-500 text-sm mt-1">
          Complete record of all SSI snapshots.
          {data && ` ${data.total} total snapshots.`}
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {data?.snapshots.length === 0 && (
        <div className="card p-12 text-center">
          <p className="text-slate-500">No snapshots recorded yet.</p>
        </div>
      )}

      {data && data.snapshots.length > 0 && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">Date</th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">Total</th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium hidden xl:table-cell">
                    Prof. Brand
                  </th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium hidden xl:table-cell">
                    Find People
                  </th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium hidden xl:table-cell">
                    Engage
                  </th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium hidden xl:table-cell">
                    Build Rel.
                  </th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">1d Δ</th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">7d Δ</th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">30d Δ</th>
                  <th className="text-center px-4 py-3 text-slate-500 font-medium">Screenshot</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.snapshots.map((snap) => (
                  <tr key={snap.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-800">
                      {formatDate(snap.snapshot_date)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-lg text-[#0077b5]">
                          {Math.round(snap.total_score)}
                        </span>
                        <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-[#0077b5] rounded-full"
                            style={{ width: `${snap.total_score}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 hidden xl:table-cell w-32">
                      <ScoreBar score={snap.professional_brand_score} max={25} />
                    </td>
                    <td className="px-4 py-3 hidden xl:table-cell w-32">
                      <ScoreBar score={snap.find_right_people_score} max={25} />
                    </td>
                    <td className="px-4 py-3 hidden xl:table-cell w-32">
                      <ScoreBar score={snap.engage_with_insights_score} max={25} />
                    </td>
                    <td className="px-4 py-3 hidden xl:table-cell w-32">
                      <ScoreBar score={snap.build_relationships_score} max={25} />
                    </td>
                    <td className="px-4 py-3">
                      <DeltaBadge delta={snap.delta_1d} size="sm" />
                    </td>
                    <td className="px-4 py-3">
                      <DeltaBadge delta={snap.delta_7d} size="sm" />
                    </td>
                    <td className="px-4 py-3">
                      <DeltaBadge delta={snap.delta_30d} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-center">
                      {snap.screenshot_path ? (
                        <span className="text-[#0077b5]" title={snap.screenshot_path}>
                          <Camera className="w-4 h-4 inline" />
                        </span>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="px-4 py-3 border-t border-slate-100 flex items-center justify-between">
              <p className="text-sm text-slate-500">
                Page {page} of {totalPages} ({data.total} snapshots)
              </p>
              <div className="flex gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded hover:bg-slate-100 disabled:opacity-40"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const p = i + Math.max(1, page - 2);
                  if (p > totalPages) return null;
                  return (
                    <button
                      key={p}
                      onClick={() => setPage(p)}
                      className={cn(
                        "w-8 h-8 rounded text-sm",
                        p === page
                          ? "bg-[#0077b5] text-white"
                          : "hover:bg-slate-100 text-slate-600"
                      )}
                    >
                      {p}
                    </button>
                  );
                })}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-1.5 rounded hover:bg-slate-100 disabled:opacity-40"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
