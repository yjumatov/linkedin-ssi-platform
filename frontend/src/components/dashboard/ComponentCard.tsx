"use client";

import { cn, trendColor, trendIcon } from "@/lib/utils";
import DeltaBadge from "@/components/ui/DeltaBadge";
import type { ComponentAnalytics } from "@/types";

interface ComponentCardProps {
  label: string;
  icon: string;
  analytics: ComponentAnalytics;
  maxScore?: number;
  isWeakest?: boolean;
}

export default function ComponentCard({
  label,
  icon,
  analytics,
  maxScore = 25,
  isWeakest = false,
}: ComponentCardProps) {
  const pct = (analytics.current / maxScore) * 100;

  const barColor =
    pct >= 75 ? "bg-emerald-500" : pct >= 50 ? "bg-[#0077b5]" : pct >= 25 ? "bg-amber-400" : "bg-red-400";

  return (
    <div
      className={cn(
        "card p-5 transition-all hover:shadow-md",
        isWeakest && "ring-2 ring-amber-300"
      )}
    >
      {isWeakest && (
        <div className="flex items-center gap-1 mb-2">
          <span className="text-xs text-amber-600 font-medium bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
            Focus Area
          </span>
        </div>
      )}
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-lg mr-1 inline">{icon}</p>
          <p className="text-sm font-medium text-slate-700 inline">{label}</p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-slate-900">
            {analytics.current.toFixed(0)}
          </span>
          <span className="text-slate-400 text-sm">/{maxScore}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-slate-100 rounded-full mb-3 overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-700", barColor)}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Deltas */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <span>1d</span>
          <DeltaBadge delta={analytics.delta_1d} size="sm" />
        </div>
        <div className="flex items-center gap-2">
          <span>7d</span>
          <DeltaBadge delta={analytics.delta_7d} size="sm" />
        </div>
        <div className="flex items-center gap-2">
          <span>30d</span>
          <DeltaBadge delta={analytics.delta_30d} size="sm" />
        </div>
        <span className={cn("font-medium", trendColor(analytics.trend))}>
          {trendIcon(analytics.trend)} {analytics.trend}
        </span>
      </div>
    </div>
  );
}
