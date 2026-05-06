"""
core/risk.py
============
Stage 6 & 7: Risk Modeling and Position Sizing.

Resolves: Issue 6 (Value at Risk), Issue 7 (Max Drawdown & Volatility),
          Issue 9 (Risk-Aware Position Sizing).

Implements non-parametric Historical VaR, continuous max drawdown tracking,
and volatility-targeted position sizing.
"""

import logging
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class RiskModeler:
    """
    Computes risk metrics for the portfolio.

    Parameters
    ----------
    confidence_level : float
        Confidence level for VaR (e.g., 0.95).
    lookback : int
        Number of trailing days to use for Historical VaR.
    """

    def __init__(self, confidence_level: float = 0.95, lookback: int = 252) -> None:
        self.confidence_level = confidence_level
        self.lookback = lookback

    def calculate_historical_var(self, returns_series: pd.Series) -> float:
        """
        Calculates Value at Risk using the historical simulation method.
        Non-parametric approach prevents distribution assumptions from failing
        during fat-tail events.

        Parameters
        ----------
        returns_series : pd.Series
            Historical daily returns of the asset/portfolio.

        Returns
        -------
        float
            Estimated loss at the confidence level (a negative number).
        """
        if len(returns_series) < self.lookback:
            return float(returns_series.quantile(1 - self.confidence_level)) if len(returns_series) > 0 else -0.05

        recent_returns = returns_series.tail(self.lookback)
        var = recent_returns.quantile(1 - self.confidence_level)
        return float(var)

    def calculate_parametric_var(self, returns_series: pd.Series) -> float:
        """Calculates VaR assuming normal distribution (optional alternative)."""
        if len(returns_series) < 2:
            return -0.05
        mean = returns_series.mean()
        std = returns_series.std()

        if self.confidence_level >= 0.99:
            z_score = -2.33
        elif self.confidence_level >= 0.95:
            z_score = -1.645
        elif self.confidence_level >= 0.90:
            z_score = -1.28
        else:
            z_score = -1.645

        var = mean + z_score * std
        return float(var)

    def calculate_drawdown(self, portfolio_values: pd.Series) -> float:
        """
        Calculates the current maximum drawdown of the portfolio.

        Parameters
        ----------
        portfolio_values : pd.Series
            Historical net asset values of the portfolio.

        Returns
        -------
        float
            Current drawdown as a percentage (a negative number or zero).
        """
        rolling_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values / rolling_max) - 1.0
        return float(drawdown.iloc[-1]) if len(drawdown) > 0 else 0.0


class PositionSizer:
    """
    Determines trade sizes based on target volatility and signal conviction.

    Parameters
    ----------
    max_position_size : float
        Maximum percentage of the total portfolio allowed in one asset.
    target_volatility : float
        The annualized volatility target for the asset position.
    """

    def __init__(self, max_position_size: float = 0.15, target_volatility: float = 0.10) -> None:
        self.max_position_size = max_position_size
        self.target_volatility = target_volatility  # 10% annualized vol target

    def calculate_position_size(
        self, signal: float, current_volatility: float, capital: float
    ) -> Tuple[float, float]:
        """
        Dynamically sizes a position using Volatility Targeting.
        Weight = Target Vol / Current Vol. Highly volatile assets get smaller allocations.

        Parameters
        ----------
        signal : float
            Trading signal between -1.0 and 1.0.
        current_volatility : float
            Current annualized or daily volatility.
        capital : float
            Total capital available in the portfolio.

        Returns
        -------
        tuple
            (position_value_in_dollars, final_weight)
        """
        if current_volatility <= 0 or pd.isna(current_volatility):
            # Fallback size if vol is zero or unknown
            raw_weight = self.max_position_size * 0.5
        else:
            # Annualize daily vol
            annual_vol = current_volatility * np.sqrt(252)
            if annual_vol == 0:
                raw_weight = 0.0
            else:
                vol_scalar = self.target_volatility / annual_vol
                # Base weight modulated by absolute signal strength
                raw_weight = vol_scalar * abs(signal)

        # Enforce maximum position limit
        final_weight = min(raw_weight, self.max_position_size)

        # Determine long/short/flat direction
        # Modified: No short selling allowed. Negative signals simply liquidate to cash (0).
        direction = 1 if signal > 0 else 0

        position_value = capital * final_weight * direction
        return position_value, final_weight * direction
