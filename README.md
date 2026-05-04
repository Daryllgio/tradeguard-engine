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


## Dashboard Frontend

A lightweight static dashboard is included in the `dashboard/` folder. It visualizes the latest engine outputs, including summary metrics, benchmark results, trade decisions, and optimization results.

Run locally:

    python3 -m http.server 9000

Then open:

    http://localhost:9000/dashboard/

Before opening the dashboard, regenerate engine outputs:

    ./build/tradeguard data/sample_ticks.csv output config/risk_config.json
    python python_analytics/report.py
    python python_analytics/optimize_strategy.py

Then copy dashboard data:

    cp output/summary.json dashboard/data/summary.json
    cp output/benchmark_report.txt dashboard/data/benchmark_report.txt
    cp output/performance_summary.md dashboard/data/performance_summary.md
    cp output/decisions.csv dashboard/data/decisions.csv
    cp output/trades.csv dashboard/data/trades.csv
    cp output/optimization_results.csv dashboard/data/optimization_results.csv


## Architecture

TradeGuard is structured as a multi-layer trading operations platform:

    C++20 Trading / Risk Engine
            |
            | writes decisions, trades, equity curve, benchmark reports
            v
    Python Analytics Layer
            |
            | generates reports, charts, optimization results
            v
    FastAPI Control API
            |
            | serves live endpoints and triggers engine runs
            v
    React + TypeScript Dashboard

The broker layer is adapter-based:

    BrokerAdapter
      - SimulatedBrokerAdapter
      - AlpacaBrokerAdapter

The system currently runs in simulated paper mode by default. Alpaca paper trading support is adapter-ready but not enabled until API keys are configured.

## API Endpoints

    GET  /api/health
    GET  /api/summary
    GET  /api/decisions
    GET  /api/trades
    GET  /api/risk
    GET  /api/optimization
    GET  /api/benchmark
    GET  /api/broker
    GET  /api/live/status
    POST /api/live/start
    POST /api/live/stop
    POST /api/run-engine
    POST /api/run-optimization

## Run Full Platform Locally

Terminal 1:

    ./run_api.sh

Terminal 2:

    ./run_dashboard.sh

Then open:

    http://localhost:5173/


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


## Implemented Advanced Features

- Multi-symbol market data ingestion
- Config-driven risk engine
- Structured trade rejection reason codes
- Portfolio and symbol exposure controls
- Open-position exposure tracking
- Latency benchmark reporting
- Python analytics reporting
- Strategy optimization script
- Lightweight dashboard frontend

## Remaining Future Improvements

- Live WebSocket market data ingestion
- Order book simulation
- Multi-session risk reset
- Slippage and transaction cost modeling
