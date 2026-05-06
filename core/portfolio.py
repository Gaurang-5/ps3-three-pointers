"""
core/portfolio.py
=================
Stage 5, 9 & 11: Portfolio State Management, Trade Execution, and Rebalancing.

Resolves: Issue 5 (State Management), Issue 10 (Transaction Costs & Slippage),
          Issue 11 (Periodic Portfolio Rebalancing), Issue 15 (Insufficient Capital).

Manages multi-asset positions, enforces position limits, tracks cash, and handles
drift-based rebalancing and daily mark-to-market valuations.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List

logger = logging.getLogger(__name__)

class InsufficientCapitalError(Exception):
    """Raised when there is not enough cash to execute a trade."""
    pass

class PortfolioManager:
    """
    State manager for the multi-asset trading simulation.

    Parameters
    ----------
    initial_capital : float
        Starting cash balance.
    transaction_cost_pct : float
        Commission rate (e.g., 0.001 for 10 bps).
    slippage_pct : float
        Slippage penalty rate (e.g., 0.0005 for 5 bps).
    """

    def __init__(
        self,
        initial_capital: float = 1_000_000.0,
        transaction_cost_pct: float = 0.001,
        slippage_pct: float = 0.0005
    ) -> None:
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.shares: Dict[str, float] = {}  # Dynamic multi-asset support
        self.history: List[Dict[str, float]] = []
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct

    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculates total portfolio value (cash + mark-to-market positions).

        Parameters
        ----------
        current_prices : dict
            Current prices keyed by asset ticker.

        Returns
        -------
        float
            Total net asset value.
        """
        total_value = self.cash
        for asset, qty in self.shares.items():
            price = current_prices.get(asset)
            if price is not None and not pd.isna(price):
                total_value += qty * price
        return total_value

    def get_current_weights(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """
        Calculates the current allocation weight of each asset in the portfolio.

        Returns
        -------
        dict
            Asset weights (0.0 to 1.0) keyed by ticker.
        """
        total_val = self.get_total_value(current_prices)
        if total_val <= 0:
            return {}

        weights = {}
        for asset, qty in self.shares.items():
            price = current_prices.get(asset)
            if price is not None and not pd.isna(price):
                weights[asset] = (qty * price) / total_val
        return weights

    def should_rebalance(
        self,
        target_weights: Dict[str, float],
        current_prices: Dict[str, float],
        drift_threshold: float = 0.15
    ) -> bool:
        """
        Determines if the portfolio has drifted beyond acceptable limits (Issue 11).

        Parameters
        ----------
        target_weights : dict
            Target weights keyed by ticker.
        current_prices : dict
            Current prices keyed by asset ticker.
        drift_threshold : float
            Maximum allowed absolute deviation (e.g., 0.15 for 15%).

        Returns
        -------
        bool
            True if any asset deviates from its target by > drift_threshold.
        """
        current_weights = self.get_current_weights(current_prices)
        
        # Check drift for all assets (both in targets and current holdings)
        all_assets = set(target_weights.keys()).union(set(self.shares.keys()))
        
        for asset in all_assets:
            target = target_weights.get(asset, 0.0)
            current = current_weights.get(asset, 0.0)
            if abs(current - target) > drift_threshold:
                return True
                
        return False

    def execute_trade(
        self,
        asset: str,
        target_value: float,
        current_price: float,
        date: str,
        min_cash_reserve: float = 0.0
    ) -> Tuple[float, float, float]:
        """
        Executes a trade to adjust an asset's position to a target value.

        Simulates slippage and deducts transaction costs. Gracefully scales down
        trades if capital is insufficient (Issue 15).

        Parameters
        ----------
        asset : str
            Asset ticker symbol.
        target_value : float
            Desired total value of this asset position in $.
        current_price : float
            Current market price of the asset.
        date : str
            Current date string (for logging).
        min_cash_reserve : float
            Minimum cash balance that must remain after execution.

        Returns
        -------
        tuple
            (transaction_cost, shares_traded, executed_price)
        """
        if pd.isna(current_price) or current_price <= 0:
            logger.warning(f"[{date}] Invalid price for {asset}. Skipping trade.")
            return 0.0, 0.0, current_price

        current_value = self.shares.get(asset, 0.0) * current_price
        value_delta = target_value - current_value

        if abs(value_delta) < 100:  # Minimum trade threshold to avoid micro-trades
            return 0.0, 0.0, current_price

        shares_to_trade = value_delta / current_price
        direction = np.sign(shares_to_trade)

        # Apply slippage: buy higher, sell lower
        executed_price = current_price * (1 + direction * self.slippage_pct)
        gross_cost = shares_to_trade * executed_price
        tx_cost = abs(gross_cost) * self.transaction_cost_pct
        total_cash_impact = gross_cost + tx_cost

        # Capital safeguard: scale down if buying more than cash allows
        if total_cash_impact > (self.cash - min_cash_reserve) and direction > 0:
            available_cash = max(self.cash - min_cash_reserve, 0.0)
            max_affordable_gross = available_cash / (1 + self.transaction_cost_pct)
            shares_to_trade = max_affordable_gross / executed_price
            gross_cost = shares_to_trade * executed_price
            tx_cost = abs(gross_cost) * self.transaction_cost_pct
            total_cash_impact = gross_cost + tx_cost
            logger.warning(f"[{date}] Insufficient capital. Scaled down trade for {asset}.")
            if available_cash < 10:
                raise InsufficientCapitalError(f"[{date}] Insufficient capital to trade.")

        # Update state
        self.cash -= total_cash_impact
        self.shares[asset] = self.shares.get(asset, 0.0) + shares_to_trade
        
        # Clean up zero-share positions
        if abs(self.shares[asset]) < 1e-6:
            self.shares[asset] = 0.0

        return tx_cost, shares_to_trade, executed_price

    def update_history(self, date: str, current_prices: Dict[str, float]) -> None:
        """
        Records the end-of-day portfolio state.

        Parameters
        ----------
        date : str
            The current date.
        current_prices : dict
            Current prices of all assets.
        """
        total_val = self.get_total_value(current_prices)
        snapshot = {
            'Date': date,
            'Total_Value': total_val,
            'Cash': self.cash
        }
        # Record shares and prices for all held and tracked assets
        for asset, price in current_prices.items():
            snapshot[f'{asset}_Shares'] = self.shares.get(asset, 0.0)
            snapshot[f'{asset}_Price'] = price
            
        self.history.append(snapshot)

    def get_history_df(self) -> pd.DataFrame:
        """Returns the portfolio history as a pandas DataFrame."""
        return pd.DataFrame(self.history)
