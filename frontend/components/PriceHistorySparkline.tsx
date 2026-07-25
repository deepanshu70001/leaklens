"use client";

import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import { PriceHistoryEntry } from "@/lib/types";

interface PriceHistorySparklineProps {
  data: PriceHistoryEntry[];
  hikeDetected?: boolean;
}

export default function PriceHistorySparkline({ data, hikeDetected }: PriceHistorySparklineProps) {
  if (!data || data.length < 2) return null;

  const chartData = data.map((d) => ({ amount: d.amount }));
  const color = hikeDetected ? "#D85A30" : "#0F6E56";

  return (
    <div className="w-20 h-8">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <YAxis hide domain={["dataMin - 10", "dataMax + 10"]} />
          <Line
            type="monotone"
            dataKey="amount"
            stroke={color}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
