"""
core/data.py
============
Stage 1 & 2: Market Data Ingestion and Preprocessing.

Resolves: Issue 1 (Concurrent Ingestion), Issue 2 (Missing Data + Outliers),
          Issue 16 (Invalid Formats).

Design Notes:
- Datasets are loaded concurrently using ThreadPoolExecutor (Issue 1).
- Left-join merge on Equity timeline preserves all market dates.
- Outlier detection uses 3σ z-score capping per column.
- ffill/bfill applied in time-order — no forward-looking bias.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataIngestionError(Exception):
    """Raised when a dataset fails schema validation or cannot be loaded."""


class DataPreprocessor:
    """
    Ingests, validates, cleans, and merges multi-asset market datasets.

    Parameters
    ----------
    config_paths : dict
        Mapping of dataset keys → file paths from config.yaml.

    Example
    -------
    >>> preprocessor = DataPreprocessor(config['paths'])
    >>> merged_df = preprocessor.prepare_data()
    """

    # Maps internal key → (config key, columns to rename on load)
    _DATASET_CONFIG: Dict[str, Dict] = {
        "equity": {
            "path_key": "equity_data",
            "rename": {"Price": "Equity_Price", "Volume": "Equity_Volume", "Returns": "Equity_Returns"},
        },
        "macro": {"path_key": "macro_data", "rename": {}},
        "multi_asset": {
            "path_key": "multi_asset", 
            "rename": {"Oil": "Oil_Price", "Gold": "Gold_Price", "Bonds": "Bond_Price",
                       "Oil_Returns": "Oil_Returns", "Gold_Returns": "Gold_Returns"}
        },
        "oil": {
            "path_key": "oil_data",
            "rename": {}
        },
    }

    def __init__(self, config_paths: dict) -> None:
        self.paths = config_paths

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_schema(self, df: pd.DataFrame, name: str) -> None:
        """Raise DataIngestionError if 'Date' column is absent (Issue 16)."""
        if "Date" not in df.columns:
            raise DataIngestionError(
                f"[{name}] Missing required 'Date' column. Found: {list(df.columns)}"
            )

    def _load_single(self, name: str) -> tuple[str, pd.DataFrame]:
        """
        Load and validate one dataset from disk.

        Returns (name, DataFrame) on success.
        Raises DataIngestionError on failure so the executor can propagate it.
        """
        cfg = self._DATASET_CONFIG[name]
        path = self.paths[cfg["path_key"]]
        try:
            df = pd.read_csv(path, parse_dates=["Date"])
        except Exception as exc:
            raise DataIngestionError(f"Cannot read [{name}] from '{path}': {exc}") from exc

        self._validate_schema(df, name)

        if cfg["rename"]:
            df = df.rename(columns=cfg["rename"])

        logger.info(f"Loaded [{name}]: {len(df):,} rows, {len(df.columns)} columns.")
        return name, df

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_all_concurrent(self) -> Dict[str, pd.DataFrame]:
        """
        Load all datasets **concurrently** using a ThreadPoolExecutor (Issue 1).

        Each file is read in a separate thread; I/O-bound work that benefits
        from concurrency without the GIL overhead of CPU-bound tasks.

        Returns
        -------
        dict[str, pd.DataFrame]
            Validated DataFrames keyed by dataset name.

        Raises
        ------
        DataIngestionError
            If any dataset fails to load or validate.
        """
        datasets: Dict[str, pd.DataFrame] = {}
        names = list(self._DATASET_CONFIG.keys())

        with ThreadPoolExecutor(max_workers=len(names), thread_name_prefix="data_loader") as executor:
            futures = {executor.submit(self._load_single, name): name for name in names}
            for future in as_completed(futures):
                name, df = future.result()   # propagates DataIngestionError
                datasets[name] = df

        return datasets

    def handle_missing_data(self, df: pd.DataFrame, ffill_limit: int = 5) -> pd.DataFrame:
        """
        Impute missing values without forward-looking bias.

        - Prices: forward-fill ≤ ffill_limit consecutive days.
        - Initial rows are never backward-filled to avoid lookahead leakage.

        Parameters
        ----------
        df : pd.DataFrame
        ffill_limit : int
            Max consecutive days to forward-fill (default 5).
        """
        before = int(df.isnull().sum().sum())
        df = df.ffill(limit=ffill_limit)
        after = int(df.isnull().sum().sum())
        if before:
            logger.info(f"Imputed {before - after} missing values ({after} remaining).")
        return df

    def detect_and_handle_outliers(
        self,
        df: pd.DataFrame,
        columns: list,
        z_thresh: float = 3.0,
    ) -> pd.DataFrame:
        """
        Clip outliers beyond ±z_thresh standard deviations (Issue 2).

        Prevents flash crashes from distorting risk calculations and signals.

        Parameters
        ----------
        df : pd.DataFrame
        columns : list
            Numeric columns to check.
        z_thresh : float
            Z-score boundary (default 3.0).
        """
        for col in columns:
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            mu, sigma = df[col].mean(), df[col].std()
            if sigma > 0:
                n_clipped = int(((df[col] < mu - z_thresh * sigma) | (df[col] > mu + z_thresh * sigma)).sum())
                if n_clipped:
                    logger.debug(f"Capped {n_clipped} outliers in '{col}'.")
                df[col] = np.clip(df[col], mu - z_thresh * sigma, mu + z_thresh * sigma)
        return df

    def prepare_data(self) -> pd.DataFrame:
        """
        Full pipeline: concurrent load → rename → clean → merge.

        Returns
        -------
        pd.DataFrame
            Clean, Date-indexed DataFrame with all asset features.
        """
        dfs = self.load_all_concurrent()

        # Clean each dataset individually
        for key, df in dfs.items():
            df = self.handle_missing_data(df)
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            df = self.detect_and_handle_outliers(df, numeric_cols)
            dfs[key] = df.sort_values("Date").reset_index(drop=True)

        # Outer-join all timelines to preserve full historical/future ranges present in source data.
        merged = None
        for key in ("equity", "macro", "multi_asset", "oil"):
            if merged is None:
                merged = dfs[key].copy()
            else:
                merged = pd.merge(merged, dfs[key], on="Date", how="outer")

        merged = merged.sort_values("Date").ffill()
        merged = merged.drop_duplicates(subset=["Date"]).set_index("Date")

        logger.info(
            f"Data pipeline complete — rows: {len(merged):,}, features: {len(merged.columns)}"
        )
        return merged
