# MASTER PROMPT — Hedge Fund Risk Modeling & Semi-Automated Trading System
## Code2Create Challenge — Round 3

---

> **How to use this prompt:** Feed this entire document to your AI agent (e.g. Claude via API) as a system prompt, or break it into stage-by-stage calls. Every stage references the issues explicitly so nothing is missed. Work sequentially — each stage builds on the previous one.

---

## ROLE & OBJECTIVE

You are an expert quantitative finance engineer building a **production-grade, semi-automated trading and risk management system** for a simulated hedge fund.

Your goal is to design and implement a complete pipeline that:
1. Ingests and preprocesses multi-asset market data
2. Engineers features for signal generation
3. Models portfolio risk (VaR, drawdown, volatility)
4. Generates explainable buy/sell/hold trading signals
5. Executes risk-aware position sizing and portfolio rebalancing
6. Simulates realistic market friction (costs, slippage)
7. Computes all key performance metrics (Sharpe, Alpha, Beta)
8. Outputs a dashboard-ready visualization layer

**Primary constraint:** Every design decision must be **risk-aware**. Simplicity is preferred over unnecessary complexity. Strategies must be explainable — no black boxes without audit trails.

---

## SYSTEM ARCHITECTURE OVERVIEW

Build the system as **modular Python components** with clean interfaces between them. The high-level data flow is:

```
Raw Data (CSV/API)
    │
    ▼
[Stage 1] Data Ingestion Pipeline
    │
    ▼
[Stage 2] Preprocessing (Missing Data + Outlier Handling)
    │
    ▼
[Stage 3] Feature Engineering (Volatility + Momentum)
    │
    ▼
[Stage 4] Optional: Macro & Sentiment Integration
    │
    ▼
[Stage 5] Portfolio State Management
    │
    ▼
[Stage 6] Risk Modeling (VaR, Max Drawdown, Volatility)
    │
    ▼
[Stage 7] Signal Generation Engine
    │
    ▼
[Stage 8] Position Sizing + Rebalancing
    │
    ▼
[Stage 9] Trade Execution Simulation (Costs + Slippage)
    │
    ▼
[Stage 10] Metrics Calculation (Sharpe, Alpha, Beta)
    │
    ▼
[Stage 11] Logging + Explainability
    │
    ▼
[Stage 12] Dashboard Output
```

---

## STAGE 1 — Data Ingestion Pipeline
*Resolves: Issue 1, Issue 16*

**Task:** Build a robust data ingestion module that loads historical market data (price, volume, volatility) from raw CSV datasets or APIs.

**Requirements:**
- Load multi-asset data concurrently using `concurrent.futures` or `asyncio` to avoid memory bottlenecks
- Support the following columns at minimum: `date`, `ticker`, `open`, `high`, `low`, `close`, `volume`
- Parse and validate timestamps; enforce a consistent datetime index (UTC, daily frequency)
- Store data in a `dict[str, pd.DataFrame]` keyed by ticker symbol
- Implement strict schema validation at ingestion (Issue 16):
  - Check expected column names and types
  - If a file is malformed, log the specific error, skip that asset, and continue — do NOT crash
  - Log all skipped assets with reasons

**Code skeleton to implement:**
```python
class MarketDataIngester:
    def __init__(self, data_dir: str, tickers: list[str])
    def load_all(self) -> dict[str, pd.DataFrame]
    def _load_single(self, ticker: str) -> pd.DataFrame | None
    def _validate_schema(self, df: pd.DataFrame, ticker: str) -> bool
```

**Output:** `raw_data: dict[str, pd.DataFrame]` — validated, timestamped, indexed.

---

## STAGE 2 — Preprocessing: Missing Data & Outlier Handling
*Resolves: Issue 2, Issue 16*

**Task:** Clean the ingested data before any analysis or feature engineering.

**Missing Data Strategy (no forward-looking bias):**
- For prices: use **forward-fill** (`ffill`) capped at 5 consecutive days, then **backward-fill** for any remaining gaps at the start
- For volume: fill with the rolling 5-day median
- Any column still missing after imputation → log a warning and drop that date row

**Outlier Detection & Smoothing:**
- Compute daily log returns for each asset
- Flag any return where `|z-score| > 4` (relative to a 60-day rolling window) as a potential flash crash
- Smooth flagged values by replacing with the rolling 5-day median return (converted back to price)
- Log every flagged outlier: `{date, ticker, original_value, smoothed_value, z_score}`

**Code skeleton:**
```python
class DataPreprocessor:
    def __init__(self, raw_data: dict[str, pd.DataFrame])
    def preprocess(self) -> dict[str, pd.DataFrame]
    def _impute_missing(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame
    def _detect_and_smooth_outliers(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame
```

**Output:** `clean_data: dict[str, pd.DataFrame]`

---

## STAGE 3 — Feature Engineering: Volatility & Momentum
*Resolves: Issue 3*

**Task:** Derive the features that will drive signal generation and risk assessment.

**Features to compute (all on a rolling basis, no lookahead):**

| Feature | Formula | Window |
|---|---|---|
| Log Return | `ln(P_t / P_{t-1})` | Daily |
| Historical Volatility | `std(log_returns) * sqrt(252)` | 21-day rolling |
| Short Momentum | Price change % | 10-day rolling |
| Long Momentum | Price change % | 30-day rolling |
| RSI | Relative Strength Index | 14-day |
| Volume Z-Score | `(vol - mean_vol) / std_vol` | 20-day rolling |

**Rules:**
- All features must be computed using `.rolling().apply()` with `min_periods` set to avoid NaN propagation
- Append features as new columns to each ticker's DataFrame
- Ensure features are only derived from past data — never from future observations

**Code skeleton:**
```python
class FeatureEngineer:
    def __init__(self, clean_data: dict[str, pd.DataFrame])
    def compute_features(self) -> dict[str, pd.DataFrame]
    def _compute_volatility(self, df: pd.DataFrame) -> pd.Series
    def _compute_momentum(self, df: pd.DataFrame, window: int) -> pd.Series
    def _compute_rsi(self, df: pd.DataFrame, window: int = 14) -> pd.Series
```

**Output:** `featured_data: dict[str, pd.DataFrame]` with all feature columns added.

---

## STAGE 4 — Macroeconomic & Sentiment Integration (Optional)
*Resolves: Issue 4*

**Task:** If macro or sentiment data is available, align and merge it with the primary market data.

**Requirements:**
- Macro data (e.g., CPI, Fed rate) is typically monthly → **forward-fill** to daily frequency
- Sentiment data (e.g., news scores) may be daily but sparse → fill gaps with `0` (neutral)
- Normalize all macro/sentiment columns to `[0, 1]` using min-max scaling based on training period only
- Merge on the date index using a **left join** from the market data side (never drop market dates)
- Mark this stage as optional — if no macro data exists, the pipeline continues without it

**Code skeleton:**
```python
class MacroSentimentIntegrator:
    def __init__(self, featured_data: dict[str, pd.DataFrame], macro_path: str = None, sentiment_path: str = None)
    def integrate(self) -> dict[str, pd.DataFrame]
    def _align_frequency(self, macro_df: pd.DataFrame) -> pd.DataFrame
    def _normalize(self, series: pd.Series) -> pd.Series
```

---

## STAGE 5 — Portfolio State Management
*Resolves: Issue 5, Issue 15*

**Task:** Build the central portfolio state object that tracks all positions and cash.

**State to maintain at all times:**
```python
portfolio = {
    "cash": float,                         # available cash
    "positions": dict[str, float],         # ticker → number of shares held
    "position_value": dict[str, float],    # ticker → current market value
    "total_value": float,                  # cash + sum(position_values)
    "daily_values": list[float],           # historical total portfolio values
    "trade_log": list[dict],               # all executed trades
    "error_log": list[dict],               # all rejected trades / errors
}
```

**Rules:**
- `initial_capital` and `max_position_pct` (e.g., 20% per asset) are configurable parameters
- Before any trade, validate: `required_capital <= available_cash` (Issue 15)
  - If insufficient: log `{date, ticker, action, required, available, reason: "INSUFFICIENT_CAPITAL"}` and skip
- Update `position_value` daily using current market prices
- Enforce: no single position can exceed `max_position_pct * total_value`

**Code skeleton:**
```python
class PortfolioManager:
    def __init__(self, initial_capital: float, max_position_pct: float = 0.20)
    def update_prices(self, date: str, prices: dict[str, float])
    def execute_trade(self, date: str, ticker: str, action: str, shares: float, price: float, cost: float) -> bool
    def get_snapshot(self) -> dict
    def get_allocations(self) -> dict[str, float]  # returns % allocation per ticker
```

---

## STAGE 6 — Risk Modeling: VaR, Max Drawdown, Volatility
*Resolves: Issue 6, Issue 7*

**Task:** Implement the core risk metrics that govern the strategy's risk boundaries.

### 6a. Value at Risk (VaR)
- Use the **Historical Simulation** method (non-parametric, no distributional assumption)
- VaR at 95% confidence over a 1-day horizon:
  `VaR = -np.percentile(portfolio_returns[-lookback:], 5)`
- Lookback window: 252 trading days (1 year)
- Recalculate daily after portfolio state update
- If `daily_VaR > risk_tolerance_threshold` → flag a risk breach event in logs

### 6b. Maximum Drawdown
- Track the running peak of portfolio value
- `drawdown[t] = (peak_value - current_value) / peak_value`
- `max_drawdown = max(drawdown)`
- Recalculate on every new daily portfolio value

### 6c. Portfolio Volatility
- Compute rolling 21-day annualized volatility of daily portfolio returns
- `portfolio_vol = std(daily_returns[-21:]) * sqrt(252)`

**Code skeleton:**
```python
class RiskModeler:
    def __init__(self, portfolio_manager: PortfolioManager)
    def calculate_var(self, confidence: float = 0.95) -> float
    def calculate_max_drawdown(self) -> float
    def calculate_portfolio_volatility(self) -> float
    def get_risk_report(self) -> dict
```

---

## STAGE 7 — Trading Signal Generation Engine
*Resolves: Issue 8*

**Task:** Generate buy / sell / hold signals for each asset on each trading day.

**Strategy (rule-based, explainable):**

Use a **multi-factor scoring system**. For each asset on each date:

| Factor | Buy Signal | Sell Signal | Weight |
|---|---|---|---|
| Momentum (10d) | > +2% | < -2% | 0.30 |
| RSI | < 35 (oversold) | > 65 (overbought) | 0.25 |
| Volatility | < median vol | > 1.5x median vol | 0.20 |
| Volume Z-Score | > 1.5 (high conviction) | < -1.0 | 0.15 |
| Macro Sentiment | > 0.6 (positive) | < 0.4 (negative) | 0.10 (if available) |

- Compute a **composite score** in `[-1, +1]`
- `score > 0.3` → **BUY**
- `score < -0.3` → **SELL**
- otherwise → **HOLD**

**Rules:**
- Signals are computed AFTER all features are available (no lookahead)
- Each signal must log the factor values that drove it (for explainability — Issue 14)
- The engine outputs signals only — it does NOT execute trades

**Code skeleton:**
```python
class SignalEngine:
    def __init__(self, featured_data: dict[str, pd.DataFrame], weights: dict = None)
    def generate_signals(self, date: str) -> dict[str, str]  # ticker → "BUY"|"SELL"|"HOLD"
    def get_signal_explanation(self, date: str, ticker: str) -> dict  # factor breakdown
    def _compute_score(self, row: pd.Series) -> float
```

---

## STAGE 8 — Position Sizing & Portfolio Rebalancing
*Resolves: Issue 9, Issue 11*

### 8a. Risk-Aware Position Sizing
- Use **volatility-adjusted sizing**: allocate less capital to high-volatility assets
- `target_weight[ticker] = (1 / vol[ticker]) / sum(1/vol[i] for all BUY signals)`
- Cap each position at `max_position_pct` (from PortfolioManager)
- Compute `shares_to_buy = (target_weight * available_capital) / current_price`
- Round down to whole shares; never go above position limit

### 8b. Periodic Rebalancing
- Trigger rebalancing: **monthly** (first trading day of each month) OR when any position drifts > 15% from its target weight
- Rebalancing logic:
  1. Compute current allocations from PortfolioManager
  2. Compute target allocations from current signals
  3. Generate the minimum set of trades needed to restore targets
  4. Log all rebalancing trades with reason: `"REBALANCE"`

**Code skeleton:**
```python
class PositionSizer:
    def __init__(self, portfolio_manager: PortfolioManager, risk_modeler: RiskModeler)
    def compute_position_sizes(self, signals: dict[str, str], volatilities: dict[str, float], prices: dict[str, float]) -> dict[str, float]
    def should_rebalance(self, date: str, last_rebalance_date: str) -> bool
    def compute_rebalance_trades(self, target_weights: dict[str, float], current_prices: dict[str, float]) -> list[dict]
```

---

## STAGE 9 — Trade Execution Simulation (Costs + Slippage)
*Resolves: Issue 10*

**Task:** Apply market friction to every simulated trade.

**Transaction Costs:**
- Commission: `0.1%` of trade value (configurable)
- Applied on both buy and sell

**Slippage Model:**
- For BUY: execution price = `signal_price * (1 + slippage_factor)`
- For SELL: execution price = `signal_price * (1 - slippage_factor)`
- `slippage_factor = base_slippage + (volume_z_score_penalty if low_liquidity else 0)`
- Base slippage: `0.05%` (configurable); add `0.10%` if Volume Z-Score < -1 (low liquidity)

**Rules:**
- All costs deducted from `portfolio.cash` before updating positions
- Total cost per trade = `commission + slippage_cost`; log separately
- No trade executes at a loss greater than the asset's daily range (sanity check)

**Code skeleton:**
```python
class ExecutionSimulator:
    def __init__(self, commission_rate: float = 0.001, base_slippage: float = 0.0005)
    def execute(self, signal: str, ticker: str, shares: float, signal_price: float, volume_zscore: float, portfolio: PortfolioManager, date: str) -> dict
    def _apply_slippage(self, price: float, action: str, volume_zscore: float) -> float
    def _calculate_commission(self, trade_value: float) -> float
```

---

## STAGE 10 — Performance Metrics
*Resolves: Issue 12, Issue 13*

**Task:** Compute all required KPIs at the end of the simulation period.

### Metrics to implement:

**Returns:**
```python
cumulative_return = (final_value - initial_capital) / initial_capital
annualized_return = (1 + cumulative_return) ** (252 / trading_days) - 1
```

**Sharpe Ratio (Issue 12):**
```python
excess_returns = daily_returns - (risk_free_rate / 252)
sharpe_ratio = (mean(excess_returns) / std(excess_returns)) * sqrt(252)
# risk_free_rate is configurable (default: 0.05)
```

**Alpha & Beta (Issue 13):**
- Requires a benchmark (e.g., SPY or a market index provided in data)
- Use OLS regression: `portfolio_return = alpha + beta * market_return + epsilon`
- `beta = cov(portfolio, market) / var(market)`
- `alpha = mean(portfolio_return) - beta * mean(market_return)` (annualized)

**Code skeleton:**
```python
class MetricsCalculator:
    def __init__(self, portfolio_manager: PortfolioManager, benchmark_returns: pd.Series, risk_free_rate: float = 0.05)
    def compute_all(self) -> dict
    def sharpe_ratio(self) -> float
    def alpha_beta(self) -> tuple[float, float]
    def max_drawdown(self) -> float
    def annualized_return(self) -> float
    def annualized_volatility(self) -> float
```

---

## STAGE 11 — Explainability Logging
*Resolves: Issue 14, Issue 15, Issue 16*

**Task:** Every signal, trade, rejection, and risk event must be logged with full context.

**Log entry schema (JSON per event):**
```json
{
  "timestamp": "2024-01-15",
  "event_type": "TRADE_EXECUTED | TRADE_REJECTED | SIGNAL | RISK_BREACH | DATA_ERROR",
  "ticker": "AAPL",
  "action": "BUY | SELL | HOLD | SKIP",
  "reason": "human-readable explanation",
  "factors": {
    "momentum_10d": 0.034,
    "rsi": 32.1,
    "volatility": 0.18,
    "composite_score": 0.41
  },
  "portfolio_state": {
    "cash_before": 95000.0,
    "cash_after": 87540.0,
    "total_value": 102000.0
  },
  "costs": {
    "commission": 75.0,
    "slippage": 37.5
  }
}
```

**Implementation:**
- Use Python's `logging` module + a custom `JSONFileHandler`
- Maintain a live `trade_log.jsonl` (append-only, one JSON object per line)
- Maintain a separate `error_log.jsonl` for rejected trades and data issues
- At end of simulation, export a `summary_log.json` with aggregate counts

```python
class AuditLogger:
    def __init__(self, log_dir: str)
    def log_signal(self, date, ticker, signal, explanation)
    def log_trade(self, date, ticker, action, shares, price, costs, portfolio_snapshot)
    def log_rejection(self, date, ticker, reason, details)
    def log_risk_event(self, date, metric, value, threshold)
    def log_data_error(self, source, error, record)
    def export_summary(self) -> dict
```

---

## STAGE 12 — Dashboard Data Output
*Resolves: Issue 18*

**Task:** Aggregate all simulation outputs into a structured format for visualization.

**Output files to generate:**

1. `portfolio_timeseries.csv` — columns: `date, total_value, cash, invested_value, daily_return, cumulative_return, rolling_sharpe, rolling_var, rolling_drawdown`

2. `trade_log.csv` — columns: `date, ticker, action, shares, price, value, commission, slippage, reason`

3. `asset_allocations.csv` — columns: `date, ticker, weight` (daily snapshot)

4. `metrics_summary.json` — final values: `{sharpe, alpha, beta, max_drawdown, annualized_return, annualized_vol, total_trades, win_rate, ...}`

5. `signal_heatmap.csv` — columns: `date, ticker, signal, composite_score` (for all assets, all dates)

**Visualization layer** (Plotly / matplotlib):
- Line chart: Portfolio value over time vs. benchmark
- Bar chart: Final asset allocation
- Heatmap: Daily signal matrix (assets × dates)
- Rolling metrics chart: Sharpe, VaR, Drawdown over time

```python
class DashboardExporter:
    def __init__(self, portfolio_manager, metrics, signal_history, log_dir)
    def export_all(self)
    def build_timeseries_df(self) -> pd.DataFrame
    def build_allocation_df(self) -> pd.DataFrame
    def plot_all(self, output_dir: str)
```

---

## STAGE 13 — Scalability & Performance Optimization
*Resolves: Issue 17, Issue 20*

**Task:** Ensure the system handles large asset universes efficiently and survives edge cases.

**Optimization techniques:**
- Use `concurrent.futures.ThreadPoolExecutor` for parallel per-asset feature engineering
- Use `numpy` vectorized operations instead of row-by-row loops wherever possible
- Cache computed volatility and correlation matrices; invalidate weekly
- Profile with `cProfile` and optimize any function taking > 1s per 100 assets

**Edge case tests to implement (Issue 20):**

| Scenario | Expected Behavior |
|---|---|
| All assets hit VaR limit simultaneously | Freeze all trades; log `RISK_BREACH`; continue next day |
| Cash drops below 5% of initial capital | Block all new BUY orders until cash restored |
| Asset has 20+ consecutive missing days | Drop asset from universe for that window; log warning |
| Flash crash: asset drops > 15% in 1 day | Outlier smoothed; signal engine re-evaluates with smoothed data |
| Portfolio drawdown exceeds 20% | Trigger emergency rebalance to reduce risk exposure |
| Benchmark data missing for a date | Skip Alpha/Beta calc for that day; interpolate over gap |

---

## STAGE 14 — System Documentation
*Resolves: Issue 19*

**Task:** Write the following documentation files:

1. **`README.md`** — Setup instructions, how to run the full pipeline, configurable parameters table
2. **`ARCHITECTURE.md`** — Module diagram (ASCII or Mermaid), data flow description, design rationale
3. **`STRATEGY.md`** — Full explanation of the trading strategy, factor weights, and why each was chosen
4. **`RISK_FRAMEWORK.md`** — How VaR is calculated, drawdown monitoring, position limits, and risk breach handling

---

## CONFIGURATION REFERENCE

All parameters should be centralized in a `config.yaml`:

```yaml
portfolio:
  initial_capital: 1_000_000
  max_position_pct: 0.20        # Max 20% per asset
  risk_tolerance_var: 0.03      # Max daily VaR: 3% of portfolio
  max_drawdown_limit: 0.20      # Emergency rebalance at 20% drawdown
  min_cash_pct: 0.05            # Always keep 5% in cash

trading:
  commission_rate: 0.001        # 0.1%
  base_slippage: 0.0005         # 0.05%
  rebalance_frequency: "monthly"
  drift_threshold: 0.15         # Rebalance if drift > 15%

signals:
  buy_threshold: 0.30
  sell_threshold: -0.30
  rsi_oversold: 35
  rsi_overbought: 65

risk:
  var_confidence: 0.95
  var_lookback_days: 252
  volatility_window: 21
  momentum_short_window: 10
  momentum_long_window: 30

metrics:
  risk_free_rate: 0.05
  benchmark_ticker: "SPY"
```

---

## DELIVERABLES CHECKLIST

Before final submission, verify:

- [ ] All 20 GitHub issues resolved with corresponding code modules
- [ ] Pipeline runs end-to-end with no crashes on provided datasets
- [ ] All edge cases from Stage 13 tested and logged correctly
- [ ] `trade_log.jsonl`, `error_log.jsonl`, `summary_log.json` generated
- [ ] All 5 dashboard output files generated and visualizations render
- [ ] Sharpe Ratio, Alpha, Beta, Max Drawdown all printed in final report
- [ ] `README.md` contains setup and run instructions
- [ ] `config.yaml` is the single source of truth for all parameters
- [ ] No forward-looking bias in any feature or signal computation
- [ ] All costs and slippage deducted from portfolio correctly

---

## EVALUATION ALIGNMENT

| Criterion | Addressed By |
|---|---|
| Performance (Sharpe, Alpha) | Stage 10 — MetricsCalculator |
| Risk Management | Stage 6 (VaR, Drawdown), Stage 8 (Position sizing), Stage 5 (Limits) |
| Strategy Design | Stage 7 (Multi-factor), Stage 3 (Features), Stage 11 (Explainability) |
| Dashboard Quality | Stage 12 (DashboardExporter + Plotly charts) |
| Scalability | Stage 13 (ThreadPoolExecutor + vectorization) |
| Code Quality | Modular classes, config.yaml, type hints, docstrings throughout |

---

*Generated for Code2Create Challenge Round 3 — Hedge Fund Risk Modeling & Semi-Automated Trading System*
