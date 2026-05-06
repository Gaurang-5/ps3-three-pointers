import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataIngestionError(Exception):
    pass

class DataPreprocessor:
    def __init__(self, config_paths):
        self.paths = config_paths
        
    def load_data(self):
        try:
            logger.info("Ingesting datasets...")
            equity_df = pd.read_csv(self.paths['equity_data'], parse_dates=['Date'])
            macro_df = pd.read_csv(self.paths['macro_data'], parse_dates=['Date'])
            multi_asset_df = pd.read_csv(self.paths['multi_asset'], parse_dates=['Date'])
            oil_df = pd.read_csv(self.paths['oil_data'], parse_dates=['Date'])
            
            # Validate basic formats
            for df_name, df in zip(['equity', 'macro', 'multi_asset', 'oil'], [equity_df, macro_df, multi_asset_df, oil_df]):
                if 'Date' not in df.columns:
                    raise DataIngestionError(f"Missing 'Date' column in {df_name} dataset.")
            
            return {
                'equity': equity_df,
                'macro': macro_df,
                'multi_asset': multi_asset_df,
                'oil': oil_df
            }
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise DataIngestionError(f"Data ingestion failed: {e}")
            
    def handle_missing_data(self, df):
        # Forward fill missing values (e.g., weekends, holidays)
        df = df.ffill().bfill()
        return df
        
    def detect_and_handle_outliers(self, df, columns, z_thresh=3.0):
        # Cap extreme outliers to prevent model distortion
        for col in columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    lower_bound = mean - z_thresh * std
                    upper_bound = mean + z_thresh * std
                    df[col] = np.clip(df[col], lower_bound, upper_bound)
        return df

    def prepare_data(self):
        dfs = self.load_data()
        
        # Rename columns to prevent overlap
        dfs['equity'] = dfs['equity'].rename(columns={'Price': 'Equity_Price', 'Volume': 'Equity_Volume', 'Returns': 'Equity_Returns'})
        dfs['oil'] = dfs['oil'].rename(columns={'Price': 'Oil_Price_Raw', 'Volume': 'Oil_Volume_Raw', 'Returns': 'Oil_Returns_Raw'})
        
        # Clean individually
        for key in dfs:
            dfs[key] = self.handle_missing_data(dfs[key])
            numeric_cols = dfs[key].select_dtypes(include=[np.number]).columns
            dfs[key] = self.detect_and_handle_outliers(dfs[key], numeric_cols)
            dfs[key] = dfs[key].sort_values('Date').reset_index(drop=True)
            
        # Merge datasets using Equity as the primary timeline
        merged_df = dfs['equity'].copy()
        
        merged_df = pd.merge(merged_df, dfs['macro'], on='Date', how='left')
        merged_df = pd.merge(merged_df, dfs['multi_asset'], on='Date', how='left')
        merged_df = pd.merge(merged_df, dfs['oil'], on='Date', how='left')
        
        # Final cleanup post-merge
        merged_df = merged_df.ffill().bfill()
        merged_df = merged_df.drop_duplicates(subset=['Date'])
        merged_df = merged_df.set_index('Date')
        
        logger.info(f"Data prepared successfully. Total rows: {len(merged_df)}, Columns: {len(merged_df.columns)}")
        return merged_df
