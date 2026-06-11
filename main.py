import os
import yaml
import logging
import pandas as pd
from typing import Dict, Any

from core.data import DataPreprocessor
from core.features import FeatureEngineer
from core.portfolio import PortfolioManager, InsufficientCapitalError
from core.risk import RiskModeler
from core.trading import SignalEngine, AuditLogger
from core.metrics import PerformanceMetrics
from core.dashboard import DashboardExporter

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config(path="config.yaml") -> Dict[str, Any]:
    with open(path, "r") as file:
        return yaml.safe_load(file)


def _compute_portfolio_risk(
    pm: PortfolioManager, risk_modeler: RiskModeler
) -> tuple[float, float]:
    """Returns (historical_var, current_drawdown) using portfolio history."""
    if len(pm.history) < 2:
        return 0.0, 0.0

    values = pd.Series([h["Total_Value"] for h in pm.history], dtype=float)
    returns = values.pct_change().dropna()
    current_var = (
        risk_modeler.calculate_historical_var(returns) if len(returns) > 0 else 0.0
    )
    current_dd = risk_modeler.calculate_drawdown(values)
    return float(current_var), float(current_dd)


def _build_target_weights(
    signals: Dict[str, float],
    buy_threshold: float,
    sell_threshold: float,
    max_position_pct: float,
    min_cash_pct: float,
    strategic_weights: Dict[str, float] | None = None,
    defensive_weights: Dict[str, float] | None = None,
    core_assets: set[str] | None = None,
    defensive_mode: bool = False,
    defensive_risky_budget: float = 0.25,
) -> Dict[str, float]:
    """
    Builds long-only portfolio weights from multi-asset signals.
    Keeps a baseline allocation so the strategy does not get stuck in all-cash mode.
    """
    if not signals:
        return {}

    base_map = strategic_weights or {
        "Equity": 0.55,
        "Bond": 0.30,
        "Gold": 0.10,
        "Oil": 0.05,
    }
    defensive_map = defensive_weights or {
        "Equity": 0.20,
        "Bond": 0.70,
        "Gold": 0.10,
        "Oil": 0.00,
    }
    core_assets = core_assets or {"Equity", "Bond"}
    active_assets = set(signals)
    raw_scores: Dict[str, float] = {}

    for asset, signal in signals.items():
        base = (
            defensive_map.get(asset, 0.0)
            if defensive_mode
            else base_map.get(asset, 0.0)
        )
        if base <= 0:
            raw_scores[asset] = 0.0
            continue

        if asset in core_assets and not defensive_mode:
            raw_scores[asset] = base
            continue

        if signal <= sell_threshold:
            raw_scores[asset] = base * 0.25
        elif signal >= buy_threshold:
            raw_scores[asset] = base * (1.0 + 0.5 * min(max(signal, 0.0), 1.0))
        else:
            raw_scores[asset] = base

    investable_budget = max(0.0, 1.0 - min_cash_pct)

    if defensive_mode:
        strategic_active = {asset: base_map.get(asset, 0.0) for asset in active_assets}
        defensive_active = {
            asset: defensive_map.get(asset, 0.0) for asset in active_assets
        }
        risky_assets = {
            asset
            for asset in active_assets
            if strategic_active.get(asset, 0.0) > defensive_active.get(asset, 0.0)
        }
        defensive_assets = active_assets - risky_assets
    else:
        risky_assets = set()
        defensive_assets = set()

    total_raw = sum(raw_scores.values())
    if total_raw <= 0:
        return {asset: 0.0 for asset in signals}

    normalized = {
        asset: (score / total_raw) * investable_budget
        for asset, score in raw_scores.items()
    }

    if defensive_mode:
        risk_cap = min(max(0.0, defensive_risky_budget), investable_budget)
        risky_total = sum(normalized.get(asset, 0.0) for asset in risky_assets)
        if risky_total > risk_cap and risky_total > 0:
            scale = risk_cap / risky_total
            excess = 0.0
            for asset in risky_assets:
                old_weight = normalized.get(asset, 0.0)
                normalized[asset] = old_weight * scale
                excess += old_weight - normalized[asset]

            defensive_denom = sum(
                raw_scores.get(asset, 0.0) for asset in defensive_assets
            )
            if defensive_denom > 0:
                for asset in defensive_assets:
                    normalized[asset] = normalized.get(asset, 0.0) + (
                        excess * raw_scores.get(asset, 0.0) / defensive_denom
                    )

    # Cap concentration and redistribute leftover to uncapped assets.
    capped = {
        asset: min(weight, max_position_pct) for asset, weight in normalized.items()
    }
    leftover = investable_budget - sum(capped.values())

    for _ in range(len(capped)):
        if leftover <= 1e-9:
            break
        if defensive_mode:
            eligible = [
                a
                for a in defensive_assets
                if capped.get(a, 0.0) < max_position_pct - 1e-9
                and raw_scores.get(a, 0.0) > 0
            ]
        else:
            eligible = [
                a
                for a in capped
                if capped[a] < max_position_pct - 1e-9 and raw_scores[a] > 0
            ]
        if not eligible:
            break
        denom = sum(raw_scores[a] for a in eligible)
        if denom <= 0:
            break
        distributed = 0.0
        for asset in eligible:
            ideal_add = leftover * (raw_scores[asset] / denom)
            room = max_position_pct - capped[asset]
            add = min(ideal_add, room)
            capped[asset] += add
            distributed += add
        leftover -= distributed
        if distributed <= 1e-9:
            break

    return capped


def run_simulation() -> None:
    config = load_config()

    # ---------------------------------------------------------
    # Phase 1 & 2: Data & Features
    # ---------------------------------------------------------
    logger.info("--- Phase 1: Data Ingestion & Preprocessing ---")
    preprocessor = DataPreprocessor(config["paths"])
    merged_data = preprocessor.prepare_data()

    logger.info("--- Phase 2: Feature Engineering ---")
    fe = FeatureEngineer(merged_data)
    model_data = fe.generate_all_features()

    # ---------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------
    pm = PortfolioManager(
        initial_capital=config["portfolio"]["initial_capital"],
        transaction_cost_pct=config["trading"]["commission_rate"],
        slippage_pct=config["trading"]["base_slippage"],
    )

    risk_modeler = RiskModeler(
        confidence_level=config["risk"]["var_confidence"],
        lookback=config["risk"]["var_lookback_days"],
    )

    signal_engine = SignalEngine(config)

    os.makedirs("logs", exist_ok=True)
    audit_logger = AuditLogger(log_dir="logs")

    # ---------------------------------------------------------
    # Phase 3: Trading Simulation
    # ---------------------------------------------------------
    logger.info("--- Phase 3: Trading Simulation (Multi-Asset) ---")
    rebalance_freq = config["trading"].get("rebalance_frequency", 21)
    drift_threshold = config["trading"].get("drift_threshold", 0.15)
    drawdown_cooldown_days = config["trading"].get(
        "drawdown_cooldown_days", rebalance_freq
    )
    defensive_risky_budget = config["trading"].get("defensive_risky_budget", 0.30)
    drawdown_recovery_buffer = config["trading"].get("drawdown_recovery_buffer", 0.02)
    use_drift_rebalance = config["trading"].get("use_drift_rebalance", False)
    strategic_weights = config["portfolio"].get(
        "strategic_weights", {"Equity": 0.55, "Bond": 0.30, "Gold": 0.10, "Oil": 0.05}
    )
    defensive_weights = config["portfolio"].get(
        "defensive_weights", {"Equity": 0.20, "Bond": 0.70, "Gold": 0.10, "Oil": 0.00}
    )
    core_assets = set(config["portfolio"].get("core_assets", ["Equity", "Bond"]))

    signal_history = []
    assets = ["Equity", "Oil", "Gold", "Bond"]
    drawdown_cooldown_until = -1
    min_cash_pct = config["portfolio"].get("min_cash_pct", 0.05)
    min_cash_reserve = pm.initial_capital * min_cash_pct
    buy_threshold = config.get("signals", {}).get("buy_threshold", 0.3)
    sell_threshold = config.get("signals", {}).get("sell_threshold", -0.3)
    max_position_pct = config["portfolio"]["max_position_pct"]
    var_threshold = config["portfolio"]["risk_tolerance_var"]
    drawdown_limit = config["portfolio"]["max_drawdown_limit"]

    for i in range(len(model_data)):
        row = model_data.iloc[i]
        date = str(model_data.index[i].date())

        # 1. Extract current prices for all available assets
        current_prices = {}
        for asset in assets:
            price_col = f"{asset}_Price"
            if price_col in row and pd.notna(row[price_col]):
                current_prices[asset] = row[price_col]

        # 2. Daily Risk Overlay (portfolio-based, not single-asset proxy)
        current_var, current_dd = _compute_portfolio_risk(pm, risk_modeler)

        # Trigger temporary defensive mode on drawdown breach (instead of permanent cash lock).
        breached_drawdown = current_dd < -drawdown_limit
        if breached_drawdown and i > drawdown_cooldown_until:
            drawdown_cooldown_until = i + drawdown_cooldown_days
            audit_logger.log_risk_event(date, "Drawdown", current_dd, -drawdown_limit)
        elif current_dd > -(drawdown_limit - drawdown_recovery_buffer):
            # Exit cooldown once drawdown meaningfully recovers.
            drawdown_cooldown_until = -1
        in_defensive_mode = i <= drawdown_cooldown_until

        # Determine if we should trade today (time-based and drift-aware).
        baseline_weights = {
            asset: strategic_weights.get(asset, 0.0) for asset in current_prices
        }
        drift_exceeded = (
            use_drift_rebalance
            and len(pm.history) > 0
            and pm.should_rebalance(baseline_weights, current_prices, drift_threshold)
        )
        is_rebalance_day = (i % rebalance_freq == 0) or drift_exceeded

        # We always compute signals for heatmap generation.
        raw_signals: Dict[str, float] = {}
        signal_meta: Dict[str, tuple[str, Dict[str, float]]] = {}
        for asset, _price in current_prices.items():
            signal, reason, factors = signal_engine.generate_signals(
                row, prefix=f"{asset}_"
            )
            raw_signals[asset] = float(signal)
            signal_meta[asset] = (reason, factors)
            signal_history.append(
                {
                    "date": date,
                    "ticker": asset,
                    "signal": (
                        "BUY" if signal > 0 else ("SELL" if signal < 0 else "HOLD")
                    ),
                    "composite_score": signal,
                }
            )

        if is_rebalance_day and current_prices:
            if current_var < -var_threshold:
                audit_logger.log_risk_event(date, "VaR", current_var, -var_threshold)

            # Risk gate: block new buys on VaR breach, keep existing sells allowed.
            gated_signals: Dict[str, float] = {}
            for asset, signal in raw_signals.items():
                reason, factors = signal_meta[asset]
                if current_var < -var_threshold and signal > 0:
                    signal = 0.0
                    reason = f"{reason} | VaR Gate Active"
                gated_signals[asset] = signal
                audit_logger.log_signal(date, asset, signal, reason, factors)

            target_weights = _build_target_weights(
                gated_signals,
                buy_threshold=buy_threshold,
                sell_threshold=sell_threshold,
                max_position_pct=max_position_pct,
                min_cash_pct=min_cash_pct,
                strategic_weights=strategic_weights,
                defensive_weights=defensive_weights,
                core_assets=core_assets,
                defensive_mode=in_defensive_mode,
                defensive_risky_budget=defensive_risky_budget,
            )

            total_capital = pm.get_total_value(current_prices)
            orders = []
            for asset, price in current_prices.items():
                target_value = total_capital * target_weights.get(asset, 0.0)
                current_value = pm.shares.get(asset, 0.0) * price
                orders.append(
                    (asset, price, target_value, target_value - current_value)
                )

            # Execute sells first so buys can use released cash.
            orders.sort(key=lambda x: x[3])

            for asset, price, target_value, _value_delta in orders:

                try:
                    tx_cost, shares_traded, exec_price = pm.execute_trade(
                        asset,
                        target_value,
                        price,
                        date,
                        min_cash_reserve=min_cash_reserve,
                    )

                    if abs(shares_traded) > 0:
                        audit_logger.log_trade(
                            date=date,
                            ticker=asset,
                            action="BUY" if shares_traded > 0 else "SELL",
                            shares=shares_traded,
                            price=exec_price,
                            costs={
                                "commission": tx_cost,
                                "slippage": abs(shares_traded * (exec_price - price)),
                            },
                            portfolio_snapshot={
                                "cash": pm.cash,
                                "total_value": pm.get_total_value(current_prices),
                            },
                        )
                except InsufficientCapitalError as e:
                    audit_logger.log_rejection(
                        date, asset, "INSUFFICIENT_CAPITAL", str(e)
                    )

        # Daily Mark-to-Market
        pm.update_history(date, current_prices)

    audit_logger.export_summary()

    # ---------------------------------------------------------
    # Phase 4 & 5: Metrics & Exports
    # ---------------------------------------------------------
    logger.info("--- Phase 4: Performance Evaluation ---")
    portfolio_df = pm.get_history_df()
    benchmark_returns = model_data["Equity_Returns"]

    metrics = PerformanceMetrics(
        portfolio_df,
        benchmark_returns,
        risk_free_rate=config["metrics"]["risk_free_rate"],
    )
    report = metrics.generate_report()

    logger.info("\n=== Final Performance Report ===")
    for k, v in report.items():
        logger.info(
            f"{k}: {v:.4f}" if "Ratio" in k or k == "Beta" else f"{k}: {v*100:.2f}%"
        )

    logger.info("--- Phase 5: Generating Dashboard Exports ---")
    exporter = DashboardExporter(pm, report, signal_history, output_dir="output")
    exporter.export_all()


if __name__ == "__main__":
    run_simulation()
