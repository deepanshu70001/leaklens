"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { GrowthChartPoint } from "@/lib/types";

interface GrowthChartProps {
  data: GrowthChartPoint[];
}

export default function GrowthChart({ data }: GrowthChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 text-sm">
        No growth data yet. Cancel or downgrade a subscription to start building your growth fund.
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const month = payload[0]?.payload?.month;
      const years = month ? (month / 12).toFixed(1) : "0";
      return (
        <div className="rounded-lg bg-[#1E293B] border border-white/10 p-3 shadow-xl">
          <p className="text-gray-400 text-xs mb-1.5">
            Month {month} ({years} years)
          </p>
          {payload.map((entry: any) => (
            <p key={entry.dataKey} className="text-sm" style={{ color: entry.color }}>
              {entry.dataKey === "projected_value" ? "Projected" : "Contributed"}:{" "}
              <span className="font-semibold">₹{entry.value.toLocaleString()}</span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Show tick labels only at year boundaries
  const yearTicks = [12, 24, 36, 48, 60].filter((m) => m <= data.length);

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="growthGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0F6E56" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#0F6E56" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="contribGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366F1" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#6366F1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="month"
            stroke="rgba(255,255,255,0.2)"
            tick={{ fill: "#6B7280", fontSize: 11 }}
            ticks={yearTicks}
            tickFormatter={(m: number) => `${m / 12}y`}
          />
          <YAxis
            stroke="rgba(255,255,255,0.2)"
            tick={{ fill: "#6B7280", fontSize: 11 }}
            tickFormatter={(v: number) => `₹${(v / 1000).toFixed(0)}k`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="contributed"
            stroke="#6366F1"
            strokeWidth={2}
            fill="url(#contribGradient)"
            name="Contributed"
          />
          <Area
            type="monotone"
            dataKey="projected_value"
            stroke="#0F6E56"
            strokeWidth={2}
            fill="url(#growthGradient)"
            name="Projected Value"
          />
          <Legend
            wrapperStyle={{ paddingTop: 12 }}
            formatter={(value: string) => (
              <span className="text-xs text-gray-400">{value}</span>
            )}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
