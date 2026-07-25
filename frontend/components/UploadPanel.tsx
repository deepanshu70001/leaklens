"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ingestSMS, ingestStatement, ingestDemo } from "@/lib/api";

export default function UploadPanel() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"sms" | "upload" | "demo">("demo");
  const [smsText, setSmsText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  const handleDemo = async () => {
    setLoading(true);
    setError("");
    try {
      await ingestDemo("sample_sms_1");
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to load demo data");
    } finally {
      setLoading(false);
    }
  };

  const handleSMS = async () => {
    if (!smsText.trim()) {
      setError("Please paste some SMS text");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await ingestSMS(smsText);
      if (result.subscriptions_detected > 0) {
        router.push("/dashboard");
      } else {
        setError("No recurring subscriptions detected. Try pasting more transaction messages.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to parse SMS text");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    setLoading(true);
    setError("");
    try {
      const result = await ingestStatement(file);
      if (result.subscriptions_detected > 0) {
        router.push("/dashboard");
      } else {
        setError("No recurring subscriptions detected in this file.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to parse file");
    } finally {
      setLoading(false);
    }
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  }, []);

  const tabs = [
    { id: "demo" as const, label: "Try Demo", icon: "✨" },
    { id: "sms" as const, label: "Paste SMS", icon: "💬" },
    { id: "upload" as const, label: "Upload File", icon: "📄" },
  ];

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Tab Selector */}
      <div className="flex rounded-xl bg-white/5 p-1.5 mb-6 border border-white/10">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id); setError(""); }}
            className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeTab === tab.id
                ? "bg-gradient-to-r from-[#D85A30] to-[#e8845f] text-white shadow-lg shadow-[#D85A30]/25"
                : "text-gray-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <span className="mr-1.5">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-sm">
        {activeTab === "demo" && (
          <div className="text-center space-y-6">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-[#D85A30]/20 to-[#e8845f]/10 border border-[#D85A30]/20">
              <span className="text-3xl">🔍</span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">See LeakLens in Action</h3>
              <p className="text-gray-400 text-sm leading-relaxed max-w-md mx-auto">
                Load a sample dataset with realistic SMS transaction data containing multiple subscriptions,
                price hikes, and redundant services. No signup required.
              </p>
            </div>
            <button
              onClick={handleDemo}
              disabled={loading}
              className="w-full py-4 rounded-xl bg-gradient-to-r from-[#D85A30] to-[#e8845f] text-white font-semibold text-base shadow-lg shadow-[#D85A30]/25 hover:shadow-[#D85A30]/40 transition-all duration-300 hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Analyzing Transactions...
                </span>
              ) : (
                "🚀 Try Demo Data — No Setup Needed"
              )}
            </button>
          </div>
        )}

        {activeTab === "sms" && (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">Paste SMS Alerts</h3>
              <p className="text-gray-400 text-sm">
                Paste your bank transaction SMS messages. We'll detect subscriptions automatically.
              </p>
            </div>
            <textarea
              value={smsText}
              onChange={(e) => setSmsText(e.target.value)}
              placeholder={`Paste your SMS alerts here, one per line. Example:\n\nYour a/c XX4521 debited INR 199.00 on 15-Jan-2024 for NETFLIX.COM. Avl bal: INR 45,230.50\nYour a/c XX4521 debited INR 119.00 on 03-Jan-2024 for SPOTIFY INDIA. Avl bal: INR 46,100.00`}
              className="w-full h-48 rounded-xl bg-white/5 border border-white/10 p-4 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#D85A30]/50 focus:border-[#D85A30]/50 resize-none transition-all"
            />
            <button
              onClick={handleSMS}
              disabled={loading || !smsText.trim()}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-[#D85A30] to-[#e8845f] text-white font-semibold shadow-lg shadow-[#D85A30]/25 hover:shadow-[#D85A30]/40 transition-all duration-300 disabled:opacity-50"
            >
              {loading ? "Analyzing..." : "🔍 Analyze SMS Messages"}
            </button>
          </div>
        )}

        {activeTab === "upload" && (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">Upload Statement</h3>
              <p className="text-gray-400 text-sm">Upload a CSV or PDF bank statement (max 5MB).</p>
            </div>
            <div
              onDrop={onDrop}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 ${
                dragOver
                  ? "border-[#D85A30] bg-[#D85A30]/10"
                  : "border-white/15 hover:border-white/30 hover:bg-white/[0.02]"
              }`}
            >
              <div className="text-4xl mb-3">📁</div>
              <p className="text-gray-300 font-medium mb-1">Drag & drop your statement here</p>
              <p className="text-gray-500 text-sm mb-4">or click to browse</p>
              <input
                type="file"
                accept=".csv,.pdf"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileUpload(file);
                }}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="inline-block px-6 py-2.5 rounded-lg bg-white/10 text-white text-sm font-medium cursor-pointer hover:bg-white/15 transition-all"
              >
                Browse Files
              </label>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            ⚠️ {error}
          </div>
        )}
      </div>
    </div>
  );
}
