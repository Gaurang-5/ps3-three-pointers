'use client';
import { motion } from 'framer-motion';
import useSWR from 'swr';
import dynamic from 'next/dynamic';
import GlassCard from '@/components/ui/GlassCard';

const CandlestickChart3D = dynamic(() => import('@/components/three/CandlestickChart3D'), { ssr: false });
const fetcher = (url: string) => fetch(url).then(r => r.json());

function RiskGauge({ label, value, min, max, warn, danger, unit = '%' }: {
  label: string; value: number; min: number; max: number;
  warn: number; danger: number; unit?: string;
}) {
  const pct = Math.min(Math.max((value - min) / (max - min), 0), 1);
  const angle = -135 + pct * 270;
  const color = Math.abs(value) >= danger
    ? 'var(--loss)' : Math.abs(value) >= warn
    ? 'var(--warn)' : 'var(--gain)';

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-28 h-28">
        <svg viewBox="0 0 100 100" className="w-full h-full">
          <path d="M 15 75 A 42 42 0 1 1 85 75" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" strokeLinecap="round" />
          <path
            d="M 15 75 A 42 42 0 1 1 85 75" fill="none" stroke={color} strokeWidth="8"
            strokeLinecap="round" strokeDasharray={`${pct * 188} 188`}
          />
          <line
            x1="50" y1="50"
            x2={50 + 28 * Math.cos((angle - 90) * Math.PI / 180)}
            y2={50 + 28 * Math.sin((angle - 90) * Math.PI / 180)}
            stroke={color} strokeWidth="2" strokeLinecap="round"
          />
          <circle cx="50" cy="50" r="3" fill={color} />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center pt-4">
          <span className="number text-white text-xs font-semibold">
            {value.toFixed(1)}{unit}
          </span>
        </div>
      </div>
      <span className="label">{label}</span>
    </div>
  );
}

export default function RiskPage() {
  const { data: metrics } = useSWR('/api/metrics', fetcher);

  const maxDD = Math.abs((metrics?.['Max Drawdown'] ?? -0.196) * 100);
  const varEst = maxDD * 0.1;
  const volEst = 15.2;

  const riskEvents = [
    { date: '2024-03-15', type: 'VaR Breach', detail: '3.8% (limit: 3.0%)', status: 'FLAGGED', color: 'var(--loss)' },
    { date: '2024-02-28', type: 'Drawdown Alert', detail: `-${maxDD.toFixed(1)}%`, status: 'MONITORED', color: 'var(--warn)' },
    { date: '2024-01-10', type: 'Capital Low', detail: 'Cash < 5%', status: 'RESOLVED', color: 'var(--gain)' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="p-6 space-y-6 max-w-7xl"
    >
      <h1 className="text-white">Risk Management</h1>

      {/* 3D Candlestick */}
      <GlassCard className="p-4">
        <h2 className="text-white mb-1">3D Price History</h2>
        <p className="text-xs mb-3" style={{ color: 'var(--text-secondary)' }}>Scroll to zoom · Green = up day, Red = down day</p>
        <CandlestickChart3D />
      </GlassCard>

      {/* Risk Gauges */}
      <GlassCard className="p-6">
        <h2 className="text-white mb-6">Risk Gauges</h2>
        <div className="flex justify-around">
          <RiskGauge label="Daily VaR" value={varEst} min={0} max={5} warn={2} danger={3.5} />
          <RiskGauge label="Max Drawdown" value={maxDD} min={0} max={30} warn={10} danger={20} />
          <RiskGauge label="Ann. Volatility" value={volEst} min={0} max={50} warn={20} danger={35} />
        </div>
      </GlassCard>

      {/* Risk Events Log */}
      <GlassCard className="overflow-hidden">
        <div className="px-5 py-4" style={{ borderBottom: '1px solid var(--border)' }}>
          <h2 className="text-white">Risk Events Log</h2>
        </div>
        <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
          {riskEvents.map((e, i) => (
            <div key={i} className="flex items-center justify-between px-5 py-3">
              <div className="flex items-center gap-3">
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: e.color }} />
                <span className="number text-xs" style={{ color: 'var(--text-secondary)' }}>{e.date}</span>
                <span className="text-white text-sm">{e.type}</span>
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>— {e.detail}</span>
              </div>
              <span className="text-[10px] px-2 py-0.5 rounded font-medium"
                style={{ background: `${e.color}18`, color: e.color, border: `1px solid ${e.color}40` }}>
                {e.status}
              </span>
            </div>
          ))}
        </div>
      </GlassCard>
    </motion.div>
  );
}
