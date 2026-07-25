"use client";

import UploadPanel from "@/components/UploadPanel";

export default function HomePage() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col">
      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        {/* Glowing orb background effect */}
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-[#D85A30]/5 rounded-full blur-[120px] pointer-events-none" />

        <div className="relative text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-gray-400 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-[#0F6E56] animate-pulse" />
            Privacy-first • No bank API required • SMS-powered
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight tracking-tight mb-5">
            Find Your
            <span className="gradient-text"> Money Leaks</span>
            <br />
            <span className="text-3xl sm:text-4xl lg:text-5xl text-gray-300">
              Then Watch Them Grow
            </span>
          </h1>

          <p className="text-gray-400 text-base sm:text-lg max-w-xl mx-auto leading-relaxed mb-4">
            LeakLens scans your SMS alerts to detect hidden subscriptions, flag silent price hikes,
            and redirect your recovered money into a simulated growth fund.
          </p>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-2 mt-6 mb-10">
            {[
              { icon: "📱", text: "Works from SMS alone" },
              { icon: "🔒", text: "PII never leaves your server" },
              { icon: "📈", text: "See your money grow" },
              { icon: "🎯", text: "AI-powered insights" },
            ].map((pill) => (
              <span
                key={pill.text}
                className="px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.06] text-xs text-gray-400"
              >
                {pill.icon} {pill.text}
              </span>
            ))}
          </div>
        </div>

        {/* Upload Panel */}
        <UploadPanel />

        {/* How it works */}
        <div className="mt-20 max-w-4xl mx-auto w-full">
          <h2 className="text-center text-sm font-medium text-gray-500 uppercase tracking-wider mb-8">
            How It Works
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              {
                step: "01",
                title: "Paste or Upload",
                desc: "Share SMS alerts or upload a bank statement. No account linking needed.",
                icon: "📋",
              },
              {
                step: "02",
                title: "Detect & Score",
                desc: "We find recurring charges, flag price hikes, and score each subscription.",
                icon: "🔍",
              },
              {
                step: "03",
                title: "Act & Grow",
                desc: "Cancel leaks and redirect savings into your simulated growth portfolio.",
                icon: "🌱",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="rounded-xl border border-white/10 bg-white/[0.02] p-6 text-center hover:border-white/20 transition-all"
              >
                <div className="text-3xl mb-3">{item.icon}</div>
                <div className="text-[10px] text-[#D85A30] font-semibold tracking-widest mb-1.5">
                  STEP {item.step}
                </div>
                <h3 className="text-white font-medium text-sm mb-1.5">{item.title}</h3>
                <p className="text-gray-500 text-xs leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-6 px-4 text-center">
        <p className="text-gray-600 text-xs">
          LeakLens — Built for financial inclusion. Your data stays private by design.
        </p>
      </footer>
    </div>
  );
}
