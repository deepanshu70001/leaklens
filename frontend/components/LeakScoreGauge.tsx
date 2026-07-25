"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

interface LeakScoreGaugeProps {
  score: number;
  size?: number;
}

export default function LeakScoreGauge({ score, size = 200 }: LeakScoreGaugeProps) {
  const getColor = (s: number) => {
    if (s <= 30) return "#0F6E56";
    if (s <= 55) return "#E5A100";
    if (s <= 75) return "#D85A30";
    return "#DC2626";
  };

  const getLabel = (s: number) => {
    if (s <= 30) return "Healthy";
    if (s <= 55) return "Moderate";
    if (s <= 75) return "Leaking";
    return "Critical";
  };

  const color = getColor(score);
  const label = getLabel(score);

  const data = [
    { name: "score", value: score },
    { name: "remaining", value: 100 - score },
  ];

  return (
    <div className="flex flex-col items-center">
      <div style={{ width: size, height: size * 0.65 }} className="relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="95%"
              startAngle={180}
              endAngle={0}
              innerRadius={size * 0.28}
              outerRadius={size * 0.4}
              paddingAngle={0}
              dataKey="value"
              stroke="none"
            >
              <Cell fill={color} />
              <Cell fill="rgba(255,255,255,0.08)" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
          <span className="text-3xl font-bold text-white">{Math.round(score)}</span>
          <span className="text-xs font-medium mt-0.5" style={{ color }}>
            {label}
          </span>
        </div>
      </div>
      <p className="text-xs text-gray-500 mt-2">Avg Leak Score</p>
    </div>
  );
}
