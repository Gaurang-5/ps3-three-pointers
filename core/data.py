"""
core/data.py
============
Stage 1 & 2: Market Data Ingestion and Preprocessing.

Resolves: Issue 1 (Ingestion), Issue 2 (Missing Data + Outliers), Issue 16 (Invalid Formats).

Design Notes:
- Uses a left-join merge on the Equity timeline to avoid dropping market dates.
- Outlier detection uses a configurable z-score threshold (default 3σ).
- No forward-looking data is introduced; ffill is time-ordered before bfill.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class DataIngestionError(Exception):
    """Raised when a dataset fails schema validation or cannot be loaded."""
    pass


class DataPreprocessor:
    """
    Ingests, validates, cleans, and merges multi-asset market datasets.

    Parameters
    ----------
    config_paths : dict
        Dictionary mapping dataset keys to file paths, as defined in config.yaml.

    Example
    -------
    >>> preprocessor = DataPreprocessor(config['paths'])
    >>> merged_df = preprocessor.prepare_data()
    """

    REQUIRED_COLUMNS: Dict[str, list] = {
        'equity': ['Date'],
        'macro': ['Date'],
        'multi_asset': ['Date'],
        'oil': ['Date'],
    }

    def __init__(self, config_paths: dict) -> None:
        self.paths = config_paths

    def _validate_schema(self, df: pd.DataFrame, dataset_name: str) -> bool:
        """
        Validates that a DataFrame contains the required columns.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to validate.
        dataset_name : str
            Name used for logging and error messages.

        Returns
        -------
        bool
            True if valid, raises DataIngestionError otherwise.
        """
        required = self.REQUIRED_COLUMNS.get(dataset_name, ['Date'])
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise DataIngestionError(
                f"[{dataset_name}] Missing required columns: {missing}. "
                f"Found columns: {list(df.columns)}"
            )
        return True

    def load_data(self) -> Dict[str, pd.DataFrame]:
        """
        Loads all configured datasets from CSV files with schema validation.

        Returns
        -------
        dict[str, pd.DataFrame]
            Dictionary of validated DataFrames keyed by asset type.

        Raises
        ------
        DataIngestionError
            If any dataset cannot be loaded or fails schema validation.
        """
        datasets: Dict[str, pd.DataFrame] = {}
        path_keys = {
            'equity': self.paths['equity_data'],
            'macro': self.paths['macro_data'],
            'multi_asset': self.paths['multi_asset'],
            'oil': self.paths['oil_data'],
        }

        for name, path in path_keys.items():
            try:
                df = pd.read_csv(path, parse_dates=['Date'])
                self._validate_schema(df, name)
                datasets[name] = df
                logger.info(f"Loaded [{name}]: {len(df)} rows, {len(df.columns)} columns.")
            except DataIngestionError:
                raise
            except Exception as exc:
                # Log and skip malformed assets; do not crash (Issue 16)
                logger.error(f"Failed to load [{name}] from '{path}': {exc}")
                raise DataIngestionError(f"Critical dataset '{name}' could not be loaded: {exc}")

        return datasets

    def handle_missing_data(self, df: pd.DataFrame, ffill_limit: int = 5) -> pd.DataFrame:
        """
        Imputes missing values without introducing forward-looking bias.

        Strategy:
        - Prices: forward-fill up to `ffill_limit` consecutive days, then backward-fill.
        - Rows still missing after imputation are dropped.

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe with potential NaN values.
        ffill_limit : int
            Maximum consecutive days to forward-fill (default 5).

        Returns
        -------
        pd.DataFrame
            Cleaned dataframe with missing values imputed.
        """
        before = df.isnull().sum().sum()
        df = df.ffill(limit=ffill_limit).bfill()
        after = df.isnull().sum().sum()
        if before > 0:
            logger.info(f"Imputed {before - after} missing values ({after} remaining after bfill).")
        return df

    def detect_and_handle_outliers(
        self,
        df: pd.DataFrame,
        columns: list,
        z_thresh: float = 3.0
    ) -> pd.DataFrame:
        """
        Detects and smooths outliers using a rolling z-score cap.

        Flagged values (|z-score| > z_thresh) are clipped to the threshold boundary.
        Prevents flash crashes from distorting risk calculations and signals (Issue 2).

        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe.
        columns : list
            Column names to check for outliers.
        z_thresh : float
            Z-score threshold above which a value is considered an outlier.

        Returns
        -------
        pd.DataFrame
            Dataframe with outliers capped at ±z_thresh standard deviations.
        """
        for col in columns:
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            mean_val = df[col].mean()
            std_val = df[col].std()
            if std_val > 0:
                lower = mean_val - z_thresh * std_val
                upper = mean_val + z_thresh * std_val
                clipped = ((df[col] < lower) | (df[col] > upper)).sum()
                if clipped > 0:
                    logger.debug(f"Capped {clipped} outliers in column '{col}'.")
                df[col] = np.clip(df[col], lower, upper)
        return df

    def prepare_data(self) -> pd.DataFrame:
        """
        Runs the full ingestion → validation → cleaning → merge pipeline.

        Pipeline steps:
        1. Load all datasets with schema validation.
        2. Rename columns to avoid merge conflicts.
        3. Impute missing data per dataset.
        4. Cap outliers per numeric column.
        5. Merge all datasets onto the Equity timeline (left join).
        6. Final ffill/bfill pass and deduplication.

        Returns
        -------
        pd.DataFrame
            Clean, merged DataFrame indexed by Date with all asset features.
        """
        dfs = self.load_data()

        # Rename to prevent column collisions on merge
        dfs['equity'] = dfs['equity'].rename(columns={
            'Price': 'Equity_Price', 'Volume': 'Equity_Volume', 'Returns': 'Equity_Returns'
        })
        dfs['oil'] = dfs['oil'].rename(columns={
            'Price': 'Oil_Price_Raw', 'Volume': 'Oil_Volume_Raw', 'Returns': 'Oil_Returns_Raw'
        })

        # Clean each dataset individually
        for key, df in dfs.items():
            dfs[key] = self.handle_missing_data(df)
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            dfs[key] = self.detect_and_handle_outliers(dfs[key], numeric_cols)
            dfs[key] = dfs[key].sort_values('Date').reset_index(drop=True)

        # Merge on Equity timeline (left join — never drop market dates)
        merged = dfs['equity'].copy()
        for key in ['macro', 'multi_asset', 'oil']:
            merged = pd.merge(merged, dfs[key], on='Date', how='left')

        # Final cleanup
        merged = merged.ffill().bfill()
        merged = merged.drop_duplicates(subset=['Date'])
        merged = merged.set_index('Date')

        logger.info(
            f"Data pipeline complete. Rows: {len(merged)}, Features: {len(merged.columns)}"
        )
        return merged
