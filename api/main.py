from pathlib import Path
import json
import subprocess
from datetime import datetime
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.brokers import AlpacaBrokerAdapter, SimulatedBrokerAdapter

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
ENGINE = ROOT / "build" / "tradeguard"
DATA = ROOT / "data" / "sample_ticks.csv"
CONFIG = ROOT / "config" / "risk_config.json"

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
