# Trading Strategy

The trading engine utilizes a multi-factor signal approach.

## Signal Generation (`SignalEngine`)
The signal ranges from -1.0 (Strong Sell) to +1.0 (Strong Buy) based on the aggregation of:

1. **Momentum (RSI_14)**:
   - Oversold (<30) adds +0.4 to the score.
   - Overbought (>70) subtracts -0.4.
2. **Trend Alignment (SMA Cross)**:
   - Price > SMA50 > SMA200 adds +0.3.
   - Price < SMA50 < SMA200 subtracts -0.3.
3. **Macro Alignment**:
   - High Sentiment, Low Inflation, and Low USD Index generate a high `Macro_Score`.
   - Score > 0.5 adds +0.3.
   - Score < -0.5 subtracts -0.3.

## Volatility Filter
If the 20-day rolling volatility exceeds extreme levels (e.g., >3% daily), the system overrides the signal to 0.0 (Hold Cash) to prevent excessive capital destruction.
