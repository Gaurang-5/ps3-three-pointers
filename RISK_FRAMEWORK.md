# Risk Framework

## 1. Value at Risk (VaR)
Calculated using a 252-day historical lookback window at a 95% confidence interval. This metric is logged with every trade to track portfolio exposure.

## 2. Volatility Targeting (Position Sizing)
Positions are dynamically sized based on current market volatility to hit a target annualized volatility of 10%.
- **Formula**: `Target Weight = (Target Volatility / Annualized Current Volatility) * |Signal|`
- **Cap**: The maximum allocation to any single asset is hard-capped at 15% of total portfolio value (`max_position_size = 0.15`).

## 3. Drawdown Stop-Loss
The system actively tracks the High-Water Mark. If the portfolio suffers a drawdown exceeding 5% (`stop_loss = 0.05`), the signal engine forces liquidation (Signal = 0.0) until conditions improve, acting as a circuit breaker.

## 4. Execution Friction
To reflect reality, every trade assumes a 10bps transaction cost and 5bps slippage impact.
