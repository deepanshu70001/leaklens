"use client";

import { useState } from "react";
import { Subscription } from "@/lib/types";
import SubscriptionCard from "./SubscriptionCard";

interface SubscriptionListProps {
  subscriptions: Subscription[];
}

type SortKey = "score" | "amount" | "name";
type FilterKey = "all" | "keep" | "downgrade" | "renegotiate" | "cancel";

export default function SubscriptionList({ subscriptions }: SubscriptionListProps) {
  const [sortBy, setSortBy] = useState<SortKey>("score");
  const [filterBy, setFilterBy] = useState<FilterKey>("all");

  const filtered = subscriptions.filter((s) => {
    if (filterBy === "all") return true;
    return s.recommendation === filterBy;
  });

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === "score") return (b.leak_score || 0) - (a.leak_score || 0);
    if (sortBy === "amount") return b.current_amount - a.current_amount;
    return a.merchant_normalized.localeCompare(b.merchant_normalized);
  });

  const filterButtons: { key: FilterKey; label: string; color: string }[] = [
    { key: "all", label: "All", color: "bg-white/10 text-white" },
    { key: "cancel", label: "Cancel", color: "bg-red-500/15 text-red-400" },
    { key: "renegotiate", label: "Renegotiate", color: "bg-orange-500/15 text-orange-400" },
    { key: "downgrade", label: "Downgrade", color: "bg-yellow-500/15 text-yellow-400" },
    { key: "keep", label: "Keep", color: "bg-emerald-500/15 text-emerald-400" },
  ];

  if (subscriptions.length === 0) {
    return (
      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-12 text-center">
        <div className="text-4xl mb-3">📭</div>
        <h3 className="text-white font-medium mb-1">No Subscriptions Yet</h3>
        <p className="text-gray-400 text-sm">Upload your data or try the demo to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-1.5">
          {filterButtons.map((btn) => (
            <button
              key={btn.key}
              onClick={() => setFilterBy(btn.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filterBy === btn.key
                  ? btn.color + " border border-current/20"
                  : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
              }`}
            >
              {btn.label}
              {btn.key !== "all" && (
                <span className="ml-1 opacity-60">
                  {subscriptions.filter((s) => s.recommendation === btn.key).length}
                </span>
              )}
            </button>
          ))}
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortKey)}
          className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-300 focus:outline-none focus:ring-1 focus:ring-[#D85A30]/50"
        >
          <option value="score">Sort by Leak Score</option>
          <option value="amount">Sort by Amount</option>
          <option value="name">Sort by Name</option>
        </select>
      </div>

      {/* List */}
      <div className="space-y-2">
        {sorted.map((sub) => (
          <SubscriptionCard key={sub.id} subscription={sub} />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-8 text-gray-500 text-sm">
          No subscriptions match the selected filter.
        </div>
      )}
    </div>
  );
}
