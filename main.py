import os
import yaml
import logging
import pandas as pd
from typing import Dict, Any

from core.data import DataPreprocessor
from core.features import FeatureEngineer
from core.portfolio import PortfolioManager, InsufficientCapitalError
from core.risk import RiskModeler, PositionSizer
from core.trading import SignalEngine, AuditLogger
from core.metrics import PerformanceMetrics
from core.dashboard import DashboardExporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(path='config.yaml') -> Dict[str, Any]:
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def run_simulation() -> None:
    config = load_config()
    
    # ---------------------------------------------------------
    # Phase 1 & 2: Data & Features
    # ---------------------------------------------------------
    logger.info("--- Phase 1: Data Ingestion & Preprocessing ---")
    preprocessor = DataPreprocessor(config['paths'])
    merged_data = preprocessor.prepare_data()
    
    logger.info("--- Phase 2: Feature Engineering ---")
    fe = FeatureEngineer(merged_data)
    model_data = fe.generate_all_features()
    
    # ---------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------
    pm = PortfolioManager(
        initial_capital=config['portfolio']['initial_capital'],
        transaction_cost_pct=config['trading']['commission_rate'],
        slippage_pct=config['trading']['base_slippage']
    )
    
    risk_modeler = RiskModeler(
        confidence_level=config['risk']['var_confidence'],
        lookback=config['risk']['var_lookback_days']
    )
    
    position_sizer = PositionSizer(
        max_position_size=config['portfolio']['max_position_pct'],
        target_volatility=0.10
    )
    
    signal_engine = SignalEngine(config)
    
    os.makedirs('logs', exist_ok=True)
    audit_logger = AuditLogger(log_dir='logs')
    
    # ---------------------------------------------------------
    # Phase 3: Trading Simulation
    # ---------------------------------------------------------
    logger.info("--- Phase 3: Trading Simulation (Multi-Asset) ---")
    rebalance_freq = config['trading'].get('rebalance_frequency', 21)
    drift_threshold = config['trading'].get('drift_threshold', 0.15)
    
    signal_history = []
    assets = ['Equity', 'Oil', 'Gold', 'Bond']
    
    for i in range(len(model_data)):
        row = model_data.iloc[i]
        date = str(model_data.index[i].date())
        
        # 1. Extract current prices for all available assets
        current_prices = {}
        for asset in assets:
            price_col = f'{asset}_Price'
            if price_col in row and pd.notna(row[price_col]):
                current_prices[asset] = row[price_col]
                
        # 2. Daily Risk Overlay
        historical_returns = model_data['Equity_Returns'].iloc[:i+1]
        current_var = risk_modeler.calculate_historical_var(historical_returns)
        
        # Determine if we should trade today (Time-based or Drift-based)
        # Note: If no history exists, we have no portfolio value yet, so we rebalance on day 1.
        target_weights = {asset: 1.0/len(current_prices) for asset in current_prices} if current_prices else {}
        drift_exceeded = len(pm.history) > 0 and pm.should_rebalance(target_weights, current_prices, drift_threshold)
        is_rebalance_day = (i % rebalance_freq == 0) or drift_exceeded
        
        # We always process signals for heatmap generation, even if we don't execute trades
        for asset, price in current_prices.items():
            signal, reason, factors = signal_engine.generate_signals(row, prefix=f'{asset}_')
            signal_history.append({
                'date': date,
                'ticker': asset,
                'signal': 'BUY' if signal > 0 else ('SELL' if signal < 0 else 'HOLD'),
                'composite_score': signal
            })
            
            if is_rebalance_day:
                audit_logger.log_signal(date, asset, signal, reason, factors)
                
                # Check circuit breakers
                if len(pm.history) > 0:
                    current_dd = risk_modeler.calculate_drawdown(pd.Series([h['Total_Value'] for h in pm.history]))
                    
                    if current_var < -config['portfolio']['risk_tolerance_var']:
                        audit_logger.log_risk_event(date, "VaR", current_var, -config['portfolio']['risk_tolerance_var'])
                        if signal > 0: signal = 0.0 # Block buys
                        
                    if current_dd < -config['portfolio']['max_drawdown_limit']:
                        signal = 0.0 # Force to cash
                        reason = f"Stop Loss Triggered (DD: {current_dd*100:.2f}%)"
                        audit_logger.log_risk_event(date, "Drawdown", current_dd, -config['portfolio']['max_drawdown_limit'])
                        
                # Sizing
                total_capital = pm.get_total_value(current_prices)
                vol_col = f'{asset}_Rolling_Vol_20'
                current_vol = row.get(vol_col, 0.0)
                
                target_value, _ = position_sizer.calculate_position_size(signal, current_vol, total_capital)
                
                # Execution
                try:
                    tx_cost, shares_traded, exec_price = pm.execute_trade(asset, target_value, price, date)
                    
                    if abs(shares_traded) > 0 or signal == 0:
                        audit_logger.log_trade(
                            date=date, ticker=asset,
                            action='BUY' if shares_traded > 0 else ('SELL' if shares_traded < 0 else 'HOLD'),
                            shares=pm.shares.get(asset, 0.0),
                            price=exec_price,
                            costs={"commission": tx_cost, "slippage": abs(shares_traded * (exec_price - price))},
                            portfolio_snapshot={"cash": pm.cash, "total_value": pm.get_total_value(current_prices)}
                        )
                except InsufficientCapitalError as e:
                    audit_logger.log_rejection(date, asset, "INSUFFICIENT_CAPITAL", str(e))
                    
        # Daily Mark-to-Market
        pm.update_history(date, current_prices)
        
    audit_logger.export_summary()
    
    # ---------------------------------------------------------
    # Phase 4 & 5: Metrics & Exports
    # ---------------------------------------------------------
    logger.info("--- Phase 4: Performance Evaluation ---")
    portfolio_df = pm.get_history_df()
    benchmark_returns = model_data['Equity_Returns']
    
    metrics = PerformanceMetrics(portfolio_df, benchmark_returns, risk_free_rate=config['metrics']['risk_free_rate'])
    report = metrics.generate_report()
    
    logger.info("\n=== Final Performance Report ===")
    for k, v in report.items():
        logger.info(f"{k}: {v:.4f}" if 'Ratio' in k or k == 'Beta' else f"{k}: {v*100:.2f}%")
            
    logger.info("--- Phase 5: Generating Dashboard Exports ---")
    exporter = DashboardExporter(pm, report, signal_history, output_dir='output')
    exporter.export_all()

if __name__ == "__main__":
    run_simulation()
