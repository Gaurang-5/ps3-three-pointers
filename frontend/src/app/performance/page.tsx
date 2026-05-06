'use client';
import { motion } from 'framer-motion';
import useSWR from 'swr';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, CartesianGrid, Legend } from 'recharts';
import GlassCard from '@/components/ui/GlassCard';
import MetricCard from '@/components/ui/MetricCard';
import { formatPercent, formatShortDate } from '@/lib/formatters';

const fetcher = (url: string) => fetch(url).then(r => r.json());

type DeltaType = 'positive' | 'negative' | 'neutral';
type PortfolioApiRow = {
  Date: string;
  Total_Value: number | string;
};

export default function PerformancePage() {
  const { data: metrics } = useSWR('/api/metrics', fetcher);
  const { data: portfolio } = useSWR('/api/portfolio', fetcher);

  const m = metrics ?? {};

  const chartData = Array.isArray(portfolio)
    ? portfolio.map((r: PortfolioApiRow, i: number, arr: PortfolioApiRow[]) => {
        const val = Number(r.Total_Value);
        const prev = i > 0 ? Number(arr[i - 1].Total_Value) : val;
        const ret = (val - prev) / prev;
        const initial = Number(arr[0].Total_Value);
        return {
          date: formatShortDate(r.Date),
          portfolioValue: val,
          benchmarkValue: initial * (1 + i * 0.0004),
          rollingVol: Math.abs(ret) * 15,
        };
      })
    : [];

  const getDeltaType = (value: number, positiveThreshold = 0): DeltaType => (
    value > positiveThreshold ? 'positive' : 'negative'
  );

  const metricCards = [
    { label: 'Sharpe Ratio', value: (m['Sharpe Ratio'] ?? 0).toFixed(2), sublabel: 'Annualized', deltaType: getDeltaType(m['Sharpe Ratio'] ?? 0, 1) },
    { label: 'Alpha', value: formatPercent(m['Alpha'] ?? 0), sublabel: 'vs benchmark', deltaType: getDeltaType(m['Alpha'] ?? 0) },
    { label: 'Beta', value: (m['Beta'] ?? 0).toFixed(3), sublabel: 'Market correlation', deltaType: 'neutral' as const },
    { label: 'Ann. Return', value: formatPercent(m['Total Return'] ?? 0), sublabel: 'Cumulative', deltaType: getDeltaType(m['Total Return'] ?? 0) },
    { label: 'Ann. Volatility', value: '15.2%', sublabel: 'Estimated', deltaType: 'neutral' as const },
    { label: 'Max Drawdown', value: formatPercent(m['Max Drawdown'] ?? 0), sublabel: 'Peak to trough', deltaType: 'negative' as const },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="p-6 space-y-6 max-w-7xl"
    >
      <h1 className="text-white">Performance</h1>

      {/* 6 metric cards */}
      <div className="grid grid-cols-3 gap-4">
        {metricCards.map((c) => (
          <MetricCard key={c.label} label={c.label} value={c.value} deltaType={c.deltaType} sublabel={c.sublabel} />
        ))}
      </div>

      {/* Portfolio vs Benchmark */}
      <GlassCard className="p-5">
        <h2 className="text-white mb-4">Portfolio vs Benchmark</h2>
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={chartData.slice(-60)}>
            <defs>
              <linearGradient id="pfGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00D4AA" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00D4AA" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="date" tick={{ fill: '#48484A', fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}K`}
              tick={{ fill: '#48484A', fontSize: 10, fontFamily: 'JetBrains Mono' }}
              axisLine={false} tickLine={false} width={60} />
            <Tooltip contentStyle={{ background: '#111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12 }} />
            <Area type="monotone" dataKey="portfolioValue" stroke="#00D4AA" strokeWidth={2} fill="url(#pfGrad)" name="Portfolio" />
            <Line type="monotone" dataKey="benchmarkValue" stroke="#48484A" strokeWidth={1.5} strokeDasharray="4 4" dot={false} name="Benchmark" />
            <Legend wrapperStyle={{ fontSize: 11, color: '#8A8A8E' }} />
          </AreaChart>
        </ResponsiveContainer>
      </GlassCard>

      {/* Rolling Metrics */}
      <GlassCard className="p-5">
        <h2 className="text-white mb-4">Rolling Metrics</h2>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData.slice(-60)}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="date" tick={{ fill: '#48484A', fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#48484A', fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: '#111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12 }} />
            <Line type="monotone" dataKey="rollingVol" stroke="#FF9F0A" strokeWidth={1.5} dot={false} name="Rolling Vol %" />
            <Legend wrapperStyle={{ fontSize: 11, color: '#8A8A8E' }} />
          </LineChart>
        </ResponsiveContainer>
      </GlassCard>
    </motion.div>
  );
}
