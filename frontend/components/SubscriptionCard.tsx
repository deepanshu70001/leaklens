"use client";

import Link from "next/link";
import { Subscription } from "@/lib/types";
import PriceHistorySparkline from "./PriceHistorySparkline";

interface SubscriptionCardProps {
  subscription: Subscription;
}

export default function SubscriptionCard({ subscription }: SubscriptionCardProps) {
  const {
    id,
    merchant_normalized,
    current_amount,
    currency,
    frequency,
    leak_score,
    recommendation,
    reason,
    price_hike_detected,
    price_hike_pct,
    price_history,
    category_display,
    status,
  } = subscription;

  const getScoreColor = (score: number | null) => {
    if (score === null) return "text-gray-400";
    if (score <= 30) return "text-emerald-400";
    if (score <= 55) return "text-yellow-400";
    if (score <= 75) return "text-orange-400";
    return "text-red-400";
  };

  const getRecBadge = (rec: string | null) => {
    const styles: Record<string, string> = {
      keep: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
      downgrade: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20",
      renegotiate: "bg-orange-500/15 text-orange-400 border-orange-500/20",
      cancel: "bg-red-500/15 text-red-400 border-red-500/20",
    };
    return rec ? styles[rec] || styles.keep : styles.keep;
  };

  const freqLabel: Record<string, string> = {
    weekly: "/wk",
    monthly: "/mo",
    annual: "/yr",
  };

  const merchantTitle = merchant_normalized
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");

  return (
    <Link href={`/subscriptions/${id}`}>
      <div className={`group rounded-xl border p-4 transition-all duration-200 hover:scale-[1.01] hover:shadow-lg hover:shadow-black/20 cursor-pointer ${
        status === "canceled"
          ? "border-white/5 bg-white/[0.02] opacity-60"
          : "border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]"
      }`}>
        <div className="flex items-start justify-between gap-3">
          {/* Left: Merchant info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-white font-medium text-sm truncate">{merchantTitle}</h3>
              {status === "canceled" && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-500/20 text-gray-400">Canceled</span>
              )}
              {status === "downgraded" && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-400">Downgraded</span>
              )}
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs text-gray-500">{category_display}</span>
              <span className="text-gray-600">•</span>
              <span className="text-xs text-gray-500 capitalize">{frequency}</span>
            </div>

            {/* Badges */}
            <div className="flex flex-wrap gap-1.5">
              {recommendation && (
                <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border uppercase tracking-wide ${getRecBadge(recommendation)}`}>
                  {recommendation}
                </span>
              )}
              {price_hike_detected && price_hike_pct && (
                <span className="text-[10px] font-medium px-2 py-0.5 rounded-full border bg-red-500/10 text-red-400 border-red-500/20">
                  ↑ {price_hike_pct.toFixed(0)}% hike
                </span>
              )}
            </div>
          </div>

          {/* Right: Amount + Score + Sparkline */}
          <div className="flex flex-col items-end gap-1.5 shrink-0">
            <div className="text-right">
              <span className="text-white font-semibold text-base">
                ₹{current_amount.toLocaleString()}
              </span>
              <span className="text-gray-500 text-xs">{freqLabel[frequency] || "/mo"}</span>
            </div>
            {leak_score !== null && (
              <span className={`text-xs font-semibold ${getScoreColor(leak_score)}`}>
                Score: {Math.round(leak_score)}
              </span>
            )}
            {price_history && price_history.length >= 2 && (
              <PriceHistorySparkline data={price_history} hikeDetected={price_hike_detected} />
            )}
          </div>
        </div>

        {/* Reason */}
        {reason && (
          <p className="mt-2.5 text-xs text-gray-400 leading-relaxed line-clamp-2 border-t border-white/5 pt-2.5">
            {reason}
          </p>
        )}
      </div>
    </Link>
  );
}
