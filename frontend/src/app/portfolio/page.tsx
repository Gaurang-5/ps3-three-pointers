'use client';
import { motion } from 'framer-motion';
import useSWR from 'swr';
import dynamic from 'next/dynamic';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import GlassCard from '@/components/ui/GlassCard';
import { formatPercent, formatCurrency } from '@/lib/formatters';

const PortfolioGlobe = dynamic(() => import('@/components/three/PortfolioGlobe'), { ssr: false });
const fetcher = (url: string) => fetch(url).then(r => r.json());

const COLORS = ['#00D4AA', '#FF9F0A', '#32D74B', '#FF375F', '#8A8A8E'];

export default function PortfolioPage() {
  const { data: portfolio } = useSWR('/api/portfolio', fetcher);
  const { data: signals } = useSWR('/api/signals', fetcher);

  const latest = Array.isArray(portfolio) ? portfolio.at(-1) : null;
  const first = Array.isArray(portfolio) ? portfolio[0] : null;
  const totalValue = parseFloat(latest?.Total_Value ?? '1000000');
  const cash = parseFloat(latest?.Cash ?? '50000');

  const donutData: Array<{ name: string; value: number }> = [];
  const assets: Array<{ ticker: string; weight: number; pnl: number; signal: string }> = [];

  const getLatestSignal = (ticker: string) => {
    if (!Array.isArray(signals)) return 'HOLD';
    const sig = [...signals].reverse().find(s => s.ticker === ticker);
    return sig?.signal || 'HOLD';
  };

  if (latest) {
    ['Equity', 'Oil', 'Gold', 'Bond'].forEach(asset => {
      const shares = parseFloat(latest[`${asset}_Shares`]) || 0;
      const price = parseFloat(latest[`${asset}_Price`]) || 0;
      const initialPrice = parseFloat(first?.[`${asset}_Price`]) || price;
      const assetPnl = initialPrice > 0 ? (price - initialPrice) / initialPrice : 0;
      const val = shares * price;

      if (val > 10) {
        donutData.push({ name: asset, value: val });
        assets.push({ ticker: asset, weight: val / totalValue, pnl: assetPnl, signal: getLatestSignal(asset) });
      }
    });
  }

  // Always add Cash
  if (cash > 10) {
    donutData.push({ name: 'Cash', value: cash });
    assets.push({ ticker: 'Cash', weight: cash / totalValue, pnl: 0, signal: 'N/A' });
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="p-6 space-y-6 max-w-7xl"
    >
      <h1 className="text-white">Portfolio</h1>

      <div className="grid grid-cols-2 gap-6">
        {/* Left: Globe */}
        <GlassCard className="p-4">
          <h2 className="text-white mb-2">Asset Globe</h2>
          <p className="text-xs mb-4" style={{ color: 'var(--text-secondary)' }}>
            Drag to rotate · Node size = allocation weight
          </p>
          <PortfolioGlobe assets={assets} />
        </GlassCard>

        {/* Right: Donut + Table */}
        <div className="space-y-4">
          <GlassCard className="p-4">
            <h2 className="text-white mb-2">Allocation</h2>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={donutData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} dataKey="value">
                  {donutData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v) => formatCurrency(Number(v ?? 0))}
                  contentStyle={{ background: '#111', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12 }}
                  labelStyle={{ color: '#8A8A8E' }}
                />
                <Legend wrapperStyle={{ fontSize: 11, color: '#8A8A8E' }} />
              </PieChart>
            </ResponsiveContainer>
          </GlassCard>

          <GlassCard className="overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                  {['Ticker', 'Weight', 'P&L', 'Signal'].map(h => (
                    <th key={h} className="text-left px-4 py-3 label">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {assets.map(a => (
                  <tr key={a.ticker} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td className="px-4 py-3 number text-white">{a.ticker}</td>
                    <td className="px-4 py-3 number">{(a.weight * 100).toFixed(1)}%</td>
                    <td className={`px-4 py-3 number ${a.pnl >= 0 ? 'text-[var(--gain)]' : 'text-[var(--loss)]'}`}>
                      {formatPercent(a.pnl)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-medium"
                        style={{
                          background: a.signal === 'BUY' ? 'rgba(52,199,89,0.12)' : a.signal === 'SELL' ? 'rgba(255,59,48,0.12)' : 'var(--accent-dim)',
                          color: a.signal === 'BUY' ? 'var(--gain)' : a.signal === 'SELL' ? 'var(--loss)' : 'var(--accent)'
                        }}>
                        {a.signal}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </GlassCard>
        </div>
      </div>
    </motion.div>
  );
}
