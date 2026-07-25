"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { CategoryBreakdown } from "@/lib/types";

const COLORS = ["#D85A30", "#0F6E56", "#6366F1", "#E5A100", "#EC4899", "#8B5CF6", "#14B8A6", "#F59E0B", "#6B7280"];

interface CategoryPieChartProps {
  data: CategoryBreakdown[];
}

export default function CategoryPieChart({ data }: CategoryPieChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-52 text-gray-500 text-sm">
        No category data available
      </div>
    );
  }

  const chartData = data.map((item) => ({
    name: item.display_name,
    value: Math.round(item.monthly_amount),
    count: item.count,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="rounded-lg bg-[#1E293B] border border-white/10 p-3 shadow-xl">
          <p className="text-white font-medium text-sm">{d.name}</p>
          <p className="text-gray-400 text-xs">₹{d.value.toLocaleString()}/mo • {d.count} sub{d.count > 1 ? "s" : ""}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="w-full h-52">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
            >
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5">
        {chartData.map((entry, index) => (
          <div key={entry.name} className="flex items-center gap-1.5">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: COLORS[index % COLORS.length] }}
            />
            <span className="text-xs text-gray-400">{entry.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
