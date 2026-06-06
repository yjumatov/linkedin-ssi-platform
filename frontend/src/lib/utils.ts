import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, parseISO } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "MMM d, yyyy");
  } catch {
    return dateStr;
  }
}

export function formatShortDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "MMM d");
  } catch {
    return dateStr;
  }
}

export function formatDelta(delta: number | null | undefined): string {
  if (delta === null || delta === undefined) return "—";
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta.toFixed(1)}`;
}

export function deltaColor(delta: number | null | undefined): string {
  if (delta === null || delta === undefined) return "text-slate-400";
  if (delta > 0) return "text-emerald-600";
  if (delta < 0) return "text-red-500";
  return "text-slate-400";
}

export function trendIcon(trend: string): string {
  if (trend === "up") return "↑";
  if (trend === "down") return "↓";
  return "→";
}

export function trendColor(trend: string): string {
  if (trend === "up") return "text-emerald-600";
  if (trend === "down") return "text-red-500";
  return "text-slate-400";
}

export function priorityColor(priority: string): string {
  switch (priority) {
    case "high":
      return "bg-red-100 text-red-700 border-red-200";
    case "medium":
      return "bg-amber-100 text-amber-700 border-amber-200";
    case "low":
      return "bg-emerald-100 text-emerald-700 border-emerald-200";
    default:
      return "bg-slate-100 text-slate-600 border-slate-200";
  }
}

export function categoryLabel(category: string): string {
  const map: Record<string, string> = {
    overall: "Overall",
    professional_brand: "Professional Brand",
    find_right_people: "Find the Right People",
    engage_insights: "Engage with Insights",
    build_relationships: "Build Relationships",
  };
  return map[category] ?? category;
}

export function scoreToPercent(score: number, max: number): number {
  return Math.min(100, Math.round((score / max) * 100));
}

export function parseActionSteps(raw: string | null): string[] {
  if (!raw) return [];
  try {
    return JSON.parse(raw) as string[];
  } catch {
    return [raw];
  }
}
