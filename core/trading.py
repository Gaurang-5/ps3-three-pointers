"""
core/trading.py
===============
Stage 8 & 11: Signal Generation and Audit Logging.

Resolves: Issue 8 (Signal Generation Engine), Issue 14 (Explainable Strategy Logs).

The SignalEngine uses a multi-factor composite score to generate buy/sell signals
for any supported asset. The AuditLogger records all decisions to JSONL files.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Tuple, Any

import pandas as pd

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Appends execution decisions, risk events, and data errors to JSONL files.
    Ensures complete transparency for every trading decision (Issue 14).

    Parameters
    ----------
    log_dir : str
        Directory to store the log files.
    """

    def __init__(self, log_dir: str = "./logs") -> None:
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

        self.trade_log_file = os.path.join(self.log_dir, "trade_log.jsonl")
        self.error_log_file = os.path.join(self.log_dir, "error_log.jsonl")

        # Truncate old logs on init
        open(self.trade_log_file, "w").close()
        open(self.error_log_file, "w").close()

        self.counts: Dict[str, int] = {
            "signals_generated": 0,
            "trades_executed": 0,
            "trades_rejected": 0,
            "risk_events": 0,
            "data_errors": 0,
        }

    def _write_jsonl(self, file_path: str, entry: Dict[str, Any]) -> None:
        with open(file_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_signal(
        self,
        date: str,
        ticker: str,
        signal_value: float,
        explanation: str,
        factors: Dict[str, float] = None,
    ) -> None:
        """Logs the rationale behind a generated trading signal."""
        self.counts["signals_generated"] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": str(date),
            "event_type": "SIGNAL",
            "ticker": ticker,
            "signal_value": float(signal_value),
            "reason": explanation,
            "factors": factors or {},
        }
        self._write_jsonl(self.trade_log_file, entry)

    def log_trade(
        self,
        date: str,
        ticker: str,
        action: str,
        shares: float,
        price: float,
        costs: Dict[str, float],
        portfolio_snapshot: Dict[str, float],
    ) -> None:
        """Logs an executed trade, including slippage and commission costs."""
        self.counts["trades_executed"] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": str(date),
            "event_type": "TRADE_EXECUTED",
            "ticker": ticker,
            "action": action,
            "shares": float(shares),
            "price": float(price),
            "costs": {k: float(v) for k, v in costs.items()},
            "portfolio_state": {k: float(v) for k, v in portfolio_snapshot.items()},
        }
        self._write_jsonl(self.trade_log_file, entry)

    def log_rejection(self, date: str, ticker: str, reason: str, details: str) -> None:
        """Logs a trade that was rejected due to constraints (e.g., insufficient capital)."""
        self.counts["trades_rejected"] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": str(date),
            "event_type": "TRADE_REJECTED",
            "ticker": ticker,
            "reason": reason,
            "details": details,
        }
        self._write_jsonl(self.error_log_file, entry)

    def log_risk_event(
        self, date: str, metric: str, value: float, threshold: float
    ) -> None:
        """Logs a circuit breaker or risk limit breach."""
        self.counts["risk_events"] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": str(date),
            "event_type": "RISK_BREACH",
            "metric": metric,
            "value": float(value),
            "threshold": float(threshold),
        }
        self._write_jsonl(self.error_log_file, entry)

    def log_data_error(self, source: str, error: str, record: Any = None) -> None:
        """Logs data anomalies or missing prices."""
        self.counts["data_errors"] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "DATA_ERROR",
            "source": source,
            "error": str(error),
            "record": str(record),
        }
        self._write_jsonl(self.error_log_file, entry)

    def export_summary(self) -> Dict[str, int]:
        """Dumps total counts of all events to summary_log.json."""
        summary_path = os.path.join(self.log_dir, "summary_log.json")
        with open(summary_path, "w") as f:
            json.dump(self.counts, f, indent=4)
        logger.info(f"Exported summary log to {summary_path}")
        return self.counts


class SignalEngine:
    """
    Generates trading signals using technical and macro features.

    Parameters
    ----------
    config : dict
        Configuration loaded from config.yaml.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}

    def generate_signals(
        self, row: pd.Series, prefix: str = "Equity_"
    ) -> Tuple[float, str, Dict[str, float]]:
        """
        Generates buy/sell/hold signals based on engineered features for a specific asset.

        Parameters
        ----------
        row : pd.Series
            A single row of the feature-engineered market data.
        prefix : str
            The column prefix for the asset (e.g., 'Equity_', 'Oil_').

        Returns
        -------
        tuple
            (signal_value, reason_string, factors_dict)
            Signal value is a float between -1.0 (Strong Sell) and 1.0 (Strong Buy).
        """
        score = 0.0
        reasons = []
        factors = {}

        # Config thresholds
        cfg_sig = self.config.get("signals", {})
        buy_thresh = cfg_sig.get("buy_threshold", 0.3)
        sell_thresh = cfg_sig.get("sell_threshold", -0.3)
        rsi_os = cfg_sig.get("rsi_oversold", 35)
        rsi_ob = cfg_sig.get("rsi_overbought", 65)

        # 1. Momentum (RSI)
        rsi_col = f"{prefix}RSI_14"
        rsi = row.get(rsi_col, 50)
        factors["rsi"] = float(rsi)

        if pd.notna(rsi):
            if rsi > rsi_ob:
                score += 0.2
                reasons.append(f"Strong Momentum (RSI: {rsi:.1f})")
            elif rsi < rsi_os:
                score -= 0.2
                reasons.append(f"Weak Momentum (RSI: {rsi:.1f})")

        # 2. Trend Alignment (SMA Cross)
        sma50_col = f"{prefix}SMA_50"
        sma200_col = f"{prefix}SMA_200"

        sma50 = row.get(sma50_col)
        sma200 = row.get(sma200_col)
        price = row.get(f"{prefix}Price")

        if pd.notna(sma50) and pd.notna(sma200) and pd.notna(price):
            if sma50 > sma200 and price > sma50:
                score += 0.6
                reasons.append("Bullish Trend")
            elif sma50 < sma200 and price < sma50:
                score -= 0.6
                reasons.append("Bearish Trend")

        # 2b. Momentum Confirmation
        mom10 = row.get(f"{prefix}Momentum_10d", 0.0)
        mom30 = row.get(f"{prefix}Momentum_30d", 0.0)
        factors["mom_10d"] = float(mom10) if pd.notna(mom10) else 0.0
        factors["mom_30d"] = float(mom30) if pd.notna(mom30) else 0.0
        if pd.notna(mom10) and pd.notna(mom30):
            if mom10 > 0 and mom30 > 0:
                score += 0.2
                reasons.append("Positive Momentum")
            elif mom10 < 0 and mom30 < 0:
                score -= 0.2
                reasons.append("Negative Momentum")

        # 3. Macro Alignment (Global across assets)
        macro_score = row.get("Macro_Score", 0.5)
        factors["macro_score"] = float(macro_score)

        if pd.notna(macro_score):
            if macro_score > 0.6:
                score += 0.1
                reasons.append(f"Favorable Macro ({macro_score:.2f})")
            elif macro_score < 0.4:
                score -= 0.1
                reasons.append(f"Unfavorable Macro ({macro_score:.2f})")

        # Clip score
        final_signal = max(min(score, 1.0), -1.0)

        # 4. Volatility Filter
        vol_col = f"{prefix}Rolling_Vol_20"
        vol = row.get(vol_col, 0.0)
        factors["volatility"] = float(vol)

        if pd.notna(vol) and vol > 0.03:
            final_signal = 0.0
            reasons.append("Extreme Volatility - Holding Cash")

        reason_str = " | ".join(reasons) if reasons else "Neutral conditions"

        # Apply directional thresholds
        if sell_thresh > buy_thresh:
            # Defensive fallback for invalid config
            final_signal = 0.0
        elif sell_thresh < final_signal < buy_thresh:
            final_signal = 0.0

        factors["composite_score"] = float(final_signal)

        return final_signal, reason_str, factors
