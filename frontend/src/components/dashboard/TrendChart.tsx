"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { formatShortDate } from "@/lib/utils";
import type { TrendPoint } from "@/types";

interface TrendChartProps {
  data: TrendPoint[];
  showComponents?: boolean;
}

const COMPONENT_LINES = [
  { key: "professional_brand_score", color: "#0077b5", label: "Professional Brand" },
  { key: "find_right_people_score", color: "#7c3aed", label: "Find Right People" },
  { key: "engage_with_insights_score", color: "#059669", label: "Engage with Insights" },
  { key: "build_relationships_score", color: "#d97706", label: "Build Relationships" },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-xs">
      <p className="font-semibold text-slate-700 mb-2">{label}</p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4">
          <span style={{ color: entry.color }} className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full inline-block" style={{ background: entry.color }} />
            {entry.name}
          </span>
          <span className="font-medium text-slate-800">{entry.value?.toFixed(1)}</span>
        </div>
      ))}
    </div>
  );
};

export default function TrendChart({ data, showComponents = false }: TrendChartProps) {
  const chartData = data.map((p) => ({
    ...p,
    date: formatShortDate(p.date),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          tickLine={false}
          axisLine={false}
          domain={showComponents ? [0, 25] : [0, 100]}
        />
        <Tooltip content={<CustomTooltip />} />
        {!showComponents && (
          <>
            <Legend
              wrapperStyle={{ fontSize: "12px", paddingTop: "12px" }}
              iconType="circle"
              iconSize={8}
            />
            <Line
              type="monotone"
              dataKey="total_score"
              stroke="#0077b5"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 4, fill: "#0077b5" }}
              name="Total SSI"
            />
          </>
        )}
        {showComponents && (
          <>
            <Legend
              wrapperStyle={{ fontSize: "11px", paddingTop: "12px" }}
              iconType="circle"
              iconSize={8}
            />
            {COMPONENT_LINES.map(({ key, color, label }) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 3 }}
                name={label}
              />
            ))}
          </>
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
