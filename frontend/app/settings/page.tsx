"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ingestDemo } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleResetDemo = async (datasetId: string) => {
    setLoading(true);
    setMessage("");
    try {
      const result = await ingestDemo(datasetId);
      setMessage(result.message);
    } catch (err: any) {
      setMessage(err.message || "Failed to reset data");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 animate-in">
      <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>

      {/* Data Sources */}
      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6 mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">Data Sources</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center gap-3">
              <span className="text-lg">💬</span>
              <div>
                <p className="text-sm text-white">SMS Alerts</p>
                <p className="text-xs text-gray-500">Paste bank transaction SMS messages</p>
              </div>
            </div>
            <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">Available</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center gap-3">
              <span className="text-lg">📄</span>
              <div>
                <p className="text-sm text-white">Bank Statements</p>
                <p className="text-xs text-gray-500">CSV and PDF uploads supported</p>
              </div>
            </div>
            <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">Available</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center gap-3">
              <span className="text-lg">📧</span>
              <div>
                <p className="text-sm text-white">Email Receipts</p>
                <p className="text-xs text-gray-500">Coming in future release</p>
              </div>
            </div>
            <span className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded">Coming Soon</span>
          </div>
        </div>
      </div>

      {/* Demo Data */}
      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6 mb-6">
        <h2 className="text-lg font-semibold text-white mb-2">Demo Data</h2>
        <p className="text-sm text-gray-400 mb-4">Load sample datasets to explore LeakLens features.</p>
        <div className="space-y-2">
          {[
            { id: "sample_sms_1", label: "Sample SMS 1", desc: "7 merchants, 2 price hikes, category redundancy" },
            { id: "sample_sms_2", label: "Sample SMS 2", desc: "Different bank formats, PayPal prefix patterns" },
            { id: "sample_statement_1", label: "CSV Statement", desc: "Bank statement with debit/credit columns" },
          ].map((dataset) => (
            <button
              key={dataset.id}
              onClick={() => handleResetDemo(dataset.id)}
              disabled={loading}
              className="w-full flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all disabled:opacity-50 text-left"
            >
              <div>
                <p className="text-sm text-white">{dataset.label}</p>
                <p className="text-xs text-gray-500">{dataset.desc}</p>
              </div>
              <span className="text-xs text-[#D85A30]">Load →</span>
            </button>
          ))}
        </div>
        {message && (
          <div className="mt-3 p-3 rounded-lg bg-[#0F6E56]/10 border border-[#0F6E56]/20 text-[#0F6E56] text-sm">
            ✅ {message}
          </div>
        )}
      </div>

      {/* Privacy Note */}
      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6">
        <h2 className="text-lg font-semibold text-white mb-2">Privacy & Security</h2>
        <div className="space-y-3 text-sm text-gray-400">
          <p>🔒 <strong className="text-gray-300">PII Redaction:</strong> Card/account numbers and phone numbers are masked before any data leaves your server.</p>
          <p>🚫 <strong className="text-gray-300">No Bank API:</strong> LeakLens works from SMS text alone — no account linking required.</p>
          <p>📦 <strong className="text-gray-300">Data Minimization:</strong> Only merchant name, amount, and date are stored. Raw SMS text is truncated after parsing.</p>
          <p>🔐 <strong className="text-gray-300">Production Roadmap:</strong> Raw statement parsing would run inside an AWS Nitro Enclave or similar TEE, with only tokenized data leaving the enclave boundary.</p>
        </div>
      </div>
    </div>
  );
}
