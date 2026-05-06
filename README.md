# Hedge Fund Risk Modeling & Semi-Automated Trading System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![Three.js](https://img.shields.io/badge/Three.js-r158-orange?logo=three.js)
![License](https://img.shields.io/badge/License-MIT-green)
![Issues](https://img.shields.io/badge/Issues-20%2F20%20Resolved-brightgreen)

**Code2Create Challenge — Round 3 | Team: ps3-three-pointers**

*A production-grade, modular, risk-aware semi-automated trading simulation system with a premium Next.js dashboard.*

</div>

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Quick Start](#quick-start)
5. [Configuration](#configuration)
6. [Pipeline Stages](#pipeline-stages)
7. [Risk Framework](#risk-framework)
8. [Dashboard](#dashboard)
9. [Output Files](#output-files)
10. [Edge Cases Handled](#edge-cases-handled)
11. [Performance Results](#performance-results)
12. [Project Structure](#project-structure)

---

## Overview

This system simulates a **hedge fund's full trading lifecycle** — from raw CSV ingestion to interactive dashboard visualisation — across a multi-asset universe. Every design decision is **risk-first**: no trade executes without passing VaR, drawdown, and capital adequacy checks. Every decision is **explainable**: a structured audit trail logs the exact factor values that drove each signal.

### Key Design Principles

| Principle | Implementation |
|---|---|
| **Risk-First** | VaR gate, drawdown circuit-breaker, volatility-scaled sizing |
| **Explainability** | JSON audit log with factor breakdown per signal |
| **No Forward-Looking Bias** | All features use `min_periods` rolling; signals computed on past data only |
| **Realistic Friction** | Commission (10 bps) + slippage (5 bps) on every trade |
| **Graceful Degradation** | Malformed data skipped; capital shortfalls logged, not crashed |

---

## Architecture

```
Raw CSV Data (Equity / Macro / Multi-Asset / Oil)
        │
        ▼
┌─────────────────────────┐
│  Stage 1 & 2            │  core/data.py
│  DataPreprocessor       │  • Schema validation
│  Missing Data + Outlier │  • ffill/bfill (max 5 days)
│  Handling               │  • 3σ outlier capping
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Stage 3 & 4            │  core/features.py
│  FeatureEngineer        │  • Log Returns, Rolling Vol (21d)
│  Volatility + Momentum  │  • Momentum (10d, 30d)
│  + Macro Integration    │  • RSI (14d), Volume Z-Score
│                         │  • Macro Score (normalized)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Stage 5                │  core/portfolio.py
│  PortfolioManager       │  • Cash & position tracking
│  State Management       │  • Max position limit (20%)
│                         │  • Min cash reserve (5%)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Stage 6 & 7            │  core/risk.py
│  RiskModeler            │  • Historical VaR (95%, 252d)
│  Signal Engine          │  • Max Drawdown tracking
│                         │  • Portfolio volatility (21d)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Stage 8                │  core/trading.py
│  SignalEngine           │  • Multi-factor composite score
│                         │  • RSI + Trend + Macro + Vol
│                         │  • Score ∈ [-1.0, +1.0]
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Stage 9 & 11           │  core/portfolio.py + trading.py
│  Trade Execution        │  • Slippage simulation
│  + Audit Logging        │  • Commission deduction
│                         │  • JSONL audit trail
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Stage 10               │  core/metrics.py
│  MetricsCalculator      │  • Sharpe, Sortino
│                         │  • Alpha, Beta (OLS)
│                         │  • Cumulative & Ann. Returns
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Stage 12               │  core/dashboard.py + frontend/
│  DashboardExporter      │  • 5 CSV/JSON output files
│  Next.js Dashboard      │  • Recharts + Three.js charts
│                         │  • 5 interactive pages
└─────────────────────────┘
```

---

## Features

### Backend Pipeline
- ✅ **Multi-asset data ingestion** with schema validation and error recovery
- ✅ **Outlier detection**: 3σ capping with per-column logging
- ✅ **Feature engineering**: RSI(14), SMA(50/200), Rolling Vol(21d), Short/Long Momentum, Volume Z-Score, Macro Score
- ✅ **Multi-factor signal engine**: Composite score [-1, +1] with threshold gating (±0.3)
- ✅ **Risk-aware position sizing**: Volatility-targeted sizing with hard 20% cap
- ✅ **Transaction costs**: 10 bps commission + 5 bps slippage on every trade
- ✅ **Circuit breakers**: VaR breach → log + skip; Drawdown > 20% → force to cash
- ✅ **JSONL audit logging**: `trade_log.jsonl`, `error_log.jsonl`, `summary_log.json`
- ✅ **5 dashboard output files** for visualisation layer

### Frontend Dashboard (Next.js 14)
- ✅ **Dashboard** — Portfolio area chart, RiskSphere 3D, 4 KPI cards
- ✅ **Portfolio** — PortfolioGlobe 3D, donut allocation, positions table
- ✅ **Risk** — 3D Candlestick chart, SVG arc gauges, risk events log
- ✅ **Signals** — CSS grid heatmap, trade log with BUY/SELL coloring
- ✅ **Performance** — 6 metric cards, Portfolio vs Benchmark, rolling charts

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend Setup

```bash
# 1. Install Python dependencies
pip install pandas numpy pyyaml matplotlib

# 2. Run the full simulation pipeline
python main.py

# Output files generated:
# - output/portfolio_timeseries.csv
# - output/signal_heatmap.csv
# - output/asset_allocations.csv
# - output/metrics_summary.json
# - logs/trade_log.jsonl
# - logs/error_log.jsonl
# - logs/summary_log.json
```

### Frontend Setup

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Copy backend output to public/data (run once after backend)
cp ../output/* public/data/
cp ../logs/*.jsonl public/data/

# 4. Start the development server
npm run dev

# Dashboard available at: http://localhost:3000
```

---

## Configuration

All parameters are centralized in `config.yaml` — no code changes needed for tuning:

```yaml
portfolio:
  initial_capital: 1_000_000     # Starting capital ($)
  max_position_pct: 0.20         # Max 20% in any single asset
  risk_tolerance_var: 0.03       # Max daily VaR: 3% of portfolio
  max_drawdown_limit: 0.20       # Emergency rebalance at 20% drawdown
  min_cash_pct: 0.05             # Always keep 5% cash reserve

trading:
  commission_rate: 0.001         # 0.10% commission per trade
  base_slippage: 0.0005          # 0.05% base slippage
  rebalance_frequency: 21        # Rebalance every ~21 trading days
  drift_threshold: 0.15          # Rebalance if allocation drifts >15%

signals:
  buy_threshold: 0.30            # Composite score > 0.3 → BUY
  sell_threshold: -0.30          # Composite score < -0.3 → SELL
  rsi_oversold: 35               # RSI below this → oversold (buy signal)
  rsi_overbought: 65             # RSI above this → overbought (sell signal)

risk:
  var_confidence: 0.95           # VaR confidence level
  var_lookback_days: 252         # 1-year lookback for historical VaR
  volatility_window: 21          # Rolling window for portfolio volatility
  momentum_short_window: 10      # Short momentum window (days)
  momentum_long_window: 30       # Long momentum window (days)

metrics:
  risk_free_rate: 0.05           # Annual risk-free rate (5%)
  benchmark_ticker: "Equity"     # Benchmark for Alpha/Beta calculation
```

---

## Pipeline Stages

### Stage 1–2: Data Ingestion & Preprocessing (`core/data.py`)

- Loads 4 datasets: Equity, Macro, Multi-Asset, Oil
- Validates required `Date` column on each dataset
- Forward-fills missing prices (up to 5 consecutive days), backward-fills start gaps
- Caps outliers using 3σ z-score clipping per column
- Merges all datasets on the Equity timeline (left join — no market dates dropped)

### Stage 3–4: Feature Engineering (`core/features.py`)

| Feature | Window | Formula |
|---|---|---|
| Log Return | Daily | `ln(P_t / P_{t-1})` |
| Rolling Volatility | 21-day | `std(log_returns) × √252` |
| Short Momentum | 10-day | `(P_t - P_{t-10}) / P_{t-10}` |
| Long Momentum | 30-day | `(P_t - P_{t-30}) / P_{t-30}` |
| RSI | 14-day | Wilder's smoothed RSI |
| SMA Cross | 50 / 200-day | Simple moving averages |
| Volume Z-Score | 20-day | `(Vol - μ) / σ` |
| Macro Score | Monthly → daily | Min-max normalized, forward-filled |

### Stage 5: Portfolio State Management (`core/portfolio.py`)

- Tracks: `cash`, `shares`, `total_value`, `daily_history`
- Enforces max position limit (20% of total portfolio)
- Handles `InsufficientCapitalError` — scales down or logs rejection, never crashes

### Stage 6–7: Risk Modeling (`core/risk.py`)

- **Historical VaR**: `−percentile(returns[-252:], 5)` — non-parametric, no distribution assumption
- **Max Drawdown**: Running peak-to-trough tracking
- **Portfolio Volatility**: 21-day rolling annualized standard deviation

### Stage 8: Signal Engine (`core/trading.py`)

Multi-factor composite score ∈ [-1.0, +1.0]:

| Factor | BUY condition | SELL condition | Weight |
|---|---|---|---|
| RSI | < 35 (oversold) | > 65 (overbought) | 0.40 |
| SMA Cross | Price > SMA50 > SMA200 | Price < SMA50 < SMA200 | 0.30 |
| Macro Score | > 0.6 | < 0.4 | 0.10 |
| Volatility filter | Vol < 3% daily | Vol > 3% daily → HOLD | Override |

### Stage 9: Execution Simulation (`core/portfolio.py`)

- **Slippage**: BUY at `price × (1 + slippage)`, SELL at `price × (1 - slippage)`
- **Commission**: `0.1%` of gross trade value, deducted from cash
- **Capital check**: If insufficient, trade is scaled down and logged

### Stage 10: Performance Metrics (`core/metrics.py`)

```
Cumulative Return  = (V_final - V_0) / V_0
Annualized Return  = (1 + cum_ret)^(252 / N) - 1
Sharpe Ratio       = mean(excess_returns) / std(excess_returns) × √252
Sortino Ratio      = mean(excess_returns) / std(negative_returns) × √252
Beta               = Cov(R_portfolio, R_benchmark) / Var(R_benchmark)
Alpha              = mean(R_portfolio) - Beta × mean(R_benchmark)  [annualized]
Max Drawdown       = max((peak - trough) / peak)
```

### Stage 11: Explainability Logging (`core/trading.py`)

Every signal and trade is logged to `logs/trade_log.jsonl` with full factor breakdown:

```json
{
  "timestamp": "2026-05-06T06:30:52",
  "date": "2024-03-15",
  "event_type": "SIGNAL",
  "ticker": "Equity",
  "signal_value": 0.4,
  "reason": "RSI Oversold (32.1) | Bullish Trend",
  "factors": {
    "rsi": 32.1,
    "macro_score": 0.62,
    "volatility": 0.018,
    "composite_score": 0.4
  }
}
```

Risk events, rejected trades, and data errors are separately logged to `logs/error_log.jsonl`.

---

## Risk Framework

### Circuit Breakers

| Trigger | Action |
|---|---|
| Daily VaR > 3% of portfolio | Log `RISK_BREACH`, skip all BUY orders |
| Portfolio drawdown > 20% | Force signal to 0 (hold cash), log event |
| Cash < 5% of initial capital | Block new BUY orders |
| Asset price invalid / NaN | Skip trade, log `DATA_ERROR` |
| InsufficientCapitalError | Scale down trade, log rejection |

### Position Sizing Formula

```
target_weight = 1 / rolling_vol_21d          # Inverse-volatility weighting
position_value = target_weight × available_capital
position_value = min(position_value, 0.20 × total_portfolio)  # Cap at 20%
```

---

## Dashboard

The interactive dashboard is a **Next.js 14** application with **Three.js** 3D visualisations and **Recharts** 2D charts.

### Pages

| Page | Key Components |
|---|---|
| `/dashboard` | Portfolio area chart · RiskSphere 3D · VaR/Drawdown/Sharpe KPIs |
| `/portfolio` | PortfolioGlobe 3D · Donut allocation · Positions table |
| `/risk` | CandlestickChart3D · SVG arc gauges · Risk events log |
| `/signals` | Signal heatmap (score-intensity CSS grid) · Trade log table |
| `/performance` | 6 metric cards · Portfolio vs Benchmark · Rolling metrics |

### 3D Components (Three.js, no react-three-fiber)

- **RiskSphere** — Icosahedron wireframe; color shifts green→amber→red with VaR level
- **PortfolioGlobe** — Fibonacci-distributed asset nodes; drag to rotate
- **CandlestickChart3D** — BoxGeometry candles; scroll to zoom; shadow mapping enabled
- **MarketParticles** — 3,000-particle ambient field; additive blending; opacity 0.18

---

## Output Files

| File | Contents |
|---|---|
| `output/portfolio_timeseries.csv` | Daily: Date, Total_Value, Cash, Equity_Shares, Equity_Price |
| `output/signal_heatmap.csv` | Daily: Date, Ticker, Signal, Composite_Score |
| `output/asset_allocations.csv` | Daily: Date, Ticker, Weight |
| `output/metrics_summary.json` | Final: Sharpe, Sortino, Alpha, Beta, Max Drawdown, Total Return |
| `output/portfolio_value.png` | Matplotlib line chart of portfolio value |
| `output/final_allocation.png` | Matplotlib bar chart of final allocation |
| `logs/trade_log.jsonl` | Append-only: all signals and executed trades |
| `logs/error_log.jsonl` | Append-only: rejected trades, risk breaches, data errors |
| `logs/summary_log.json` | Aggregate counts of all event types |

---

## Edge Cases Handled

| Scenario | Handling |
|---|---|
| Missing price for N days | `ffill` (cap 5 days) → `bfill` → drop row if still NaN |
| Flash crash (|return| > 3σ) | Value clipped to 3σ bounds; logged as `DATA_ERROR` |
| All assets breach VaR simultaneously | All BUY signals blocked; logged as `RISK_BREACH` |
| Portfolio drawdown > 20% | Signal forced to 0.0; emergency cash hold |
| Cash < 5% of capital | BUY orders rejected; logged as `TRADE_REJECTED` |
| Invalid/NaN asset price | Trade skipped; warning logged |
| Insufficient capital | Trade scaled to affordable size; `InsufficientCapitalError` logged |
| Malformed CSV column | `DataIngestionError` raised with specific column name |

---

## Performance Results

Running `python main.py` on the provided datasets produces:

| Metric | Value |
|---|---|
| Total Return | see `output/metrics_summary.json` |
| Sharpe Ratio | see `output/metrics_summary.json` |
| Sortino Ratio | see `output/metrics_summary.json` |
| Max Drawdown | see `output/metrics_summary.json` |
| Alpha | see `output/metrics_summary.json` |
| Beta | see `output/metrics_summary.json` |

> **Reproducibility**: All results are fully reproducible. Run `python main.py` to regenerate all metrics, logs, and output files.

---

## Project Structure

```
ps3-three-pointers/
│
├── main.py                      # Orchestrator: runs the full pipeline
├── config.yaml                  # Single source of truth for all parameters
│
├── core/
│   ├── __init__.py
│   ├── data.py                  # Stage 1–2: Ingestion + Preprocessing
│   ├── features.py              # Stage 3–4: Feature Engineering
│   ├── portfolio.py             # Stage 5 + 9: State Management + Execution
│   ├── risk.py                  # Stage 6–7: VaR, Drawdown, Volatility
│   ├── trading.py               # Stage 8 + 11: Signals + Audit Logging
│   ├── metrics.py               # Stage 10: Performance Metrics
│   └── dashboard.py             # Stage 12: CSV/PNG export
│
├── data/raw/                    # Input datasets
│   ├── equity_dataset.csv
│   ├── macro_dataset.csv
│   ├── multi_asset_dataset.csv
│   └── oil_dataset.csv
│
├── output/                      # Generated by main.py
│   ├── portfolio_timeseries.csv
│   ├── signal_heatmap.csv
│   ├── asset_allocations.csv
│   ├── metrics_summary.json
│   ├── portfolio_value.png
│   └── final_allocation.png
│
├── logs/                        # Audit trail
│   ├── trade_log.jsonl
│   ├── error_log.jsonl
│   └── summary_log.json
│
├── frontend/                    # Next.js 14 dashboard
│   ├── src/
│   │   ├── app/                 # App Router pages + API routes
│   │   ├── components/
│   │   │   ├── three/           # RiskSphere, PortfolioGlobe, CandlestickChart3D, MarketParticles
│   │   │   └── ui/              # GlassCard, MetricCard, Sidebar, TopBar
│   │   └── lib/                 # formatters.ts, store.ts
│   └── public/data/             # Backend output files served to frontend
│
├── README.md
├── ARCHITECTURE.md
├── STRATEGY.md
├── RISK_FRAMEWORK.md
├── ISSUES.md
├── master_prompt.md
└── frontend_master_prompt.md
```

---

## Documentation

| Document | Contents |
|---|---|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Module diagram, data flow, design rationale |
| [STRATEGY.md](./STRATEGY.md) | Signal logic, factor weights, strategy explanation |
| [RISK_FRAMEWORK.md](./RISK_FRAMEWORK.md) | VaR methodology, position sizing, circuit breakers |

---

*Code2Create Challenge — Round 3 | Hedge Fund Risk Modeling & Semi-Automated Trading System*
