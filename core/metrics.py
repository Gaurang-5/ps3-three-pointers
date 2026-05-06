import pandas as pd
import numpy as np

class PerformanceMetrics:
    def __init__(self, portfolio_df: pd.DataFrame, benchmark_returns: pd.Series, risk_free_rate=0.02):
        self.df = portfolio_df.copy()
        if 'Date' in self.df.columns:
            self.df = self.df.set_index('Date')
            
        self.df['Daily_Return'] = self.df['Total_Value'].pct_change().fillna(0)
        self.returns = self.df['Daily_Return']
        self.benchmark_returns = benchmark_returns
        self.rf = risk_free_rate
        self.daily_rf = (1 + self.rf) ** (1/252) - 1
        
    def sharpe_ratio(self):
        """Calculates annualized Sharpe Ratio."""
        excess_returns = self.returns - self.daily_rf
        std = excess_returns.std()
        if std == 0 or pd.isna(std):
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / std
        
    def sortino_ratio(self):
        """Calculates annualized Sortino Ratio."""
        excess_returns = self.returns - self.daily_rf
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = downside_returns.std()
        if downside_std == 0 or pd.isna(downside_std):
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / downside_std
        
    def max_drawdown(self):
        """Calculates Maximum Drawdown."""
        cum_returns = (1 + self.returns).cumprod()
        rolling_max = cum_returns.expanding().max()
        drawdown = (cum_returns / rolling_max) - 1.0
        return drawdown.min()
        
    def total_return(self):
        """Calculates total cumulative return."""
        if len(self.df) == 0:
            return 0.0
        start_val = self.df['Total_Value'].iloc[0]
        end_val = self.df['Total_Value'].iloc[-1]
        return (end_val / start_val) - 1.0
        
    def calculate_alpha_beta(self):
        """Calculates Jensen's Alpha and Beta vs Benchmark."""
        aligned = pd.concat([self.returns, self.benchmark_returns], axis=1).dropna()
        if len(aligned) < 2:
            return 0.0, 1.0
            
        port_ret = aligned.iloc[:, 0]
        bench_ret = aligned.iloc[:, 1]
        
        covariance = np.cov(port_ret, bench_ret)[0, 1]
        variance = np.var(bench_ret)
        
        if variance == 0:
            beta = 1.0
        else:
            beta = covariance / variance
            
        # Annualized Alpha
        annual_port_ret = port_ret.mean() * 252
        annual_bench_ret = bench_ret.mean() * 252
        alpha = annual_port_ret - (self.rf + beta * (annual_bench_ret - self.rf))
        
        return alpha, beta
        
    def generate_report(self):
        """Generates a summary of all metrics."""
        alpha, beta = self.calculate_alpha_beta()
        return {
            'Total Return': self.total_return(),
            'Sharpe Ratio': self.sharpe_ratio(),
            'Sortino Ratio': self.sortino_ratio(),
            'Max Drawdown': self.max_drawdown(),
            'Alpha': alpha,
            'Beta': beta
        }
