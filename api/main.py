from pathlib import Path
import json
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

def read_execution_log():
    if not EXECUTION_LOG.exists():
        return []
    return json.loads(EXECUTION_LOG.read_text())

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
    if not ALPACA_BROKER.is_configured():
        return {
            "ok": False,
            "stage": "broker",
            "message": "Alpaca keys are not configured.",
        }

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

    # Keep the paper execution capped so one click does not spam paper orders.
    selected = accepted[-3:]

    fills = []
    errors = []

    for decision in selected:
        side = "BUY" if decision.get("signal") == "LONG" else "SELL"

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
                "type": "ENGINE_SIGNAL_EXECUTION",
                "source_decision": decision,
                "fill": fill.__dict__,
            }

            fills.append(
                {
                    "source_decision": decision,
                    "fill": fill.__dict__,
                }
            )

            append_execution_log(execution_entry)
        except Exception as exc:
            errors.append(
                {
                    "source_decision": decision,
                    "error": str(exc),
                }
            )

    return {
        "ok": len(errors) == 0,
        "stage": "complete" if len(errors) == 0 else "partial_execution",
        "accepted_signals_found": len(accepted),
        "orders_submitted": len(fills),
        "fills": fills,
        "errors": errors,
        "summary": summary(),
        "message": f"Executed {len(fills)} Alpaca paper BUY orders from accepted LONG engine signals.",
    }

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
