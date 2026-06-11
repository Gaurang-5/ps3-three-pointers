"use client";
import { motion } from "framer-motion";
import { useState } from "react";
import useSWR from "swr";
import dynamic from "next/dynamic";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import MetricCard from "@/components/ui/MetricCard";
import GlassCard from "@/components/ui/GlassCard";
import {
  formatCurrency,
  formatPercent,
  formatShortDate,
  formatDate,
} from "@/lib/formatters";
import { TrendingUp, Activity, Wallet, AlertTriangle } from "lucide-react";

const RiskSphere = dynamic(() => import("@/components/three/RiskSphere"), {
  ssr: false,
});
const MarketParticles = dynamic(
  () => import("@/components/three/MarketParticles"),
  { ssr: false },
);

const fetcher = (url: string) => fetch(url).then((r) => r.json());

const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.3, ease: "easeOut" as const },
};

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-card p-3 text-xs" style={{ minWidth: 160 }}>
      <div className="label mb-1">{label ? formatDate(label) : ""}</div>
      <div className="number text-white">
        {formatCurrency(payload[0]?.value)}
      </div>
    </div>
  );
};

export default function DashboardPage() {
  const { data: metrics } = useSWR("/api/metrics", fetcher, {
    refreshInterval: 30000,
  });
  const { data: portfolio } = useSWR("/api/portfolio", fetcher, {
    refreshInterval: 30000,
  });
  const { data: logs } = useSWR("/api/logs", fetcher, {
    refreshInterval: 30000,
  });

  const [range, setRange] = useState<"1W" | "1M" | "3M" | "ALL">("ALL");

  const chartData = (() => {
    if (!portfolio || !Array.isArray(portfolio)) return [];
    const days =
      range === "1W"
        ? 7
        : range === "1M"
          ? 21
          : range === "3M"
            ? 63
            : portfolio.length;
    return portfolio.slice(-days).map((r: Record<string, string | number>) => ({
      date: r.Date as string,
      value: parseFloat(r.Total_Value as string),
    }));
  })();

  const latestValue = chartData.at(-1)?.value ?? 1000000;
  const firstValue = chartData[0]?.value ?? 1000000;
  const totalReturn = (latestValue - firstValue) / firstValue;
  const varValue = metrics
    ? Math.abs(metrics["Max Drawdown"] ?? 0.02) * 0.1
    : 0.023;

  const ranges: Array<"1W" | "1M" | "3M" | "ALL"> = ["1W", "1M", "3M", "ALL"];

  return (
    <>
      <MarketParticles />
      <motion.div {...pageTransition} className="p-6 space-y-6 w-full">
        {/* Hero Row */}
        <div className="flex items-start justify-between gap-6">
          {/* Left: portfolio value */}
          <div className="flex flex-col gap-2">
            <span className="label">Total Portfolio Value</span>
            <span className="number text-5xl font-semibold text-white">
              {formatCurrency(latestValue)}
            </span>
            <span
              className={`text-sm font-medium number ${totalReturn >= 0 ? "text-[var(--gain)]" : "text-[var(--loss)]"}`}
            >
              {totalReturn >= 0 ? "+" : ""}
              {formatCurrency(latestValue - firstValue)} (
              {formatPercent(totalReturn)})
            </span>
            <div className="flex gap-6 mt-3">
              {metrics && (
                <>
                  <div>
                    <div className="label">Sharpe</div>
                    <div className="number text-white text-lg">
                      {(metrics["Sharpe Ratio"] ?? 0).toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="label">VaR (est.)</div>
                    <div className="number text-[var(--warn)] text-lg">
                      {(varValue * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div className="label">Max DD</div>
                    <div className="number text-[var(--loss)] text-lg">
                      {formatPercent(metrics["Max Drawdown"] ?? 0)}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Right: Risk Sphere */}
          <div className="flex flex-col items-center gap-2">
            <RiskSphere varValue={varValue} />
            <span className="label">Risk Level</span>
          </div>
        </div>

        {/* Portfolio Value Chart */}
        <GlassCard className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-white font-medium text-base">
              Portfolio Value Over Time
            </h2>
            <div className="flex gap-1">
              {ranges.map((r) => (
                <button
                  key={r}
                  onClick={() => setRange(r)}
                  className="px-3 py-1 rounded-lg text-xs transition-all duration-150"
                  style={{
                    background:
                      range === r ? "var(--accent-dim)" : "transparent",
                    color:
                      range === r ? "var(--accent)" : "var(--text-secondary)",
                    border: `1px solid ${range === r ? "var(--accent)" : "transparent"}`,
                  }}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="portfolioGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00D4AA" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00D4AA" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255,255,255,0.04)"
              />
              <XAxis
                dataKey="date"
                tickFormatter={(v) => formatShortDate(v)}
                tick={{ fill: "#48484A", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
                tick={{
                  fill: "#48484A",
                  fontSize: 10,
                  fontFamily: "JetBrains Mono",
                }}
                axisLine={false}
                tickLine={false}
                width={60}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#00D4AA"
                strokeWidth={2}
                fill="url(#portfolioGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </GlassCard>

        {/* Bottom 4 Mini Cards */}
        <div className="grid grid-cols-4 gap-4">
          <GlassCard className="p-4 flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "var(--accent-dim)" }}
            >
              <Wallet size={16} style={{ color: "var(--accent)" }} />
            </div>
            <div>
              <div className="label">Active Positions</div>
              <div className="number text-white text-xl">
                {(() => {
                  const last = portfolio?.at(-1) || {};
                  return (
                    Object.keys(last).filter(
                      (k) => k.endsWith("_Shares") && parseFloat(last[k]) > 0,
                    ).length || 0
                  );
                })()}
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(52,199,89,0.12)" }}
            >
              <Activity size={16} style={{ color: "var(--gain)" }} />
            </div>
            <div>
              <div className="label">Total Trades Logged</div>
              <div className="number text-white text-xl">
                {logs?.trades_executed
                  ? logs.trades_executed.toLocaleString()
                  : "..."}
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(52,199,89,0.12)" }}
            >
              <TrendingUp size={16} style={{ color: "var(--gain)" }} />
            </div>
            <div>
              <div className="label">Top Alloc</div>
              <div className="number text-[var(--gain)] text-lg">
                {(() => {
                  const last = portfolio?.at(-1) || {};
                  let top = "Cash";
                  let maxVal = parseFloat(last.Cash) || 0;
                  ["Equity", "Oil", "Gold", "Bond"].forEach((asset) => {
                    const val =
                      (parseFloat(last[`${asset}_Shares`]) || 0) *
                      (parseFloat(last[`${asset}_Price`]) || 0);
                    if (val > maxVal) {
                      maxVal = val;
                      top = asset;
                    }
                  });
                  return top;
                })()}
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-4 flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(255,159,10,0.12)" }}
            >
              <AlertTriangle size={16} style={{ color: "var(--warn)" }} />
            </div>
            <div>
              <div className="label">Risk Breaches</div>
              <div className="text-[var(--warn)] text-sm font-medium flex items-center gap-1">
                <span
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ background: "var(--warn)" }}
                />
                {logs?.risk_events ? logs.risk_events.toLocaleString() : "0"}
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Metrics Row */}
        {metrics && (
          <div className="grid grid-cols-3 gap-4">
            <MetricCard
              label="Sharpe Ratio"
              value={(metrics["Sharpe Ratio"] ?? 0).toFixed(2)}
              deltaType={metrics["Sharpe Ratio"] > 1 ? "positive" : "negative"}
              sublabel="Annualized risk-adjusted return"
            />
            <MetricCard
              label="Sortino Ratio"
              value={(metrics["Sortino Ratio"] ?? 0).toFixed(2)}
              deltaType={metrics["Sortino Ratio"] > 1 ? "positive" : "negative"}
              sublabel="Downside risk adjusted"
            />
            <MetricCard
              label="Max Drawdown"
              value={formatPercent(metrics["Max Drawdown"] ?? 0)}
              deltaType="negative"
              sublabel="Peak to trough"
            />
          </div>
        )}
      </motion.div>
    </>
  );
}
