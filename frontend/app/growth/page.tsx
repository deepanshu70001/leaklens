"use client";

import { useQuery } from "@tanstack/react-query";
import { getGrowthSummary } from "@/lib/api";
import GrowthChart from "@/components/GrowthChart";
import Link from "next/link";

export default function GrowthPage() {
  const { data: growth, isLoading } = useQuery({
    queryKey: ["growth-summary"],
    queryFn: getGrowthSummary,
  });

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-48 bg-white/10 rounded-lg" />
          <div className="h-64 bg-white/5 rounded-xl border border-white/10" />
        </div>
      </div>
    );
  }

  const hasData = growth && growth.total_monthly_contribution > 0;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 animate-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            🌱 Growth Fund
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Watch your recovered money compound over time
          </p>
        </div>
        <Link
          href="/dashboard"
          className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-gray-300 hover:bg-white/10 transition-all"
        >
          ← Dashboard
        </Link>
      </div>

      {!hasData ? (
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-12 text-center">
          <div className="text-5xl mb-4">🌱</div>
          <h2 className="text-xl font-bold text-white mb-2">Your Growth Fund is Empty</h2>
          <p className="text-gray-400 text-sm mb-6 max-w-md mx-auto">
            Cancel or downgrade subscriptions and redirect the savings here to see your money grow.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex px-6 py-3 rounded-xl bg-gradient-to-r from-[#0F6E56] to-[#14B8A6] text-white font-semibold shadow-lg shadow-[#0F6E56]/25 hover:shadow-[#0F6E56]/40 transition-all"
          >
            Find Leaks to Fix →
          </Link>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
            <div className="rounded-xl border border-[#0F6E56]/20 bg-[#0F6E56]/5 p-5">
              <p className="text-xs text-gray-500 mb-1">Monthly Contribution</p>
              <p className="text-2xl font-bold text-[#0F6E56]">
                ₹{growth.total_monthly_contribution.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 mt-1">from {growth.actions_count} action{growth.actions_count !== 1 ? "s" : ""}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
              <p className="text-xs text-gray-500 mb-1">Assumed Return</p>
              <p className="text-2xl font-bold text-white">{growth.assumed_annual_return_pct}%</p>
              <p className="text-xs text-gray-500 mt-1">annual, compounded monthly</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
              <p className="text-xs text-gray-500 mb-1">Recovered to Date</p>
              <p className="text-2xl font-bold text-white">
                ₹{growth.total_recovered_to_date.toLocaleString()}
              </p>
            </div>
          </div>

          {/* Projections */}
          <div className="grid grid-cols-3 gap-3 mb-8">
            {growth.projections.map((proj) => (
              <div key={proj.years} className="rounded-xl border border-white/10 bg-white/[0.03] p-5 text-center">
                <p className="text-xs text-gray-500 mb-2">{proj.years} Year{proj.years > 1 ? "s" : ""}</p>
                <p className="text-xl font-bold text-white">₹{proj.projected_value.toLocaleString()}</p>
                <p className="text-xs text-[#0F6E56] mt-1">
                  +₹{proj.growth_amount.toLocaleString()} growth
                </p>
              </div>
            ))}
          </div>

          {/* Chart */}
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-6 mb-6">
            <h3 className="text-sm font-medium text-gray-400 mb-4">Projected Growth (5 Years)</h3>
            <GrowthChart data={growth.chart_data} />
          </div>

          {/* Disclaimer */}
          <div className="rounded-lg bg-white/5 border border-white/10 p-4">
            <p className="text-xs text-gray-500 leading-relaxed">
              ⚠️ {growth.disclaimer}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
