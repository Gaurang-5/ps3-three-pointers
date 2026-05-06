import { create } from 'zustand';

export interface MetricsSummary {
  'Total Return': number;
  'Sharpe Ratio': number;
  'Sortino Ratio': number;
  'Max Drawdown': number;
  Alpha: number;
  Beta: number;
}

export interface PortfolioRow {
  Date: string;
  Total_Value: number;
  Cash: number;
  Equity_Shares: number;
  Equity_Price: number;
}

export interface SignalRow {
  date: string;
  ticker: string;
  signal: string;
  composite_score: number;
}

interface AppState {
  metrics: MetricsSummary | null;
  portfolio: PortfolioRow[];
  signals: SignalRow[];
  setMetrics: (m: MetricsSummary) => void;
  setPortfolio: (p: PortfolioRow[]) => void;
  setSignals: (s: SignalRow[]) => void;
}

export const useAppStore = create<AppState>((set) => ({
  metrics: null,
  portfolio: [],
  signals: [],
  setMetrics: (metrics) => set({ metrics }),
  setPortfolio: (portfolio) => set({ portfolio }),
  setSignals: (signals) => set({ signals }),
}));
