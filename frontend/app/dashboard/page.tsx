"use client";

import { useQuery } from "@tanstack/react-query";
import { getDashboardSummary, getSubscriptions } from "@/lib/api";
import LeakScoreGauge from "@/components/LeakScoreGauge";
import CategoryPieChart from "@/components/CategoryPieChart";
import SubscriptionList from "@/components/SubscriptionList";
import Link from "next/link";
import WhatsAppSimulator from "@/components/WhatsAppSimulator";

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: getDashboardSummary,
  });

  const { data: subsData, isLoading: subsLoading } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: getSubscriptions,
  });

  const isLoading = summaryLoading || subsLoading;

  // Empty state
  if (!isLoading && (!subsData?.subscriptions || subsData.subscriptions.length === 0)) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
        <div className="text-center py-24">
          <div className="text-6xl mb-4">🔍</div>
          <h2 className="text-2xl font-bold text-white mb-3">No Data Yet</h2>
          <p className="text-gray-400 mb-8 max-w-md mx-auto">
            Upload your SMS alerts or bank statement to start detecting subscription leaks.
          </p>
          <Link
            href="/"
            className="inline-flex px-6 py-3 rounded-xl bg-gradient-to-r from-[#D85A30] to-[#e8845f] text-white font-semibold shadow-lg shadow-[#D85A30]/25 hover:shadow-[#D85A30]/40 transition-all"
          >
            Get Started →
          </Link>
        </div>
      </div>
    );
  }

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-48 bg-white/10 rounded-lg" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-white/5 rounded-xl border border-white/10" />
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="h-64 bg-white/5 rounded-xl border border-white/10" />
            <div className="h-64 bg-white/5 rounded-xl border border-white/10" />
            <div className="h-64 bg-white/5 rounded-xl border border-white/10 lg:col-span-1" />
          </div>
        </div>
      </div>
    );
  }

  const recCounts = summary?.recommendation_counts || { keep: 0, downgrade: 0, renegotiate: 0, cancel: 0 };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 animate-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {summary?.total_subscriptions || 0} active subscriptions detected
          </p>
        </div>
        <Link
          href="/"
          className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-gray-300 hover:bg-white/10 transition-all"
        >
          + Add Data
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <p className="text-xs text-gray-500 mb-1">Monthly Spend</p>
          <p className="text-xl font-bold text-white">₹{summary?.total_monthly_spend?.toLocaleString() || 0}</p>
        </div>
        <div className="rounded-xl border border-[#D85A30]/20 bg-[#D85A30]/5 p-4">
          <p className="text-xs text-gray-500 mb-1">Potential Savings</p>
          <p className="text-xl font-bold text-[#D85A30]">₹{summary?.potential_monthly_savings?.toLocaleString() || 0}<span className="text-xs font-normal text-gray-500">/mo</span></p>
        </div>
        <div className="rounded-xl border border-[#0F6E56]/20 bg-[#0F6E56]/5 p-4">
          <p className="text-xs text-gray-500 mb-1">Recovered</p>
          <p className="text-xl font-bold text-[#0F6E56]">₹{summary?.total_recovered?.toLocaleString() || 0}</p>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <p className="text-xs text-gray-500 mb-1">Action Needed</p>
          <p className="text-xl font-bold text-white">{(recCounts.cancel || 0) + (recCounts.renegotiate || 0) + (recCounts.downgrade || 0)}</p>
        </div>
      </div>

      {/* Charts + Score Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Leak Score Gauge */}
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6 flex flex-col items-center justify-center">
          <LeakScoreGauge score={summary?.average_leak_score || 0} size={220} />
          <div className="flex justify-center gap-4 mt-4">
            {Object.entries(recCounts).map(([key, count]) => {
              const colors: Record<string, string> = {
                keep: "text-emerald-400",
                downgrade: "text-yellow-400",
                renegotiate: "text-orange-400",
                cancel: "text-red-400",
              };
              return (
                <div key={key} className="text-center">
                  <p className={`text-lg font-bold ${colors[key]}`}>{count}</p>
                  <p className="text-[10px] text-gray-500 capitalize">{key}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Spending by Category</h3>
          <CategoryPieChart data={summary?.category_breakdown || []} />
        </div>

        {/* Quick Stats */}
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6 space-y-4">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Quick Insights</h3>
          {summary?.category_breakdown?.slice(0, 4).map((cat) => (
            <div key={cat.category} className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white">{cat.display_name}</p>
                <p className="text-xs text-gray-500">{cat.count} subscription{cat.count > 1 ? "s" : ""}</p>
              </div>
              <p className="text-sm font-semibold text-white">₹{cat.monthly_amount.toLocaleString()}/mo</p>
            </div>
          ))}
          <Link
            href="/growth"
            className="block w-full text-center py-3 rounded-xl bg-[#0F6E56]/10 border border-[#0F6E56]/20 text-[#0F6E56] text-sm font-medium hover:bg-[#0F6E56]/15 transition-all mt-4"
          >
            🌱 View Growth Fund →
          </Link>
        </div>
      </div>

      {/* Subscription List */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Your Subscriptions</h2>
        <SubscriptionList subscriptions={subsData?.subscriptions || []} />
      </div>
      
      {/* WhatsApp Intervention Simulator Widget */}
      {subsData?.subscriptions && subsData.subscriptions.length > 0 && (
        <WhatsAppSimulator subscriptions={subsData.subscriptions} />
      )}
    </div>
  );
}
