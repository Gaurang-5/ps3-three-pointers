'use client';
import { motion } from 'framer-motion';
import useSWR from 'swr';
import { useState } from 'react';
import GlassCard from '@/components/ui/GlassCard';

const fetcher = (url: string) => fetch(url).then(r => r.json());

type SignalEvent = {
  date: string;
  ticker: string;
  signal: 'BUY' | 'SELL' | 'HOLD' | string;
  composite_score?: number | string;
};

type TradeEvent = {
  event_type: string;
  date: string;
  ticker: string;
  action: 'BUY' | 'SELL' | string;
  shares?: number | string;
  price?: number | string;
  costs?: {
    commission?: number | string;
    slippage?: number | string;
  };
};

function SignalBadge({ signal }: { signal: string }) {
  const color = signal === 'BUY' ? 'var(--gain)' : signal === 'SELL' ? 'var(--loss)' : 'var(--text-tertiary)';
  const bg = signal === 'BUY' ? 'rgba(52,199,89,0.12)' : signal === 'SELL' ? 'rgba(255,59,48,0.12)' : 'rgba(72,72,74,0.2)';
  return (
    <span className="text-[10px] px-2 py-0.5 rounded font-semibold"
      style={{ color, background: bg, border: `1px solid ${color}40` }}>
      {signal}
    </span>
  );
}

export default function SignalsPage() {
  const { data: signals } = useSWR('/api/signals', fetcher, { refreshInterval: 30000 });
  const { data: trades } = useSWR('/api/trades', fetcher, { refreshInterval: 30000 });
  const [filter, setFilter] = useState<'ALL' | 'BUY' | 'SELL' | 'HOLD'>('ALL');

  const filteredSignals = Array.isArray(signals)
    ? (signals as SignalEvent[]).filter((s) => filter === 'ALL' || s.signal === filter)
    : [];

  const filteredTrades = Array.isArray(trades)
    ? (trades as TradeEvent[]).filter((t) => {
        if (t.event_type !== 'TRADE_EXECUTED') return false;
        return filter === 'ALL' || t.action === filter;
      })
    : [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="p-6 space-y-6 max-w-7xl"
    >
      <div className="flex items-center justify-between">
        <h1 className="text-white">Signals</h1>
        <div className="flex gap-1">
          {(['ALL', 'BUY', 'SELL', 'HOLD'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className="px-3 py-1 rounded-lg text-xs transition-all duration-150"
              style={{
                background: filter === f ? 'var(--accent-dim)' : 'transparent',
                color: filter === f ? 'var(--accent)' : 'var(--text-secondary)',
                border: `1px solid ${filter === f ? 'var(--accent)' : 'transparent'}`,
              }}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Signal Heatmap */}
      <GlassCard className="p-5">
        <h2 className="text-white mb-4">Signal Heatmap</h2>
        <div className="overflow-x-auto">
          <div className="flex flex-col gap-1 min-w-max">
            {['Equity'].map(ticker => (
              <div key={ticker} className="flex items-center gap-1">
                <span className="number text-xs w-14 flex-shrink-0" style={{ color: 'var(--text-secondary)' }}>{ticker}</span>
                {filteredSignals.slice(0, 30).map((s, i: number) => {
                  const score = Math.abs(Number(s.composite_score ?? 0));
                  const bg = s.signal === 'BUY'
                    ? `rgba(52,199,89,${0.2 + score * 0.8})`
                    : s.signal === 'SELL'
                    ? `rgba(255,59,48,${0.2 + score * 0.8})`
                    : 'rgba(72,72,74,0.3)';
                  return (
                    <div key={i} title={`${s.date} | ${s.signal} | Score: ${Number(s.composite_score ?? 0).toFixed(2)}`}
                      style={{ width: 14, height: 14, borderRadius: 2, background: bg, cursor: 'help' }} />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* Trade Log */}
      <GlassCard className="overflow-hidden">
        <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border)' }}>
          <h2 className="text-white">Trade Log</h2>
          <span className="label">{filteredTrades.length} entries</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                {['Date', 'Ticker', 'Action', 'Shares', 'Price', 'Commission', 'Slippage'].map(h => (
                  <th key={h} className="text-left px-4 py-3 label">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredTrades.slice(0, 20).map((t, i: number) => (
                <tr key={i} style={{
                  borderBottom: '1px solid var(--border)',
                  borderLeft: `2px solid ${t.action === 'BUY' ? 'var(--gain)' : t.action === 'SELL' ? 'var(--loss)' : 'transparent'}`,
                }}>
                  <td className="px-4 py-2.5 number" style={{ color: 'var(--text-secondary)' }}>{t.date}</td>
                  <td className="px-4 py-2.5 number text-white">{t.ticker}</td>
                  <td className="px-4 py-2.5"><SignalBadge signal={t.action} /></td>
                  <td className="px-4 py-2.5 number">{Number(t.shares ?? 0).toFixed(0)}</td>
                  <td className="px-4 py-2.5 number">${Number(t.price ?? 0).toFixed(2)}</td>
                  <td className="px-4 py-2.5 number" style={{ color: 'var(--loss)' }}>
                    ${Number(t.costs?.commission ?? 0).toFixed(2)}
                  </td>
                  <td className="px-4 py-2.5 number" style={{ color: 'var(--warn)' }}>
                    ${Number(t.costs?.slippage ?? 0).toFixed(2)}
                  </td>
                </tr>
              ))}
              {filteredTrades.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center" style={{ color: 'var(--text-tertiary)' }}>No trades found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </motion.div>
  );
}
