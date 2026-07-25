"use client";

import { useState } from "react";
import { triggerLiveWhatsAppAlert } from "@/lib/api";

export default function WhatsAppTrigger({ subscriptions }: { subscriptions: any[] }) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "sent" | "error">("idle");

  // Find a high risk subscription to demo
  const demoSub = subscriptions?.find(s => s.leak_score > 60 && s.status === "active") || subscriptions?.[0];

  const handleSendLiveAlert = async () => {
    if (!demoSub) return;
    setLoading(true);
    setStatus("idle");
    try {
      await triggerLiveWhatsAppAlert(demoSub.id || demoSub._id);
      setStatus("sent");
      // Reset status after a few seconds
      setTimeout(() => setStatus("idle"), 8000);
    } catch (err) {
      console.error(err);
      setStatus("error");
      setTimeout(() => setStatus("idle"), 5000);
    } finally {
      setLoading(false);
    }
  };

  if (!demoSub) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      
      {/* Toast Notification */}
      {status === "sent" && (
        <div className="px-4 py-3 bg-[#0F6E56] text-white text-sm font-medium rounded-xl shadow-xl shadow-[#0F6E56]/25 animate-in slide-in-from-bottom-5 fade-in flex items-center gap-2">
          <span>✅</span>
          Live WhatsApp alert dispatched to your phone!
        </div>
      )}

      {status === "error" && (
        <div className="px-4 py-3 bg-red-500/90 text-white text-sm font-medium rounded-xl shadow-xl shadow-red-500/25 animate-in slide-in-from-bottom-5 fade-in flex items-center gap-2 border border-red-500/50">
          <span>❌</span>
          Failed to dispatch. Ensure Twilio keys are set in backend/.env
        </div>
      )}

      {/* Floating Action Button */}
      <button
        onClick={handleSendLiveAlert}
        disabled={loading || status === "sent"}
        className="flex items-center gap-2 px-5 py-3.5 bg-[#25D366] hover:bg-[#1DA851] text-white rounded-full shadow-lg shadow-[#25D366]/30 transition-transform hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 disabled:cursor-not-allowed group"
      >
        <span className="text-xl group-hover:animate-pulse">💬</span>
        <span className="font-semibold text-sm">
          {loading ? "Dispatching..." : status === "sent" ? "Check your Phone!" : "Send Live WhatsApp Alert"}
        </span>
        {!loading && status !== "sent" && (
          <span className="absolute -top-1 -right-1 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-4 w-4 bg-red-500 text-[10px] items-center justify-center font-bold">1</span>
          </span>
        )}
      </button>
    </div>
  );
}
