"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { getSubscriptionDetail, generateNegotiationScript } from "@/lib/api";
import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import ActionButtons from "@/components/ActionButtons";

export default function SubscriptionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const id = params.id as string;

  const [negotiationMessage, setNegotiationMessage] = useState<string | null>(null);
  const [negLoading, setNegLoading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const { data: sub, isLoading } = useQuery({
    queryKey: ["subscription", id],
    queryFn: () => getSubscriptionDetail(id),
  });

  const handleGenerateScript = async () => {
    setNegLoading(true);
    try {
      const result = await generateNegotiationScript(id);
      setNegotiationMessage(result.message);
    } catch (err) {
      setNegotiationMessage("Unable to generate a message at this time. Please try again.");
    } finally {
      setNegLoading(false);
    }
  };

  const handleActionTaken = (result: any) => {
    setToast(result.message);
    queryClient.invalidateQueries({ queryKey: ["subscription", id] });
    queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    queryClient.invalidateQueries({ queryKey: ["growth-summary"] });
    setTimeout(() => setToast(null), 5000);
  };

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-64 bg-white/10 rounded-lg" />
          <div className="h-48 bg-white/5 rounded-xl border border-white/10" />
          <div className="h-48 bg-white/5 rounded-xl border border-white/10" />
        </div>
      </div>
    );
  }

  if (!sub) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 text-center">
        <p className="text-gray-400">Subscription not found.</p>
      </div>
    );
  }

  const merchantTitle = sub.merchant_normalized
    .split(" ")
    .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

  const getScoreColor = (s: number) => {
    if (s <= 30) return "#0F6E56";
    if (s <= 55) return "#E5A100";
    if (s <= 75) return "#D85A30";
    return "#DC2626";
  };

  const priceChartData = sub.price_history?.map((ph: any) => ({
    date: new Date(ph.effective_date).toLocaleDateString("en-IN", { month: "short", year: "2-digit" }),
    amount: ph.amount,
  })) || [];

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 animate-in">
      {/* Toast */}
      {toast && (
        <div className="fixed top-20 right-4 z-50 px-4 py-3 rounded-xl bg-[#0F6E56] text-white text-sm font-medium shadow-xl shadow-[#0F6E56]/25 animate-in">
          ✅ {toast}
        </div>
      )}

      {/* Back Button */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1.5 text-gray-400 text-sm hover:text-white transition-colors mb-6"
      >
        ← Back to Dashboard
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">{merchantTitle}</h1>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="text-sm text-gray-500">{sub.category_display}</span>
            <span className="text-gray-600">•</span>
            <span className="text-sm text-gray-500 capitalize">{sub.frequency}</span>
            <span className="text-gray-600">•</span>
            <span className="text-sm font-semibold text-white">₹{sub.current_amount.toLocaleString()}</span>
          </div>
        </div>
        {sub.leak_score !== null && (
          <div
            className="flex flex-col items-center px-4 py-3 rounded-xl border"
            style={{
              borderColor: getScoreColor(sub.leak_score) + "30",
              backgroundColor: getScoreColor(sub.leak_score) + "08",
            }}
          >
            <span className="text-2xl font-bold" style={{ color: getScoreColor(sub.leak_score) }}>
              {Math.round(sub.leak_score)}
            </span>
            <span className="text-[10px] text-gray-500 uppercase tracking-wide">Leak Score</span>
          </div>
        )}
      </div>

      {/* Score Components */}
      {sub.score_components && (
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5 mb-6">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Score Breakdown</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {Object.entries(sub.score_components).map(([key, value]) => {
              const labels: Record<string, string> = {
                unused: "Unused",
                price_hike: "Price Hike",
                redundancy: "Redundancy",
                relative_cost: "Relative Cost",
              };
              const weights: Record<string, string> = {
                unused: "40%",
                price_hike: "30%",
                redundancy: "20%",
                relative_cost: "10%",
              };
              return (
                <div key={key}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs text-gray-500">{labels[key] || key}</span>
                    <span className="text-[10px] text-gray-600">w:{weights[key]}</span>
                  </div>
                  <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${value}%`,
                        backgroundColor: (value as number) > 60 ? "#D85A30" : (value as number) > 30 ? "#E5A100" : "#0F6E56",
                      }}
                    />
                  </div>
                  <p className="text-xs text-white font-medium mt-1">{Math.round(value as number)}%</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommendation Reason */}
      {sub.reason && (
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5 mb-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Analysis</h3>
          <p className="text-white text-sm leading-relaxed">{sub.reason}</p>
          {sub.price_hike_detected && sub.price_hike_pct && (
            <div className="mt-3 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20">
              <p className="text-red-400 text-xs font-medium">
                ⚠️ Price increased by {sub.price_hike_pct.toFixed(1)}% — a silent hike was detected in your charges.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Price History Chart */}
      {priceChartData.length >= 2 && (
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5 mb-6">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Price History</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={priceChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" stroke="rgba(255,255,255,0.2)" tick={{ fill: "#6B7280", fontSize: 11 }} />
                <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fill: "#6B7280", fontSize: 11 }} tickFormatter={(v: number) => `₹${v}`} />
                <Tooltip
                  contentStyle={{
                    background: "#1E293B",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(value) => [`₹${value}`, "Price"]}
                />
                <Line
                  type="stepAfter"
                  dataKey="amount"
                  stroke={sub.price_hike_detected ? "#D85A30" : "#0F6E56"}
                  strokeWidth={2.5}
                  dot={{ fill: sub.price_hike_detected ? "#D85A30" : "#0F6E56", r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5 mb-6">
        <h3 className="text-sm font-medium text-gray-400 mb-3">Take Action</h3>
        <ActionButtons
          subscriptionId={id}
          currentRecommendation={sub.recommendation}
          currentStatus={sub.status}
          onActionTaken={handleActionTaken}
        />
      </div>

      {/* Negotiation Script Generator */}
      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5 mb-6">
        <h3 className="text-sm font-medium text-gray-400 mb-2">Negotiation Assistant</h3>
        <p className="text-xs text-gray-500 mb-3">
          Generate a polite message to send to {merchantTitle}&apos;s support team.
        </p>
        {!negotiationMessage ? (
          <button
            onClick={handleGenerateScript}
            disabled={negLoading}
            className="w-full py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-gray-300 font-medium hover:bg-white/10 transition-all disabled:opacity-50"
          >
            {negLoading ? "Generating..." : "💬 Generate Negotiation Message"}
          </button>
        ) : (
          <div className="space-y-3">
            <div className="rounded-lg bg-white/5 border border-white/10 p-4">
              <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
                {negotiationMessage}
              </pre>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => navigator.clipboard.writeText(negotiationMessage)}
                className="flex-1 py-2 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-300 hover:bg-white/10 transition-all"
              >
                📋 Copy to Clipboard
              </button>
              <button
                onClick={handleGenerateScript}
                disabled={negLoading}
                className="py-2 px-4 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-300 hover:bg-white/10 transition-all"
              >
                🔄
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
