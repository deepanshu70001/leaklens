"use client";

import { useState } from "react";
import { ghostCancelSubscription } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";

export default function WhatsAppSimulator({ subscriptions }: { subscriptions: any[] }) {
  const [isOpen, setIsOpen] = useState(false);
  const [chatStep, setChatStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const queryClient = useQueryClient();

  // Find a high risk subscription to demo
  const demoSub = subscriptions?.find(s => s.leak_score > 60 && s.status === "active") || subscriptions?.[0];

  const handleSend = async () => {
    if (inputValue.trim().toLowerCase() === "cancel" && demoSub) {
      setLoading(true);
      setInputValue("");
      
      // Simulate WhatsApp typing delay
      setTimeout(async () => {
        try {
          await ghostCancelSubscription(demoSub._id || demoSub.id);
          setChatStep(2); // Success step
          queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
          queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
        } catch (err) {
          setChatStep(3); // Error step
        } finally {
          setLoading(false);
        }
      }, 1500);
      setChatStep(1); // User sent message
    }
  };

  if (!demoSub) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Floating Action Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-4 py-3 bg-[#25D366] hover:bg-[#1DA851] text-white rounded-full shadow-lg shadow-[#25D366]/30 transition-transform hover:scale-105 animate-bounce"
        >
          <span className="text-xl">💬</span>
          <span className="font-semibold text-sm">Simulate WhatsApp Alert</span>
          <span className="absolute -top-1 -right-1 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-4 w-4 bg-red-500 text-[10px] items-center justify-center font-bold">1</span>
          </span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="w-80 bg-[#0b141a] rounded-xl shadow-2xl border border-white/10 overflow-hidden flex flex-col animate-in slide-in-from-bottom-5">
          {/* Header */}
          <div className="bg-[#202c33] px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#D85A30] to-[#e8845f] flex items-center justify-center text-xs shadow-lg">
                LL
              </div>
              <div>
                <h4 className="text-white text-sm font-semibold">LeakLens Bot</h4>
                <p className="text-[#8696a0] text-xs">bot verified</p>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-[#8696a0] hover:text-white">
              ✕
            </button>
          </div>

          {/* Chat Body */}
          <div className="flex-1 p-4 space-y-4 h-64 overflow-y-auto bg-[#0b141a]" style={{ backgroundImage: "url('https://static.whatsapp.net/rsrc.php/v3/yl/r/r_QZ352iV3M.png')", opacity: 0.9 }}>
            
            <div className="flex justify-start">
              <div className="bg-[#202c33] text-[#e9edef] text-sm p-2.5 rounded-lg rounded-tl-none max-w-[85%] shadow-sm">
                Hey! LeakLens noticed you paid <b>₹{demoSub.current_amount}</b> for <b>{demoSub.merchant_normalized}</b> but haven't used it much recently.
                <br/><br/>
                Reply <b>CANCEL</b> and I will email their support to close the account.
                <span className="block text-right text-[#8696a0] text-[10px] mt-1">10:42 AM</span>
              </div>
            </div>

            {chatStep >= 1 && (
              <div className="flex justify-end animate-in fade-in">
                <div className="bg-[#005c4b] text-[#e9edef] text-sm p-2.5 rounded-lg rounded-tr-none max-w-[85%] shadow-sm">
                  CANCEL
                  <span className="block text-right text-[#8696a0] text-[10px] mt-1">10:43 AM ✓✓</span>
                </div>
              </div>
            )}

            {loading && (
              <div className="flex justify-start animate-in fade-in">
                <div className="bg-[#202c33] text-[#e9edef] text-sm p-2.5 rounded-lg rounded-tl-none shadow-sm flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-[#8696a0] rounded-full animate-bounce" />
                  <div className="w-1.5 h-1.5 bg-[#8696a0] rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                  <div className="w-1.5 h-1.5 bg-[#8696a0] rounded-full animate-bounce" style={{ animationDelay: "0.4s" }} />
                </div>
              </div>
            )}

            {chatStep === 2 && (
              <div className="flex justify-start animate-in fade-in">
                <div className="bg-[#202c33] text-[#e9edef] text-sm p-2.5 rounded-lg rounded-tl-none max-w-[85%] shadow-sm">
                  ✅ Done! I've dispatched the ghost cancellation email to {demoSub.merchant_normalized} Support. You just saved ₹{demoSub.current_amount}/mo!
                  <span className="block text-right text-[#8696a0] text-[10px] mt-1">10:43 AM</span>
                </div>
              </div>
            )}
            
            {chatStep === 3 && (
              <div className="flex justify-start animate-in fade-in">
                <div className="bg-[#202c33] text-[#e9edef] text-sm p-2.5 rounded-lg rounded-tl-none max-w-[85%] shadow-sm text-red-400">
                  ❌ Oops, failed to send cancellation email.
                  <span className="block text-right text-[#8696a0] text-[10px] mt-1">10:43 AM</span>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="bg-[#202c33] p-3 flex items-center gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Type CANCEL"
              disabled={chatStep > 0}
              className="flex-1 bg-[#2a3942] text-sm text-[#e9edef] rounded-lg px-4 py-2 focus:outline-none placeholder-[#8696a0] disabled:opacity-50"
            />
            <button 
              onClick={handleSend}
              disabled={chatStep > 0 || !inputValue.trim()}
              className="w-10 h-10 rounded-full bg-[#00a884] flex items-center justify-center text-white disabled:opacity-50 hover:bg-[#008f6f] transition-colors"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
