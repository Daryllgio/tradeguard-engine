from pathlib import Path
import json
import random
import asyncio
import subprocess
from datetime import datetime
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.brokers import AlpacaBrokerAdapter, BrokerOrder, SimulatedBrokerAdapter

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
ENGINE = ROOT / "build" / "tradeguard"
DATA = ROOT / "data" / "sample_ticks.csv"
CONFIG = ROOT / "config" / "risk_config.json"

EXECUTION_LOG = OUTPUT / "execution_log.json"

PAPER_STATE_FILE = OUTPUT / "paper_state.json"

def default_paper_state():
    return {
        "cash": 100000.0,
        "equity": 100000.0,
        "realized_pnl": 0.0,
        "unrealized_pnl": 0.0,
        "market_value": 0.0,
        "positions": {},
        "orders": [],
        "last_updated_at": None,
    }

def read_paper_state():
    if not PAPER_STATE_FILE.exists():
        state = default_paper_state()
        PAPER_STATE_FILE.write_text(json.dumps(state, indent=2))
        return state
    return json.loads(PAPER_STATE_FILE.read_text())

def write_paper_state(state: dict):
    PAPER_STATE_FILE.write_text(json.dumps(state, indent=2))
    return state

def mark_paper_portfolio_to_market():
    state = read_paper_state()
    prices = MARKET_STATE.get("latest_prices", {}) or {}

    market_value = 0.0
    unrealized = 0.0

    for symbol, position in state.get("positions", {}).items():
        qty = float(position.get("qty", 0))
        avg_price = float(position.get("avg_price", 0))
        current_price = float(prices.get(symbol, position.get("current_price", avg_price)) or avg_price)

        position["current_price"] = current_price
        position["market_value"] = round(qty * current_price, 4)
        position["unrealized_pnl"] = round((current_price - avg_price) * qty, 4)

        market_value += position["market_value"]
        unrealized += position["unrealized_pnl"]

    state["market_value"] = round(market_value, 4)
    state["unrealized_pnl"] = round(unrealized, 4)
    state["equity"] = round(float(state.get("cash", 0)) + market_value, 4)
    state["last_updated_at"] = datetime.utcnow().isoformat()

    return write_paper_state(state)

def execute_internal_paper_fill(decision: dict, broker_fill: dict):
    state = read_paper_state()

    symbol = str(decision.get("symbol", "UNKNOWN"))
    qty = 1
    prices = MARKET_STATE.get("latest_prices", {}) or {}
    fill_price = float(prices.get(symbol, decision.get("entry_price", 0)) or decision.get("entry_price", 0))

    if fill_price <= 0:
        fill_price = float(decision.get("entry_price", 0) or 0)

    cost = fill_price * qty
    state["cash"] = round(float(state.get("cash", 100000.0)) - cost, 4)

    positions = state.setdefault("positions", {})
    existing = positions.get(symbol, {
        "symbol": symbol,
        "qty": 0.0,
        "avg_price": 0.0,
        "current_price": fill_price,
        "market_value": 0.0,
        "unrealized_pnl": 0.0,
    })

    old_qty = float(existing.get("qty", 0))
    old_avg = float(existing.get("avg_price", 0))
    new_qty = old_qty + qty
    new_avg = ((old_qty * old_avg) + cost) / new_qty if new_qty else fill_price

    existing["qty"] = round(new_qty, 4)
    existing["avg_price"] = round(new_avg, 4)
    existing["current_price"] = round(fill_price, 4)
    positions[symbol] = existing

    paper_order = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "side": "BUY",
        "qty": qty,
        "fill_price": round(fill_price, 4),
        "status": "FILLED_INTERNAL",
        "source": "ENGINE_SIGNAL",
        "broker_order_id": broker_fill.get("broker_order_id"),
        "source_decision": decision,
    }

    state.setdefault("orders", []).insert(0, paper_order)
    state["orders"] = state["orders"][:100]

    write_paper_state(state)
    return mark_paper_portfolio_to_market()


def read_execution_log():
    if not EXECUTION_LOG.exists():
        return []
    return json.loads(EXECUTION_LOG.read_text())


def signal_key(decision: dict) -> str:
    return "|".join([
        str(MARKET_STATE.get("cycle_id", 0)),
        str(decision.get("timestamp", "")),
        str(decision.get("symbol", "")),
        str(decision.get("signal", "")),
        str(decision.get("entry_price", "")),
    ])

def executed_signal_keys() -> set[str]:
    keys = set()
    for entry in read_execution_log():
        source = entry.get("source_decision", {})
        key = entry.get("signal_key") or signal_key(source)
        if key:
            keys.add(key)
    return keys

def append_execution_log(entry: dict):
    log = read_execution_log()
    log.insert(0, entry)
    EXECUTION_LOG.write_text(json.dumps(log[:100], indent=2))
    return log[:100]


app = FastAPI(title="TradeGuard Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SIM_BROKER = SimulatedBrokerAdapter()
ALPACA_BROKER = AlpacaBrokerAdapter()

MARKET_STATE = {
    "last_generated_at": None,
    "cycle_id": 0,
    "symbols": ["AAPL", "MSFT", "NVDA", "TSLA", "AMD", "AMZN", "META", "GOOGL", "SPY", "QQQ"],
    "latest_prices": {},
    "rows_generated": 0,
}

AUTO_EXECUTION_STATE = {
    "enabled": False,
    "interval_seconds": 1,
    "last_cycle_at": None,
    "last_result": None,
    "cycles_completed": 0,
}

LIVE_STATE = {
    "running": False,
    "mode": "SIMULATED_PAPER",
    "broker": "SimulatedBrokerAdapter",
    "last_started_at": None,
    "last_run_at": None,
}

def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text())

def read_csv(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return []
    return pd.read_csv(path).fillna("").to_dict(orient="records")


def generate_market_ticks_from_quotes():
    """
    Generate a fresh multi-symbol tick file using current broker quote snapshots
    plus controlled micro-movement. This keeps the engine input dynamic while
    still using real broker market data as the anchor.
    """
    symbols = MARKET_STATE["symbols"]
    quotes = []

    if ALPACA_BROKER.is_configured():
        try:
            quotes = ALPACA_BROKER.get_latest_quotes(symbols)
        except Exception:
            quotes = []

    quote_by_symbol = {quote["symbol"]: quote for quote in quotes}
    MARKET_STATE["cycle_id"] += 1
    cycle_id = MARKET_STATE["cycle_id"]

    base_prices = {
        "AAPL": 190.0,
        "MSFT": 420.0,
        "NVDA": 900.0,
        "TSLA": 250.0,
        "AMD": 160.0,
        "AMZN": 180.0,
        "META": 500.0,
        "GOOGL": 170.0,
        "SPY": 520.0,
        "QQQ": 450.0,
    }

    # Use broker midpoint as the initial anchor, then evolve prices across cycles.
    # This keeps the internal paper portfolio moving even when broker quotes are stale
    # or markets are closed.
    previous_prices = MARKET_STATE.get("latest_prices", {}) or {}

    current_prices = {}
    for symbol in symbols:
        quote = quote_by_symbol.get(symbol, {})
        bid = float(quote.get("bid_price", 0) or 0)
        ask = float(quote.get("ask_price", 0) or 0)

        if symbol in previous_prices:
            anchor = float(previous_prices[symbol])
        elif bid > 0 and ask > 0:
            anchor = (bid + ask) / 2
        else:
            anchor = base_prices.get(symbol, 100.0)

        drift = random.uniform(-0.004, 0.004)
        current_prices[symbol] = max(0.01, anchor * (1 + drift))

    rows = ["timestamp,symbol,price,volume"]
    tick_count_per_symbol = 750

    for i in range(tick_count_per_symbol):
        for symbol in symbols:
            base = current_prices[symbol]

            # Create a deterministic but changing trend per cycle so the engine sees new data.
            direction = 1 if (cycle_id + len(symbol)) % 2 == 0 else -1
            trend = direction * 0.000035 * i
            wave = random.uniform(-0.0015, 0.0015)
            price = max(0.01, base * (1 + trend + wave))
            volume = random.randint(80, 900)

            rows.append(
                f"2026-01-02T09:{30 + (i // 100):02d}:{i % 60:02d},{symbol},{price:.4f},{volume}"
            )

    DATA.write_text("\n".join(rows) + "\n")

    MARKET_STATE["last_generated_at"] = datetime.utcnow().isoformat()
    MARKET_STATE["latest_prices"] = {symbol: round(price, 4) for symbol, price in current_prices.items()}
    MARKET_STATE["rows_generated"] = len(rows) - 1

    return MARKET_STATE

def run_command(command):
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

def default_summary():
    return {
        "total_decisions": 0,
        "accepted_trades": 0,
        "rejected_setups": 0,
        "executed_trades": 0,
        "ending_equity": 10000,
        "total_pnl": 0,
        "win_rate": 0,
        "average_pnl": 0,
        "best_trade": 0,
        "worst_trade": 0,
        "max_drawdown": 0,
    }


@app.get("/api/market/status")
def market_status():
    return MARKET_STATE

@app.post("/api/market/regenerate")
def market_regenerate():
    return generate_market_ticks_from_quotes()

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "TradeGuard Engine API",
        "time": datetime.utcnow().isoformat(),
    }

@app.get("/api/live/status")
def live_status():
    return LIVE_STATE

@app.post("/api/live/start")
def live_start():
    LIVE_STATE["running"] = True
    LIVE_STATE["last_started_at"] = datetime.utcnow().isoformat()
    return LIVE_STATE

@app.post("/api/live/stop")
def live_stop():
    LIVE_STATE["running"] = False
    return LIVE_STATE

@app.get("/api/summary")
def summary():
    return read_json(OUTPUT / "summary.json", default_summary())

@app.get("/api/decisions")
def decisions():
    return read_csv(OUTPUT / "decisions.csv")

@app.get("/api/trades")
def trades():
    return read_csv(OUTPUT / "trades.csv")

@app.get("/api/optimization")
def optimization():
    return read_csv(OUTPUT / "optimization_results.csv")

@app.get("/api/benchmark")
def benchmark():
    path = OUTPUT / "benchmark_report.txt"
    if not path.exists():
        return {"text": ""}
    return {"text": path.read_text()}

@app.get("/api/risk")
def risk():
    decisions_data = read_csv(OUTPUT / "decisions.csv")
    trades_data = read_csv(OUTPUT / "trades.csv")
    config = read_json(CONFIG, {})

    reason_counts = {}
    symbol_exposure = {}

    for row in decisions_data:
        if row.get("decision") == "REJECTED":
            reason = row.get("reason_code", "UNKNOWN")
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    for row in trades_data:
        symbol = row.get("symbol", "UNKNOWN")
        notional = abs(float(row.get("entry_price", 0) or 0) * float(row.get("quantity", 0) or 0))
        symbol_exposure[symbol] = symbol_exposure.get(symbol, 0) + notional

    return {
        "config": config,
        "reason_counts": reason_counts,
        "symbol_exposure": symbol_exposure,
        "total_rejections": sum(reason_counts.values()),
    }

@app.get("/api/broker")
def broker():
    return {
        "active_adapter": SIM_BROKER.name,
        "simulated_account": SIM_BROKER.get_account(),
        "alpaca_account": ALPACA_BROKER.get_account(),
        "available_adapters": [
            "SimulatedBrokerAdapter",
            "AlpacaBrokerAdapter"
        ],
        "message": "System runs in simulated paper mode by default. Alpaca paper trading can be enabled later with API keys."
    }


@app.get("/api/broker/account")
def broker_account():
    return {
        "simulated": SIM_BROKER.get_account(),
        "alpaca": ALPACA_BROKER.get_account(),
    }

@app.get("/api/broker/orders")
def broker_orders():
    return {
        "adapter": ALPACA_BROKER.name,
        "configured": ALPACA_BROKER.is_configured(),
        "orders": ALPACA_BROKER.list_orders() if ALPACA_BROKER.is_configured() else [],
    }

@app.post("/api/broker/test-order")
def broker_test_order():
    if not ALPACA_BROKER.is_configured():
        return {
            "ok": False,
            "message": "Alpaca keys are not configured. Add them to .env first.",
        }

    fill = ALPACA_BROKER.submit_order(
        BrokerOrder(
            symbol="AAPL",
            side="BUY",
            quantity=1,
        )
    )

    return {
        "ok": True,
        "fill": fill.__dict__,
        "message": "Submitted 1-share AAPL market order to Alpaca paper trading.",
    }


@app.get("/api/broker/market-snapshot")
def broker_market_snapshot():
    if not ALPACA_BROKER.is_configured():
        return {
            "configured": False,
            "quotes": [],
            "message": "Alpaca keys are not configured.",
        }

    return {
        "configured": True,
        "quotes": ALPACA_BROKER.get_latest_quotes(["AAPL", "MSFT", "NVDA", "TSLA", "SPY"]),
    }

@app.post("/api/broker/execute-latest-signal")
def broker_execute_latest_signal():
    if not ALPACA_BROKER.is_configured():
        return {
            "ok": False,
            "message": "Alpaca keys are not configured.",
        }

    decisions_data = read_csv(OUTPUT / "decisions.csv")
    accepted = [
        row for row in decisions_data
        if row.get("decision") == "ACCEPTED" and row.get("signal") == "LONG"
    ]

    if not accepted:
        return {
            "ok": False,
            "message": "No accepted LONG/SHORT engine decision available to execute.",
        }

    latest = accepted[-1]
    side = "BUY" if latest.get("signal") == "LONG" else "SELL"

    fill = ALPACA_BROKER.submit_order(
        BrokerOrder(
            symbol=str(latest.get("symbol", "AAPL")),
            side=side,
            quantity=1,
        )
    )

    return {
        "ok": True,
        "source_decision": latest,
        "fill": fill.__dict__,
        "message": "Submitted latest accepted engine signal to Alpaca paper trading.",
    }




def run_engine_and_execute_signals_internal():
    if not ALPACA_BROKER.is_configured():
        return {
            "ok": False,
            "stage": "broker",
            "message": "Alpaca keys are not configured.",
        }

    market_state = generate_market_ticks_from_quotes()

    engine_result = run_command([
        str(ENGINE),
        str(DATA),
        str(OUTPUT),
        str(CONFIG),
    ])

    LIVE_STATE["last_run_at"] = datetime.utcnow().isoformat()

    if engine_result["returncode"] != 0:
        return {
            "ok": False,
            "stage": "engine",
            "result": engine_result,
        }

    report_result = run_command([
        "python3",
        "python_analytics/report.py",
    ])

    if report_result["returncode"] != 0:
        return {
            "ok": False,
            "stage": "analytics",
            "result": report_result,
        }

    decisions_data = read_csv(OUTPUT / "decisions.csv")
    accepted = [
        row for row in decisions_data
        if row.get("decision") == "ACCEPTED" and row.get("signal") == "LONG"
    ]

    executed_keys = executed_signal_keys()
    selected = [
        decision for decision in accepted[-3:]
        if signal_key(decision) not in executed_keys
    ]

    fills = []
    errors = []

    for decision in selected:
        side = "BUY"

        try:
            fill = ALPACA_BROKER.submit_order(
                BrokerOrder(
                    symbol=str(decision.get("symbol", "AAPL")),
                    side=side,
                    quantity=1,
                )
            )

            execution_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "AUTO_ENGINE_SIGNAL_EXECUTION",
                "signal_key": signal_key(decision),
                "market_cycle_id": MARKET_STATE.get("cycle_id"),
                "source_decision": decision,
                "fill": fill.__dict__,
            }

            paper_state_after_fill = execute_internal_paper_fill(decision, fill.__dict__)

            fills.append(
                {
                    "source_decision": decision,
                    "fill": fill.__dict__,
                    "paper_state": {
                        "equity": paper_state_after_fill.get("equity"),
                        "cash": paper_state_after_fill.get("cash"),
                        "market_value": paper_state_after_fill.get("market_value"),
                        "unrealized_pnl": paper_state_after_fill.get("unrealized_pnl"),
                    },
                }
            )

            execution_entry["paper_state"] = {
                "equity": paper_state_after_fill.get("equity"),
                "cash": paper_state_after_fill.get("cash"),
                "market_value": paper_state_after_fill.get("market_value"),
                "unrealized_pnl": paper_state_after_fill.get("unrealized_pnl"),
            }

            append_execution_log(execution_entry)

        except Exception as exc:
            errors.append(
                {
                    "source_decision": decision,
                    "error": str(exc),
                }
            )

    result = {
        "ok": len(errors) == 0,
        "stage": "complete" if len(errors) == 0 else "partial_execution",
        "accepted_signals_found": len(accepted),
        "orders_submitted": len(fills),
        "fills": fills,
        "errors": errors,
        "summary": summary(),
        "market_state": MARKET_STATE,
        "message": f"Executed {len(fills)} new paper BUY orders from accepted LONG engine signals. Duplicate signals are skipped.",
    }

    return result

@app.get("/api/broker/positions")
def broker_positions():
    return {
        "adapter": ALPACA_BROKER.name,
        "configured": ALPACA_BROKER.is_configured(),
        "positions": ALPACA_BROKER.list_positions() if ALPACA_BROKER.is_configured() else [],
    }

@app.post("/api/broker/orders/{order_id}/cancel")
def broker_cancel_order(order_id: str):
    if not ALPACA_BROKER.is_configured():
        return {
            "ok": False,
            "message": "Alpaca keys are not configured.",
        }

    try:
        result = ALPACA_BROKER.cancel_order(order_id)
        append_execution_log({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "ORDER_CANCEL",
            "order_id": order_id,
            "result": result,
        })
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/execution-log")
def execution_log():
    return {
        "entries": read_execution_log(),
    }

@app.post("/api/broker/run-and-execute-signals")
def broker_run_and_execute_signals():
    result = run_engine_and_execute_signals_internal()
    AUTO_EXECUTION_STATE["last_cycle_at"] = datetime.utcnow().isoformat()
    AUTO_EXECUTION_STATE["last_result"] = result
    AUTO_EXECUTION_STATE["cycles_completed"] += 1
    return result

@app.post("/api/run-engine")
def run_engine():
    engine_result = run_command([
        str(ENGINE),
        str(DATA),
        str(OUTPUT),
        str(CONFIG),
    ])

    LIVE_STATE["last_run_at"] = datetime.utcnow().isoformat()

    if engine_result["returncode"] != 0:
        return {
            "ok": False,
            "stage": "engine",
            "result": engine_result,
        }

    report_result = run_command([
        "python3",
        "python_analytics/report.py",
    ])

    if report_result["returncode"] != 0:
        return {
            "ok": False,
            "stage": "analytics",
            "result": report_result,
        }

    return {
        "ok": True,
        "engine": engine_result,
        "analytics": report_result,
        "summary": summary(),
        "live": LIVE_STATE,
    }

@app.post("/api/run-optimization")
def run_optimization():
    optimization_result = run_command([
        "python3",
        "python_analytics/optimize_strategy.py",
    ])

    if optimization_result["returncode"] != 0:
        return {
            "ok": False,
            "stage": "optimization",
            "result": optimization_result,
        }

    return {
        "ok": True,
        "result": optimization_result,
        "optimization": optimization(),
    }



@app.get("/api/paper/state")
def paper_state():
    return mark_paper_portfolio_to_market()

@app.get("/api/automation/status")
def automation_status():
    return AUTO_EXECUTION_STATE

@app.post("/api/automation/start")
def automation_start():
    AUTO_EXECUTION_STATE["enabled"] = True
    AUTO_EXECUTION_STATE["started_by"] = "dashboard_session"
    AUTO_EXECUTION_STATE["last_session_started_at"] = datetime.utcnow().isoformat()
    return AUTO_EXECUTION_STATE

@app.post("/api/automation/stop")
def automation_stop():
    AUTO_EXECUTION_STATE["enabled"] = False
    AUTO_EXECUTION_STATE["last_session_stopped_at"] = datetime.utcnow().isoformat()
    return AUTO_EXECUTION_STATE

@app.on_event("startup")
async def start_auto_execution_loop():
    async def loop():
        while True:
            if AUTO_EXECUTION_STATE["enabled"]:
                try:
                    result = run_engine_and_execute_signals_internal()
                    AUTO_EXECUTION_STATE["last_cycle_at"] = datetime.utcnow().isoformat()
                    AUTO_EXECUTION_STATE["last_result"] = result
                    AUTO_EXECUTION_STATE["cycles_completed"] += 1
                except Exception as exc:
                    AUTO_EXECUTION_STATE["last_cycle_at"] = datetime.utcnow().isoformat()
                    AUTO_EXECUTION_STATE["last_result"] = {
                        "ok": False,
                        "stage": "auto_loop_error",
                        "message": str(exc),
                    }

            await asyncio.sleep(AUTO_EXECUTION_STATE["interval_seconds"])

    asyncio.create_task(loop())
