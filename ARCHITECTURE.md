# System Architecture

## Core Modules

- **`core/data.py` (DataPreprocessor)**: Ingests raw CSVs, merges them on a primary timeline (Equity), handles missing values via forward/backward filling, and caps outliers at 3 standard deviations.
- **`core/features.py` (FeatureEngineer)**: Generates technical indicators (RSI, SMA, Rolling Volatility) and normalizes macroeconomic indicators (Inflation, Sentiment, USD Index) into a unified `Macro_Score`.
- **`core/portfolio.py` (PortfolioManager)**: Manages state, processes simulated executions, applies transaction costs (0.1%) and slippage (0.05%), and throws `InsufficientCapitalError` if limits are breached.
- **`core/risk.py` (RiskModeler & PositionSizer)**: Calculates Value at Risk (VaR) and Maximum Drawdown. Dynamically sizes positions based on a target annualized volatility to ensure risk parity.
- **`core/trading.py` (SignalEngine & AuditLogger)**: Evaluates features to produce a continuous signal between -1.0 and 1.0. Records decisions and the mathematical reasoning to JSON.
- **`core/metrics.py` (PerformanceMetrics)**: Computes Sharpe Ratio, Sortino Ratio, Alpha, Beta, and Max Drawdown post-simulation.

## Data Flow
`Raw CSVs -> data.py -> features.py -> main.py (loop) -> [trading.py <-> portfolio.py <-> risk.py] -> metrics.py -> Outputs (JSON)`
