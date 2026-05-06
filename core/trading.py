import pandas as pd
import numpy as np
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class AuditLogger:
    def __init__(self, log_dir='./'):
        self.log_dir = log_dir
        self.trade_log_file = os.path.join(log_dir, 'trade_log.jsonl')
        self.error_log_file = os.path.join(log_dir, 'error_log.jsonl')
        
        # Clear old logs
        open(self.trade_log_file, 'w').close()
        open(self.error_log_file, 'w').close()
        
        self.counts = {
            'signals_generated': 0,
            'trades_executed': 0,
            'trades_rejected': 0,
            'risk_events': 0,
            'data_errors': 0
        }
        
    def _write_jsonl(self, file_path, entry):
        with open(file_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
            
    def log_signal(self, date, ticker, signal_value, explanation, factors=None):
        self.counts['signals_generated'] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": str(date),
            "event_type": "SIGNAL",
            "ticker": ticker,
            "signal_value": signal_value,
            "reason": explanation,
            "factors": factors or {}
        }
        self._write_jsonl(self.trade_log_file, entry)

    def log_trade(self, date, ticker, action, shares, price, costs, portfolio_snapshot):
        self.counts['trades_executed'] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": str(date),
            "event_type": "TRADE_EXECUTED",
            "ticker": ticker,
            "action": action,
            "shares": shares,
            "price": price,
            "costs": costs,
            "portfolio_state": portfolio_snapshot
        }
        self._write_jsonl(self.trade_log_file, entry)

    def log_rejection(self, date, ticker, reason, details):
        self.counts['trades_rejected'] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": str(date),
            "event_type": "TRADE_REJECTED",
            "ticker": ticker,
            "reason": reason,
            "details": details
        }
        self._write_jsonl(self.error_log_file, entry)

    def log_risk_event(self, date, metric, value, threshold):
        self.counts['risk_events'] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "date": str(date),
            "event_type": "RISK_BREACH",
            "metric": metric,
            "value": value,
            "threshold": threshold
        }
        self._write_jsonl(self.error_log_file, entry)

    def log_data_error(self, source, error, record=None):
        self.counts['data_errors'] += 1
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "DATA_ERROR",
            "source": source,
            "error": str(error),
            "record": record
        }
        self._write_jsonl(self.error_log_file, entry)

    def export_summary(self):
        summary_path = os.path.join(self.log_dir, 'summary_log.json')
        with open(summary_path, 'w') as f:
            json.dump(self.counts, f, indent=4)
        logger.info(f"Exported summary log to {summary_path}")
        return self.counts

class SignalEngine:
    def __init__(self, config=None):
        self.config = config or {}
        
    def generate_signals(self, row: pd.Series):
        """
        Generates buy/sell/hold signals based on engineered features.
        Returns a float between -1.0 (Strong Sell) and 1.0 (Strong Buy), and a reason string.
        """
        score = 0.0
        reasons = []
        factors = {}
        
        # 1. Momentum (RSI)
        rsi = row.get('RSI_14', 50)
        factors['rsi'] = rsi
        if rsi < 35:
            score += 0.4
            reasons.append(f"RSI Oversold ({rsi:.1f})")
        elif rsi > 65:
            score -= 0.4
            reasons.append(f"RSI Overbought ({rsi:.1f})")
            
        # 2. Trend Alignment (SMA Cross)
        sma50 = row.get('SMA_50')
        sma200 = row.get('SMA_200')
        price = row.get('Equity_Price')
        
        if pd.notna(sma50) and pd.notna(sma200):
            if sma50 > sma200 and price > sma50:
                score += 0.3
                reasons.append("Bullish Trend")
            elif sma50 < sma200 and price < sma50:
                score -= 0.3
                reasons.append("Bearish Trend")
                
        # 3. Macro Alignment
        macro_score = row.get('Macro_Score', 0)
        factors['macro_score'] = macro_score
        if macro_score > 0.6:
            score += 0.1
            reasons.append(f"Favorable Macro ({macro_score:.2f})")
        elif macro_score < 0.4:
            score -= 0.1
            reasons.append(f"Unfavorable Macro ({macro_score:.2f})")
            
        # Clip score between -1 and 1
        final_signal = max(min(score, 1.0), -1.0)
        
        # 4. Volatility Filter
        vol = row.get('Rolling_Vol_20', 0)
        factors['volatility'] = vol
        if vol > 0.03: 
            final_signal = 0.0
            reasons.append("Extreme Volatility - Holding Cash")
            
        reason_str = " | ".join(reasons) if reasons else "Neutral conditions"
        
        # Thresholds
        if abs(final_signal) < 0.3:
            final_signal = 0.0
            
        factors['composite_score'] = final_signal
            
        return final_signal, reason_str, factors
