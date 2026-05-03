# TradeGuard Engine

TradeGuard Engine is a C++20 multi-symbol trading signal and risk engine with a Python analytics layer. It ingests tick-level market data, builds candles, detects confirmed momentum setups, applies risk controls, logs every decision, benchmarks runtime performance, and generates trading performance reports.

## Why This Project Exists

Trading systems are not just about finding entries. A real decision engine must decide whether a trade should be accepted or rejected based on position size, stop distance, daily loss limits, symbol exposure, portfolio exposure, and execution rules.

## Features

- Multi-symbol CSV market data ingestion
- Candle construction from tick streams
- Momentum signal detection
- Moving average confirmation
- Volume confirmation
- Volatility filter
- Risk-based position sizing
- Stop-loss and take-profit calculation
- Max daily loss protection
- Symbol exposure limits
- Portfolio exposure limits
- Open/closed exposure tracking
- Structured trade rejection reason codes
- Backtest simulation
- Decision, trade, and equity logging
- Runtime risk configuration through JSON
- Summary JSON export
- Latency benchmark report
- C++ unit tests
- GitHub Actions CI
- Python performance analytics
- Strategy optimization script

## Tech Stack

Core Engine: C++20, CMake, STL data structures, config-driven risk engine, file-based market data ingestion, backtesting engine.

Analytics: Python, pandas, matplotlib.

DevOps: GitHub Actions CI.

## CLI Usage

Show help:

    ./build/tradeguard --help

Run the engine:

    ./build/tradeguard data/sample_ticks.csv output config/risk_config.json

## Run Locally

Generate sample data:

    python3 python_analytics/generate_sample_data.py

Build the C++ engine:

    cmake -S cpp_engine -B build
    cmake --build build

Run tests:

    ./build/tradeguard_tests

Run the backtest:

    ./build/tradeguard data/sample_ticks.csv output config/risk_config.json

Generate analytics report:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r python_analytics/requirements.txt
    python python_analytics/report.py

Run strategy optimization:

    python python_analytics/optimize_strategy.py

## Output Artifacts

- output/decisions.csv
- output/trades.csv
- output/equity_curve.csv
- output/summary.json
- output/benchmark_report.txt
- output/performance_summary.md
- output/equity_curve.png
- output/pnl_distribution.png
- output/rejection_reasons.png
- output/symbol_pnl.png
- output/symbol_decision_mix.png
- output/optimization_results.csv

## Resume Bullet

Built TradeGuard Engine, a C++20 multi-symbol trading and risk engine with config-driven strategy execution, structured trade rejection reason codes, portfolio and symbol exposure controls, open-position exposure tracking, latency benchmarking, unit-tested signal/risk modules, GitHub Actions CI, and Python analytics for equity curves, PnL distribution, rejection analysis, symbol performance, and strategy optimization.

## Future Improvements

- Live WebSocket market data ingestion
- Order book simulation
- Multi-session risk reset
- Slippage and transaction cost modeling
- More advanced strategy optimization
- Lightweight dashboard frontend
