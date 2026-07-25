"use client";

import { useState, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getTransactions,
  deleteTransaction,
  clearAllData,
  ingestSMS,
} from "@/lib/api";
import { TransactionRecord } from "@/lib/types";

interface TransactionManagerProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function TransactionManager({
  isOpen,
  onClose,
}: TransactionManagerProps) {
  const queryClient = useQueryClient();
  const [activeView, setActiveView] = useState<"list" | "add">("list");
  const [smsText, setSmsText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [confirmClear, setConfirmClear] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const {
    data: txnData,
    isLoading: txnLoading,
    refetch: refetchTxns,
  } = useQuery({
    queryKey: ["transactions"],
    queryFn: getTransactions,
    enabled: isOpen,
  });

  const refreshAll = useCallback(() => {
    refetchTxns();
    queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
    queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
  }, [refetchTxns, queryClient]);

  const handleAddSMS = async () => {
    if (!smsText.trim()) {
      setError("Please paste some SMS messages");
      return;
    }
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const result = await ingestSMS(smsText);
      setSuccess(
        `Added ${result.transactions_parsed} transaction(s). ${result.subscriptions_detected} subscription(s) detected.`
      );
      setSmsText("");
      setActiveView("list");
      refreshAll();
    } catch (err: any) {
      setError(err.message || "Failed to parse SMS text");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTxn = async (id: string) => {
    setDeletingId(id);
    setError("");
    setSuccess("");
    try {
      const result = await deleteTransaction(id);
      setSuccess(result.message);
      refreshAll();
    } catch (err: any) {
      setError(err.message || "Failed to delete transaction");
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      await clearAllData();
      setSuccess("All data cleared successfully.");
      setConfirmClear(false);
      refreshAll();
    } catch (err: any) {
      setError(err.message || "Failed to clear data");
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "—";
    try {
      return new Date(dateStr).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  const sourceIcon = (type: string) => {
    switch (type) {
      case "sms":
        return "💬";
      case "statement":
        return "📄";
      case "screenshot":
        return "📸";
      default:
        return "📋";
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Drawer Panel */}
      <div className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-lg bg-[#0F172A] border-l border-white/10 shadow-2xl flex flex-col animate-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[#D85A30] to-[#e8845f] flex items-center justify-center text-white text-lg">
              📊
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">
                Manage Transactions
              </h2>
              <p className="text-xs text-gray-500">
                {txnData?.total ?? 0} transaction(s) stored
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-gray-400 hover:text-white transition-all"
          >
            ✕
          </button>
        </div>

        {/* View Toggle */}
        <div className="flex px-6 pt-4 gap-2">
          <button
            onClick={() => {
              setActiveView("list");
              setError("");
              setSuccess("");
            }}
            className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeView === "list"
                ? "bg-white/10 text-white"
                : "text-gray-400 hover:text-white hover:bg-white/5"
            }`}
          >
            📋 All Transactions
          </button>
          <button
            onClick={() => {
              setActiveView("add");
              setError("");
              setSuccess("");
            }}
            className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeView === "add"
                ? "bg-gradient-to-r from-[#D85A30] to-[#e8845f] text-white shadow-lg shadow-[#D85A30]/25"
                : "text-gray-400 hover:text-white hover:bg-white/5"
            }`}
          >
            ➕ Add More Data
          </button>
        </div>

        {/* Alerts */}
        <div className="px-6 pt-3">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-2">
              ⚠️ {error}
            </div>
          )}
          {success && (
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm mb-2">
              ✅ {success}
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {activeView === "list" && (
            <div className="space-y-2">
              {txnLoading ? (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="h-16 bg-white/5 rounded-xl animate-pulse"
                    />
                  ))}
                </div>
              ) : !txnData?.transactions?.length ? (
                <div className="text-center py-16">
                  <div className="text-4xl mb-3">📭</div>
                  <p className="text-gray-400 text-sm">
                    No transactions yet. Add some SMS data to get started.
                  </p>
                  <button
                    onClick={() => setActiveView("add")}
                    className="mt-4 px-4 py-2 rounded-lg bg-[#D85A30]/10 border border-[#D85A30]/20 text-[#D85A30] text-sm font-medium hover:bg-[#D85A30]/20 transition-all"
                  >
                    ➕ Add Data
                  </button>
                </div>
              ) : (
                txnData.transactions.map((txn: TransactionRecord) => (
                  <div
                    key={txn.id}
                    className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-white/10 transition-all group"
                  >
                    <div className="h-10 w-10 rounded-lg bg-white/5 flex items-center justify-center text-lg flex-shrink-0">
                      {sourceIcon(txn.source_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white font-medium truncate">
                        {txn.merchant_normalized || txn.merchant_raw || "Unknown"}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDate(txn.date)} · {txn.source_type}
                      </p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-sm font-semibold text-white">
                        ₹{txn.amount.toLocaleString()}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDeleteTxn(txn.id)}
                      disabled={deletingId === txn.id}
                      className="h-8 w-8 rounded-lg bg-red-500/0 hover:bg-red-500/10 flex items-center justify-center text-gray-500 hover:text-red-400 transition-all opacity-0 group-hover:opacity-100 disabled:opacity-50 flex-shrink-0"
                      title="Delete transaction"
                    >
                      {deletingId === txn.id ? (
                        <svg
                          className="animate-spin h-4 w-4"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                      ) : (
                        "🗑"
                      )}
                    </button>
                  </div>
                ))
              )}
            </div>
          )}

          {activeView === "add" && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-white mb-1">
                  Paste SMS Alerts
                </h3>
                <p className="text-xs text-gray-500">
                  New messages will be added to your existing data without
                  replacing anything.
                </p>
              </div>
              <textarea
                value={smsText}
                onChange={(e) => setSmsText(e.target.value)}
                placeholder={`Paste your SMS alerts here, one per line. Example:\n\nYour a/c XX4521 debited INR 199.00 on 15-Jan-2024 for NETFLIX.COM. Avl bal: INR 45,230.50\nYour a/c XX4521 debited INR 119.00 on 03-Jan-2024 for SPOTIFY INDIA. Avl bal: INR 46,100.00`}
                className="w-full h-44 rounded-xl bg-white/5 border border-white/10 p-4 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#D85A30]/50 focus:border-[#D85A30]/50 resize-none transition-all"
              />
              <button
                onClick={handleAddSMS}
                disabled={loading || !smsText.trim()}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-[#D85A30] to-[#e8845f] text-white font-semibold shadow-lg shadow-[#D85A30]/25 hover:shadow-[#D85A30]/40 transition-all duration-300 disabled:opacity-50"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Analyzing...
                  </span>
                ) : (
                  "➕ Add Transactions"
                )}
              </button>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-white/10">
          {!confirmClear ? (
            <button
              onClick={() => setConfirmClear(true)}
              disabled={!txnData?.transactions?.length}
              className="w-full py-2.5 rounded-lg bg-white/5 border border-white/10 text-gray-400 text-sm font-medium hover:text-red-400 hover:border-red-500/20 hover:bg-red-500/5 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
            >
              🗑 Clear All Data
            </button>
          ) : (
            <div className="space-y-2">
              <p className="text-xs text-red-400 text-center">
                ⚠️ This will permanently delete ALL your transactions and
                subscriptions.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setConfirmClear(false)}
                  className="flex-1 py-2.5 rounded-lg bg-white/5 border border-white/10 text-gray-400 text-sm font-medium hover:bg-white/10 transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleClearAll}
                  disabled={loading}
                  className="flex-1 py-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium hover:bg-red-500/20 transition-all disabled:opacity-50"
                >
                  {loading ? "Clearing..." : "Yes, Clear Everything"}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
