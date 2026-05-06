import yaml
import logging
import pandas as pd
import json
import os
from core.data import DataPreprocessor
from core.features import FeatureEngineer
from core.portfolio import PortfolioManager, InsufficientCapitalError
from core.risk import RiskModeler, PositionSizer
from core.trading import SignalEngine, AuditLogger
from core.metrics import PerformanceMetrics
from core.dashboard import DashboardExporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(path='config.yaml'):
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def run_simulation():
    config = load_config()
    
    # Data & Features Pipeline
    logger.info("--- Phase 1: Data Ingestion & Preprocessing ---")
    preprocessor = DataPreprocessor(config['paths'])
    merged_data = preprocessor.prepare_data()
    
    logger.info("--- Phase 2: Feature Engineering ---")
    fe = FeatureEngineer(merged_data)
    model_data = fe.generate_all_features()
    
    # State Managers Initialization
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
        target_volatility=0.10 # Hardcoded 10% target for stability
    )
    
    signal_engine = SignalEngine(config)
    
    # Set up Log directory
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    audit_logger = AuditLogger(log_dir=log_dir)
    
    # Simulation Loop
    logger.info("--- Phase 3: Trading Simulation ---")
    rebalance_freq = config['trading'].get('rebalance_frequency', 21)
    
    signal_history = []
    
    for i in range(len(model_data)):
        row = model_data.iloc[i]
        date = model_data.index[i]
        
        current_prices = {
            'Equity': row['Equity_Price']
        }
        
        # Real-time risk calculations
        historical_returns = model_data['Equity_Returns'].iloc[:i+1]
        current_var = risk_modeler.calculate_historical_var(historical_returns)
        current_vol = row.get('Rolling_Vol_20', 0.0)
        
        # Determine signals
        signal, reason, factors = signal_engine.generate_signals(row)
        
        signal_history.append({
            'date': str(date),
            'ticker': 'Equity',
            'signal': 'BUY' if signal > 0 else ('SELL' if signal < 0 else 'HOLD'),
            'composite_score': signal
        })
        
        # Periodic Rebalancing
        if i % rebalance_freq == 0:
            audit_logger.log_signal(date, 'Equity', signal, reason, factors)
            
            # Risk Overlay: Hard Stop Loss Check
            if len(pm.history) > 0:
                current_dd = risk_modeler.calculate_drawdown(pd.Series([h['Total_Value'] for h in pm.history]))
                
                # Check for risk breaches
                if current_var < -config['portfolio']['risk_tolerance_var']:
                    audit_logger.log_risk_event(date, "VaR", current_var, -config['portfolio']['risk_tolerance_var'])
                    
                if current_dd < -config['portfolio']['max_drawdown_limit']:
                    signal = 0.0
                    reason = f"Stop Loss Triggered (DD: {current_dd*100:.2f}%)"
                    audit_logger.log_risk_event(date, "Drawdown", current_dd, -config['portfolio']['max_drawdown_limit'])
                    
            # Dynamic Sizing based on Volatility
            total_capital = pm.get_total_value(current_prices)
            target_value, target_weight = position_sizer.calculate_position_size(signal, current_vol, total_capital)
            
            # Execute
            try:
                tx_cost = pm.execute_trade('Equity', target_value, current_prices['Equity'], date)
                
                # Audit Logging
                if tx_cost > 0 or signal == 0: # Log active trades or forced liquidations
                    audit_logger.log_trade(
                        date=date,
                        ticker='Equity',
                        action='BUY' if signal > 0 else ('SELL' if signal < 0 else 'HOLD'),
                        shares=pm.shares.get('Equity', 0.0),
                        price=current_prices['Equity'],
                        costs={"commission": tx_cost, "slippage": tx_cost}, # Approximated here for struct
                        portfolio_snapshot={"cash": pm.cash, "total_value": pm.get_total_value(current_prices)}
                    )
            except InsufficientCapitalError as e:
                audit_logger.log_rejection(date, 'Equity', "INSUFFICIENT_CAPITAL", str(e))
                logger.error(f"Simulation halted due to capital constraint: {e}")
                break
                
        # Daily Mark-to-Market
        pm.update_history(date, current_prices)
        
    audit_logger.export_summary()
    
    # Final Metrics
    logger.info("--- Phase 4: Performance Evaluation ---")
    portfolio_df = pm.get_history_df()
    benchmark_returns = model_data['Equity_Returns'] # Assume Equity asset is benchmark
    
    metrics = PerformanceMetrics(portfolio_df, benchmark_returns, risk_free_rate=config['metrics']['risk_free_rate'])
    report = metrics.generate_report()
    
    logger.info("\n=== Final Performance Report ===")
    for k, v in report.items():
        if 'Ratio' in k or k == 'Beta':
            logger.info(f"{k}: {v:.4f}")
        else:
            logger.info(f"{k}: {v*100:.2f}%")
            
    # Dashboard Export
    logger.info("--- Phase 5: Generating Dashboard Exports ---")
    exporter = DashboardExporter(pm, report, signal_history, output_dir='output')
    exporter.export_all()
        
if __name__ == "__main__":
    run_simulation()
