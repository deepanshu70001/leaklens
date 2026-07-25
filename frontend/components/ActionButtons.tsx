"use client";

import { useState } from "react";
import { takeAction } from "@/lib/api";

interface ActionButtonsProps {
  subscriptionId: string;
  currentRecommendation: string | null;
  currentStatus: string;
  onActionTaken?: (result: any) => void;
}

export default function ActionButtons({
  subscriptionId,
  currentRecommendation,
  currentStatus,
  onActionTaken,
}: ActionButtonsProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const [showGrowthToggle, setShowGrowthToggle] = useState(false);
  const [redirectToGrowth, setRedirectToGrowth] = useState(true);
  const [pendingAction, setPendingAction] = useState<string | null>(null);

  const handleAction = async (action: string) => {
    if (action === "cancel" || action === "downgrade") {
      setPendingAction(action);
      setShowGrowthToggle(true);
      return;
    }
    await executeAction(action, false);
  };

  const executeAction = async (action: string, redirect: boolean) => {
    setLoading(action);
    setShowGrowthToggle(false);
    try {
      const result = await takeAction(subscriptionId, action, redirect);
      onActionTaken?.(result);
    } catch (err) {
      console.error("Action failed:", err);
    } finally {
      setLoading(null);
      setPendingAction(null);
    }
  };

  if (currentStatus === "canceled" || currentStatus === "downgraded") {
    return (
      <div className="rounded-lg bg-white/5 border border-white/10 p-4 text-center">
        <p className="text-gray-400 text-sm">
          ✅ You&apos;ve already {currentStatus} this subscription.
        </p>
      </div>
    );
  }

  const actions = [
    {
      key: "cancel",
      label: "Cancel",
      icon: "✕",
      style: "bg-red-500/15 text-red-400 border-red-500/20 hover:bg-red-500/25",
    },
    {
      key: "downgrade",
      label: "Downgrade",
      icon: "↓",
      style: "bg-yellow-500/15 text-yellow-400 border-yellow-500/20 hover:bg-yellow-500/25",
    },
    {
      key: "renegotiate",
      label: "Renegotiate",
      icon: "💬",
      style: "bg-orange-500/15 text-orange-400 border-orange-500/20 hover:bg-orange-500/25",
    },
    {
      key: "keep",
      label: "Keep",
      icon: "✓",
      style: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/25",
    },
  ];

  // Put recommended action first
  const orderedActions = currentRecommendation
    ? [
        ...actions.filter((a) => a.key === currentRecommendation),
        ...actions.filter((a) => a.key !== currentRecommendation),
      ]
    : actions;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        {orderedActions.map((action) => (
          <button
            key={action.key}
            onClick={() => handleAction(action.key)}
            disabled={loading !== null}
            className={`py-3 px-4 rounded-xl border text-sm font-medium transition-all duration-200 flex items-center justify-center gap-2 ${action.style} ${
              action.key === currentRecommendation ? "ring-1 ring-current" : ""
            } disabled:opacity-50`}
          >
            {loading === action.key ? (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <span>{action.icon}</span>
            )}
            {action.label}
            {action.key === currentRecommendation && (
              <span className="text-[10px] opacity-60 ml-1">Recommended</span>
            )}
          </button>
        ))}
      </div>

      {/* Growth redirect toggle */}
      {showGrowthToggle && pendingAction && (
        <div className="rounded-xl border border-[#0F6E56]/30 bg-[#0F6E56]/10 p-4 space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-start gap-3">
            <span className="text-2xl">🌱</span>
            <div>
              <p className="text-white text-sm font-medium">Redirect savings to growth?</p>
              <p className="text-gray-400 text-xs mt-0.5">
                The recovered money will be added to your simulated micro-savings portfolio.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => executeAction(pendingAction, true)}
              className="flex-1 py-2.5 rounded-lg bg-[#0F6E56] text-white text-sm font-medium hover:bg-[#0F6E56]/80 transition-all"
            >
              Yes, grow my money 🌱
            </button>
            <button
              onClick={() => executeAction(pendingAction, false)}
              className="flex-1 py-2.5 rounded-lg bg-white/10 text-gray-300 text-sm font-medium hover:bg-white/15 transition-all"
            >
              No, just {pendingAction}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
