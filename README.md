# TradeGuard Engine

TradeGuard Engine is an automated paper-trading platform that connects a C++ signal/risk engine, a Python analytics layer, a FastAPI backend, a React dashboard, and Alpaca Paper Trading.

The platform is designed to show a full trading workflow: market data generation, signal evaluation, risk filtering, order routing, paper execution, portfolio tracking, performance analytics, and live dashboard monitoring.

## Live Demo

- Frontend Dashboard: https://project-rkyo8.vercel.app
- Backend API: https://tradeguard-engine.onrender.com/api/health

> The dashboard is connected to a live FastAPI backend hosted on Render. Alpaca integration uses paper trading only.

## What TradeGuard Does

TradeGuard simulates and monitors an automated trading system end to end.

When the system is running, it:

1. Generates market input for supported symbols.
2. Runs the C++ trading engine against the latest market data.
3. Classifies each setup as accepted or rejected.
4. Routes accepted paper-trading signals through the backend.
5. Sends paper orders to Alpaca Paper Trading.
6. Tracks paper cash, equity, market value, positions, and order history.
7. Displays performance, risk, strategy, and execution data in a live dashboard.

## Core Features

### Automated Signal Engine

The trading engine evaluates market conditions and produces structured decisions with:

- Symbol
- Timestamp
- Long/short signal
- Entry price
- Stop loss
- Take profit
- Quantity
- Risk amount
- Acceptance or rejection reason

### Risk Management

TradeGuard includes a risk layer that evaluates:

- Risk per trade
- Stop-loss configuration
- Take-profit configuration
- Rejection reasons
- Symbol-level exposure
- Trade eligibility

### Alpaca Paper Trading Integration

The backend connects to Alpaca Paper Trading and can submit paper market orders from accepted engine signals.

The integration supports:

- Paper account status
- Buying power
- Cash and equity
- Submitted paper orders
- Broker positions
- Market snapshots

### Live Dashboard

The dashboard shows:

- Paper equity
- Unrealized P/L
- Paper cash
- Open positions
- Paper fills
- Backend cycles
- Market cycles
- Signals found
- Orders submitted
- Latest paper fills
- Current paper positions
- Market input
- Execution log

### Strategy Lab

The Strategy Lab displays optimization results across different risk, stop-loss, and take-profit configurations.

It ranks strategy settings using:

- Total P/L
- Ending equity
- Win rate
- Max drawdown
- Strategy score

### Trade Blotter

The Trade Blotter provides a searchable and filterable view of engine decisions and paper-trading activity.

## Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Recharts
- CSS dashboard UI

### Backend

- FastAPI
- Python
- Uvicorn
- Alpaca Paper Trading API
- Pandas

### Trading Engine

- C++
- CMake

### Analytics

- Python
- CSV outputs
- Strategy optimization
- Performance summaries

### Deployment

- Frontend: Vercel
- Backend: Render
- Broker: Alpaca Paper Trading

## Project Structure

```text
tradeguard-engine/
├── api/                  # FastAPI backend and broker integration
├── cpp_engine/            # C++ trading engine
├── python_analytics/      # Reporting and optimization scripts
├── dashboard/             # React/Vite frontend
├── config/                # Risk and optimization configs
├── data/                  # Market input data
├── output/                # Generated engine, analytics, and paper-trading outputs
└── README.md
