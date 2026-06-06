"use client";

import { cn } from "@/lib/utils";

interface SSIGaugeProps {
  score: number;
  maxScore?: number;
  size?: "sm" | "md" | "lg";
  label?: string;
}

const SIZE_MAP = {
  sm: { r: 36, strokeWidth: 6, textSize: "text-2xl", containerSize: "w-24 h-24" },
  md: { r: 52, strokeWidth: 8, textSize: "text-4xl", containerSize: "w-36 h-36" },
  lg: { r: 70, strokeWidth: 10, textSize: "text-5xl", containerSize: "w-48 h-48" },
};

function scoreColor(score: number, max: number): string {
  const pct = score / max;
  if (pct >= 0.75) return "#16a34a";
  if (pct >= 0.5) return "#0077b5";
  if (pct >= 0.25) return "#f59e0b";
  return "#ef4444";
}

export default function SSIGauge({ score, maxScore = 100, size = "md", label }: SSIGaugeProps) {
  const { r, strokeWidth, textSize, containerSize } = SIZE_MAP[size];
  const cx = r + strokeWidth;
  const cy = r + strokeWidth;
  const viewSize = (r + strokeWidth) * 2;
  const circumference = 2 * Math.PI * r;
  const pct = Math.min(score / maxScore, 1);
  const offset = circumference * (1 - pct);
  const color = scoreColor(score, maxScore);

  return (
    <div className={cn("relative flex items-center justify-center flex-col", containerSize)}>
      <svg width={viewSize} height={viewSize} viewBox={`0 0 ${viewSize} ${viewSize}`} className="absolute">
        {/* Background track */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={strokeWidth}
        />
        {/* Progress arc */}
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="relative flex flex-col items-center">
        <span className={cn("font-bold leading-none", textSize)} style={{ color }}>
          {Math.round(score)}
        </span>
        {label && <span className="text-xs text-slate-400 mt-1">{label}</span>}
        {!label && <span className="text-xs text-slate-400 mt-1">/ {maxScore}</span>}
      </div>
    </div>
  );
}
