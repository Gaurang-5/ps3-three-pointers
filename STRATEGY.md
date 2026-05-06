# Trading Strategy

The trading engine uses a long-only, risk-aware multi-factor approach with portfolio-level controls.

## Signal Generation (`SignalEngine`)
Each asset gets a composite signal in `[-1.0, +1.0]` from:

1. **RSI_14**:
   - Oversold (`RSI < rsi_oversold`) adds +0.4.
   - Overbought (`RSI > rsi_overbought`) subtracts -0.4.
2. **Trend (SMA 50/200 + Price Confirmation)**:
   - `SMA50 > SMA200` and `Price > SMA50` adds +0.3.
   - `SMA50 < SMA200` and `Price < SMA50` subtracts -0.3.
3. **Momentum Confirmation (10d + 30d)**:
   - Both positive adds +0.2.
   - Both negative subtracts -0.2.
4. **Macro Alignment**:
   - `Macro_Score > 0.6` adds +0.1.
   - `Macro_Score < 0.4` subtracts -0.1.
5. **Volatility Filter**:
   - If rolling volatility > 3% daily, force signal to 0 (cash/hold).

Directional thresholding is explicit:
- `signal >= buy_threshold` => directional BUY bias.
- `signal <= sell_threshold` => directional SELL/de-risk bias.
- In-between => neutral.

## Portfolio Construction & Risk

At rebalance time, signals are converted to portfolio weights with:
- A baseline diversified allocation (prevents idle all-cash traps).
- Per-asset cap via `max_position_pct`.
- Hard cash reserve via `min_cash_pct`.

Portfolio risk overlays:
- **VaR gate**: on portfolio VaR breach, new buys are blocked.
- **Drawdown defensive mode**: on drawdown breach, portfolio enters temporary reduced-risk mode instead of permanently staying in cash.
