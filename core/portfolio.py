import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class InsufficientCapitalError(Exception):
    """Raised when there is not enough cash to execute a trade."""
    pass

class PortfolioManager:
    def __init__(self, initial_capital=1_000_000.0, transaction_cost_pct=0.001, slippage_pct=0.0005):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.shares = {'Equity': 0.0} # Can be extended to Multi-Asset
        self.history = []
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        
    def get_total_value(self, current_prices):
        """Calculates total portfolio value (cash + mark-to-market positions)."""
        total_value = self.cash
        for asset, qty in self.shares.items():
            if asset in current_prices and not pd.isna(current_prices[asset]):
                total_value += qty * current_prices[asset]
        return total_value
        
    def execute_trade(self, asset, target_value, current_price, date):
        """
        Simulates execution of a trade to reach target position value.
        Incorporates transaction costs and slippage.
        """
        if pd.isna(current_price) or current_price <= 0:
            logger.warning(f"Invalid price for {asset} on {date}. Skipping trade.")
            return 0.0
            
        current_value = self.shares.get(asset, 0.0) * current_price
        value_delta = target_value - current_value
        
        # Don't trade if delta is insignificantly small
        if abs(value_delta) < 100: 
            return 0.0
            
        shares_to_trade = value_delta / current_price
        direction = np.sign(shares_to_trade)
        
        # Slippage simulation (Buy higher, Sell lower)
        executed_price = current_price * (1 + direction * self.slippage_pct)
        gross_cost = shares_to_trade * executed_price
        
        # Transaction Cost simulation
        tx_cost = abs(gross_cost) * self.transaction_cost_pct
        
        total_cash_impact = gross_cost + tx_cost
        
        # Error Handling: Insufficient Capital
        if total_cash_impact > self.cash and direction > 0:
            # Adjust target value to what we can afford
            max_affordable_gross = self.cash / (1 + self.transaction_cost_pct)
            shares_to_trade = max_affordable_gross / executed_price
            gross_cost = shares_to_trade * executed_price
            tx_cost = abs(gross_cost) * self.transaction_cost_pct
            total_cash_impact = gross_cost + tx_cost
            logger.warning(f"[{date}] Insufficient capital. Scaled down trade for {asset}.")
            if self.cash < 10:
                raise InsufficientCapitalError(f"[{date}] Bankrupt or insufficient capital to trade.")
                
        # Execute trade
        self.cash -= total_cash_impact
        self.shares[asset] = self.shares.get(asset, 0.0) + shares_to_trade
        
        return tx_cost

    def update_history(self, date, current_prices):
        """Snapshots the portfolio state at the end of the day."""
        total_val = self.get_total_value(current_prices)
        self.history.append({
            'Date': date,
            'Total_Value': total_val,
            'Cash': self.cash,
            'Equity_Shares': self.shares.get('Equity', 0.0),
            'Equity_Price': current_prices.get('Equity', 0.0)
        })
        
    def get_history_df(self):
        """Returns the portfolio history as a DataFrame."""
        return pd.DataFrame(self.history)
