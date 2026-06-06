import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn, formatDelta } from "@/lib/utils";

interface DeltaBadgeProps {
  delta: number | null | undefined;
  suffix?: string;
  size?: "sm" | "md";
}

export default function DeltaBadge({ delta, suffix = "", size = "md" }: DeltaBadgeProps) {
  if (delta === null || delta === undefined) {
    return <span className="text-slate-400 text-xs">—</span>;
  }

  const isPositive = delta > 0;
  const isNeutral = delta === 0;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 font-medium rounded-full px-2 py-0.5",
        size === "sm" ? "text-xs" : "text-sm",
        isNeutral && "bg-slate-100 text-slate-500",
        isPositive && "bg-emerald-50 text-emerald-700",
        !isPositive && !isNeutral && "bg-red-50 text-red-600"
      )}
    >
      {isNeutral ? (
        <Minus className="w-3 h-3" />
      ) : isPositive ? (
        <TrendingUp className="w-3 h-3" />
      ) : (
        <TrendingDown className="w-3 h-3" />
      )}
      {formatDelta(delta)}
      {suffix}
    </span>
  );
}
