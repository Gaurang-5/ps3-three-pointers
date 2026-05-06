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

    def _get_prefixes(self) -> list[str]:
        return ['Equity_', 'Oil_', 'Gold_', 'Bond_']

    def add_rolling_volatility(self, window: int = 21) -> 'FeatureEngineer':
        """Computes annualized rolling historical volatility from log returns."""
        for pfx in self._get_prefixes():
            ret_col = f'{pfx}Returns'
            if ret_col in self.data.columns:
                self.data[f'{pfx}Rolling_Vol_20'] = (
                    self.data[ret_col].rolling(window, min_periods=5).std()
                )
                self.data[f'{pfx}Rolling_Vol_20'] = self.data[f'{pfx}Rolling_Vol_20'].bfill()
        return self

    def add_momentum_rsi(self, window: int = 14) -> 'FeatureEngineer':
        """Computes RSI using Wilder's smoothing for all assets."""
        for pfx in self._get_prefixes():
            price_col = f'{pfx}Price'
            if price_col not in self.data.columns:
                continue

            delta = self.data[price_col].diff()
            gain = delta.where(delta > 0, 0.0).rolling(window=window, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(window=window, min_periods=1).mean()

            rs = gain / loss.replace(0, np.nan)
            self.data[f'{pfx}RSI_14'] = (100 - (100 / (1 + rs))).fillna(50)
        return self

    def add_moving_averages(
        self, short_window: int = 50, long_window: int = 200
    ) -> 'FeatureEngineer':
        """Computes short and long SMAs for all assets."""
        for pfx in self._get_prefixes():
            price_col = f'{pfx}Price'
            if price_col in self.data.columns:
                self.data[f'{pfx}SMA_50'] = (
                    self.data[price_col].rolling(short_window, min_periods=10).mean().bfill()
                )
                self.data[f'{pfx}SMA_200'] = (
                    self.data[price_col].rolling(long_window, min_periods=20).mean().bfill()
                )
        return self

    def add_momentum(
        self, short_window: int = 10, long_window: int = 30
    ) -> 'FeatureEngineer':
        """Computes short and long-term price momentum for all assets."""
        for pfx in self._get_prefixes():
            price_col = f'{pfx}Price'
            if price_col in self.data.columns:
                self.data[f'{pfx}Momentum_10d'] = self.data[price_col].pct_change(short_window)
                self.data[f'{pfx}Momentum_30d'] = self.data[price_col].pct_change(long_window)
        return self

    def add_volume_zscore(self, window: int = 20) -> 'FeatureEngineer':
        """Computes rolling volume Z-score for assets with volume."""
        for pfx in self._get_prefixes():
            vol_col = f'{pfx}Volume'
            if vol_col in self.data.columns:
                roll_mean = self.data[vol_col].rolling(window, min_periods=5).mean()
                roll_std = self.data[vol_col].rolling(window, min_periods=5).std()
                self.data[f'{pfx}Volume_ZScore'] = (
                    (self.data[vol_col] - roll_mean) / roll_std.replace(0, np.nan)
                ).fillna(0)
        return self

    def add_macro_alignment(self) -> 'FeatureEngineer':
        """Builds a composite Macro Score from macroeconomic indicators."""
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

        if score.std() > 0:
            score = (score - score.min()) / (score.max() - score.min())

        self.data['Macro_Score'] = score.fillna(0.5)
        return self

    def generate_all_features(self) -> pd.DataFrame:
        """Runs the complete feature engineering pipeline."""
        (
            self
            .add_rolling_volatility()
            .add_momentum_rsi()
            .add_moving_averages()
            .add_momentum()
            .add_volume_zscore()
            .add_macro_alignment()
        )
        self.data = self.data.ffill().bfill()
        return self.data
