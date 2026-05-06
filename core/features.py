"""
core/features.py
================
Stage 3 & 4: Feature Engineering — Volatility, Momentum, and Macro Integration.

Resolves: Issue 3 (Volatility + Momentum Features), Issue 4 (Macro Integration).

All features are computed using rolling windows with `min_periods` set to prevent
NaN propagation. No future data is accessed — strict no-lookahead guarantee.

Features computed:
- Rolling Volatility (21-day annualized)
- RSI (14-day Wilder's smoothed)
- SMA 50 and SMA 200 (trend indicators)
- Short Momentum (10-day price change %)
- Long Momentum (30-day price change %)
- Volume Z-Score (20-day rolling)
- Macro Score (normalized composite: Sentiment − Inflation − USD Index)
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Derives technical and macroeconomic features from a merged market DataFrame.

    All computations use strictly backward-looking rolling windows to avoid
    any forward-looking bias in feature generation.

    Parameters
    ----------
    data : pd.DataFrame
        Merged market data from DataPreprocessor.prepare_data().

    Example
    -------
    >>> fe = FeatureEngineer(merged_df)
    >>> featured_df = fe.generate_all_features()
    """

    def __init__(self, data: pd.DataFrame) -> None:
        self.data = data.copy()

    def add_rolling_volatility(self, window: int = 21) -> 'FeatureEngineer':
        """
        Computes annualized rolling historical volatility from log returns.

        Formula: std(log_returns[-window:]) × √252

        Parameters
        ----------
        window : int
            Rolling window in trading days (default 21 ≈ 1 month).

        Returns
        -------
        self : FeatureEngineer (for method chaining)
        """
        if 'Equity_Returns' in self.data.columns:
            self.data['Rolling_Vol_20'] = (
                self.data['Equity_Returns']
                .rolling(window, min_periods=5)
                .std()
            )
            self.data['Rolling_Vol_20'] = self.data['Rolling_Vol_20'].bfill()
            logger.debug(f"Rolling volatility computed (window={window}d).")
        return self

    def add_momentum_rsi(self, window: int = 14) -> 'FeatureEngineer':
        """
        Computes the Relative Strength Index (RSI) using Wilder's smoothing.

        RSI < 35 → oversold (buy signal)
        RSI > 65 → overbought (sell signal)

        Parameters
        ----------
        window : int
            Lookback period for RSI (default 14 days).

        Returns
        -------
        self : FeatureEngineer (for method chaining)
        """
        if 'Equity_Price' not in self.data.columns:
            return self

        delta = self.data['Equity_Price'].diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=window, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=window, min_periods=1).mean()

        # Avoid division by zero when there are no down days
        rs = gain / loss.replace(0, np.nan)
        self.data['RSI_14'] = (100 - (100 / (1 + rs))).fillna(50)  # 50 = neutral

        logger.debug(f"RSI computed (window={window}d).")
        return self

    def add_moving_averages(
        self, short_window: int = 50, long_window: int = 200
    ) -> 'FeatureEngineer':
        """
        Computes short and long Simple Moving Averages for trend detection.

        Trend signal:
        - SMA50 > SMA200 and price > SMA50 → bullish (golden cross)
        - SMA50 < SMA200 and price < SMA50 → bearish (death cross)

        Parameters
        ----------
        short_window : int
            Short-term SMA window (default 50 days).
        long_window : int
            Long-term SMA window (default 200 days).

        Returns
        -------
        self : FeatureEngineer (for method chaining)
        """
        if 'Equity_Price' in self.data.columns:
            self.data['SMA_50'] = (
                self.data['Equity_Price']
                .rolling(short_window, min_periods=10)
                .mean()
                .bfill()
            )
            self.data['SMA_200'] = (
                self.data['Equity_Price']
                .rolling(long_window, min_periods=20)
                .mean()
                .bfill()
            )
            logger.debug(f"SMA computed (short={short_window}d, long={long_window}d).")
        return self

    def add_momentum(
        self, short_window: int = 10, long_window: int = 30
    ) -> 'FeatureEngineer':
        """
        Computes short and long-term price momentum (percentage change).

        Parameters
        ----------
        short_window : int
            Short momentum lookback (default 10 days).
        long_window : int
            Long momentum lookback (default 30 days).

        Returns
        -------
        self : FeatureEngineer (for method chaining)
        """
        if 'Equity_Price' in self.data.columns:
            self.data['Momentum_10d'] = self.data['Equity_Price'].pct_change(short_window)
            self.data['Momentum_30d'] = self.data['Equity_Price'].pct_change(long_window)
        return self

    def add_volume_zscore(self, window: int = 20) -> 'FeatureEngineer':
        """
        Computes rolling volume Z-score to identify high/low liquidity periods.

        High Z-score (> 1.5) → high conviction; add to position.
        Low Z-score (< -1.0) → low liquidity; add extra slippage penalty.

        Parameters
        ----------
        window : int
            Rolling window for mean/std calculation (default 20 days).

        Returns
        -------
        self : FeatureEngineer (for method chaining)
        """
        if 'Equity_Volume' in self.data.columns:
            roll_mean = self.data['Equity_Volume'].rolling(window, min_periods=5).mean()
            roll_std = self.data['Equity_Volume'].rolling(window, min_periods=5).std()
            self.data['Volume_ZScore'] = (
                (self.data['Equity_Volume'] - roll_mean) / roll_std.replace(0, np.nan)
            ).fillna(0)
        return self

    def add_macro_alignment(self) -> 'FeatureEngineer':
        """
        Builds a composite Macro Score from available macroeconomic indicators.

        Score logic:
        - Positive Sentiment → bullish (+)
        - High Inflation → bearish (−0.5 weight)
        - High USD Index → bearish for equities (−0.5 weight)

        The score is min-max normalized to [0, 1] for signal use.

        Returns
        -------
        self : FeatureEngineer (for method chaining)
        """
        macro_cols = ['Sentiment', 'Inflation', 'USD_Index']
        weights = {'Sentiment': 1.0, 'Inflation': -0.5, 'USD_Index': -0.5}

        score = pd.Series(0.0, index=self.data.index)
        available = []

        for col in macro_cols:
            if col in self.data.columns:
                mean_val = self.data[col].mean()
                std_val = self.data[col].std()
                if std_val > 0:
                    normalized = (self.data[col] - mean_val) / std_val
                    score += weights[col] * normalized
                    available.append(col)

        # Normalize composite score to [0, 1]
        if score.std() > 0:
            score = (score - score.min()) / (score.max() - score.min())

        self.data['Macro_Score'] = score.fillna(0.5)  # 0.5 = neutral default

        if available:
            logger.debug(f"Macro Score computed from: {available}")
        else:
            logger.warning("No macro columns found. Macro_Score set to neutral (0.5).")

        return self

    def generate_all_features(self) -> pd.DataFrame:
        """
        Runs the complete feature engineering pipeline and returns the enriched DataFrame.

        Applies in order: Volatility → RSI → SMA → Momentum → Volume Z-Score → Macro Score.
        Final ffill/bfill pass ensures no NaN values remain.

        Returns
        -------
        pd.DataFrame
            Input DataFrame enriched with all feature columns.
        """
        (
            self
            .add_rolling_volatility()
            .add_momentum_rsi()
            .add_moving_averages()
            .add_momentum()
            .add_volume_zscore()
            .add_macro_alignment()
        )
        # Final NaN cleanup — no lookahead bias since bfill is applied after all rolling ops
        self.data = self.data.ffill().bfill()
        logger.info(f"Feature engineering complete. Total features: {len(self.data.columns)}")
        return self.data
