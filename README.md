# Hedge Fund Risk Modeling & Semi-Automated Trading System

## Overview
This repository contains a production-grade, risk-aware, semi-automated trading system. It is designed to ingest multi-asset market data, generate robust trading signals based on technical and macroeconomic features, and simulate realistic portfolio execution considering transaction costs, slippage, and strict capital constraints.

## System Features
1. **Data Pipeline**: Robust parsing, missing data imputation, and outlier capping.
2. **Feature Engineering**: Calculates rolling volatility, RSI, SMA cross-overs, and a composite Macro Alignment Score.
3. **Risk Management**: Implements Historical VaR, Volatility-Targeted Position Sizing, and Drawdown-based Stop-Losses.
4. **Execution Simulator**: Tracks cash, simulates market friction, and gracefully handles capital shortfalls.
5. **Audit Logging**: Every trade decision is logged to `audit_log.json` for stakeholder transparency.

## Setup & Execution
1. Install requirements: `pip install pandas numpy pyyaml`
2. Run the simulation: `python main.py`
3. View the generated `audit_log.json` and `performance_report.json`.

## Performance Output
Outputs metrics including Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Alpha, and Beta.
