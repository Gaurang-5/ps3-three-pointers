import pandas as pd
import numpy as np

class FeatureEngineer:
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        
    def add_rolling_volatility(self, window=20):
        """Calculates 20-day rolling standard deviation of equity returns."""
        if 'Equity_Returns' in self.data.columns:
            self.data['Rolling_Vol_20'] = self.data['Equity_Returns'].rolling(window).std()
            self.data['Rolling_Vol_20'] = self.data['Rolling_Vol_20'].bfill()
        return self
        
    def add_momentum_rsi(self, window=14):
        """Calculates Relative Strength Index (RSI)."""
        if 'Equity_Price' in self.data.columns:
            delta = self.data['Equity_Price'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            
            # Avoid division by zero
            loss = loss.replace(0, np.nan)
            rs = gain / loss
            self.data['RSI_14'] = 100 - (100 / (1 + rs))
            self.data['RSI_14'] = self.data['RSI_14'].fillna(50) # Neutral RSI if division by zero
        return self
        
    def add_macro_alignment(self):
        """Creates a composite macro score based on Sentiment, Inflation, and USD Index."""
        macro_features = ['Sentiment', 'Inflation', 'USD_Index']
        
        for feature in macro_features:
            if feature in self.data.columns:
                mean = self.data[feature].mean()
                std = self.data[feature].std()
                if std > 0:
                    self.data[f'{feature}_Norm'] = (self.data[feature] - mean) / std
                else:
                    self.data[f'{feature}_Norm'] = 0
                    
        # Construct Macro Score: Positive Sentiment is bullish, high inflation/USD is generally bearish for equities
        self.data['Macro_Score'] = (
            self.data.get('Sentiment_Norm', 0) 
            - self.data.get('Inflation_Norm', 0) * 0.5 
            - self.data.get('USD_Index_Norm', 0) * 0.5
        )
        return self

    def add_moving_averages(self):
        """Adds long-term and short-term moving averages."""
        if 'Equity_Price' in self.data.columns:
            self.data['SMA_50'] = self.data['Equity_Price'].rolling(50).mean().bfill()
            self.data['SMA_200'] = self.data['Equity_Price'].rolling(200).mean().bfill()
        return self
        
    def generate_all_features(self):
        """Executes all feature engineering pipelines."""
        self.add_rolling_volatility()
        self.add_momentum_rsi()
        self.add_macro_alignment()
        self.add_moving_averages()
        
        # Ensure no NaNs remain after feature engineering
        self.data = self.data.ffill().bfill()
        return self.data
