import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class RiskModeler:
    def __init__(self, confidence_level=0.95, lookback=252):
        self.confidence_level = confidence_level
        self.lookback = lookback
        
    def calculate_historical_var(self, returns_series: pd.Series):
        """Calculates Value at Risk using historical simulation method."""
        if len(returns_series) < self.lookback:
            return returns_series.quantile(1 - self.confidence_level) if len(returns_series) > 0 else -0.05
            
        recent_returns = returns_series.tail(self.lookback)
        var = recent_returns.quantile(1 - self.confidence_level)
        return var
        
    def calculate_parametric_var(self, returns_series: pd.Series):
        """Calculates VaR assuming normal distribution."""
        if len(returns_series) < 2:
            return -0.05
        mean = returns_series.mean()
        std = returns_series.std()
        
        # Approximate z-scores to avoid scipy dependency
        if self.confidence_level >= 0.99:
            z_score = -2.33
        elif self.confidence_level >= 0.95:
            z_score = -1.645
        elif self.confidence_level >= 0.90:
            z_score = -1.28
        else:
            z_score = -1.645
            
        var = mean + z_score * std
        return var

    def calculate_drawdown(self, portfolio_values: pd.Series):
        """Calculates the current drawdown of the portfolio."""
        rolling_max = portfolio_values.expanding().max()
        drawdown = (portfolio_values / rolling_max) - 1.0
        return drawdown.iloc[-1] if len(drawdown) > 0 else 0.0

class PositionSizer:
    def __init__(self, max_position_size=0.15, target_volatility=0.10):
        self.max_position_size = max_position_size
        self.target_volatility = target_volatility # 10% annualized vol target
        
    def calculate_position_size(self, signal, current_volatility, capital):
        """
        Dynamically sizes position based on current volatility and signal strength.
        Vol Targeting: Position Size = Target Vol / Current Vol
        """
        if current_volatility <= 0 or pd.isna(current_volatility):
            # Fallback size if vol is zero or unknown
            raw_weight = self.max_position_size * 0.5 
        else:
            # Annualize daily vol
            annual_vol = current_volatility * np.sqrt(252)
            if annual_vol == 0:
                raw_weight = 0
            else:
                vol_scalar = self.target_volatility / annual_vol
                # Base weight modulated by signal (-1 to 1)
                raw_weight = vol_scalar * abs(signal)
            
        # Cap the maximum position size
        final_weight = min(raw_weight, self.max_position_size)
        
        # Determine long/short based on signal sign
        direction = 1 if signal > 0 else (-1 if signal < 0 else 0)
        
        # Calculate target capital to deploy
        position_value = capital * final_weight * direction
        return position_value, final_weight * direction
