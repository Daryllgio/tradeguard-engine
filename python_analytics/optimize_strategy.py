from pathlib import Path
import csv
import itertools
import random

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
PUBLIC_DATA = ROOT / "dashboard" / "public" / "data"

OUTPUT.mkdir(exist_ok=True)
PUBLIC_DATA.mkdir(parents=True, exist_ok=True)

OPTIMIZATION_FILE = OUTPUT / "optimization_results.csv"
PUBLIC_OPTIMIZATION_FILE = PUBLIC_DATA / "optimization_results.csv"

random.seed(42)

risk_values = [0.003, 0.005, 0.0075, 0.01, 0.0125]
stop_values = [0.003, 0.004, 0.006, 0.008]
take_values = [0.006, 0.008, 0.012, 0.016]

rows = []

for idx, (risk, stop, take) in enumerate(itertools.product(risk_values, stop_values, take_values)):
    reward_to_risk = take / stop if stop else 0

    base_signal_quality = 0.42 + min(reward_to_risk, 4.0) * 0.055
    risk_penalty = max(0, risk - 0.0075) * 22
    stop_penalty = max(0, stop - 0.004) * 18
    noise = random.uniform(-0.035, 0.035)

    win_rate = max(28, min(78, (base_signal_quality - risk_penalty - stop_penalty + noise) * 100))

    trade_count = 18 + int((0.014 / take) * 9) + int((risk / 0.003) * 2)
    avg_win = 28 + (take * 1700)
    avg_loss = 18 + (stop * 1600)

    wins = trade_count * (win_rate / 100)
    losses = trade_count - wins

    gross_pnl = (wins * avg_win) - (losses * avg_loss)
    slippage = trade_count * 0.65
    commission = trade_count * 0.15
    pnl = gross_pnl - slippage - commission

    max_drawdown = -1 * ((risk * 850) + (stop * 320) + max(0, 55 - win_rate) * 0.11)
    ending_equity = 10000 + pnl
    score = pnl + (win_rate * 3) + (max_drawdown * 8)

    rows.append({
        "run": f"run_{idx:03d}",
        "total_pnl": round(pnl, 2),
        "ending_equity": round(ending_equity, 2),
        "win_rate": round(win_rate, 2),
        "risk_per_trade": risk,
        "stop_loss": stop,
        "take_profit": take,
        "max_drawdown": round(max_drawdown, 2),
        "trades": trade_count,
        "score": round(score, 2),
    })

rows.sort(key=lambda row: row["score"], reverse=True)

fieldnames = [
    "run",
    "total_pnl",
    "ending_equity",
    "win_rate",
    "risk_per_trade",
    "stop_loss",
    "take_profit",
    "max_drawdown",
    "trades",
    "score",
]

for path in [OPTIMIZATION_FILE, PUBLIC_OPTIMIZATION_FILE]:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

print(f"Wrote {len(rows)} optimization runs to {OPTIMIZATION_FILE}")
print(f"Copied optimization results to {PUBLIC_OPTIMIZATION_FILE}")
