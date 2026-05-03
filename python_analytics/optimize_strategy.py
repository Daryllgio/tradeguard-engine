from pathlib import Path
import json
import subprocess
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sample_ticks.csv"
ENGINE = ROOT / "build" / "tradeguard"
OUTPUT_BASE = ROOT / "output" / "optimization_runs"
CONFIG_PATH = ROOT / "config" / "optimization_config.json"
RESULTS_PATH = ROOT / "output" / "optimization_results.csv"

def run_engine(config: dict, run_name: str) -> dict:
    output_dir = OUTPUT_BASE / run_name
    output_dir.mkdir(parents=True, exist_ok=True)

    CONFIG_PATH.write_text(json.dumps(config, indent=2))

    subprocess.run(
        [str(ENGINE), str(DATA), str(output_dir), str(CONFIG_PATH)],
        check=True,
        cwd=ROOT
    )

    summary = json.loads((output_dir / "summary.json").read_text())
    summary.update({
        "run": run_name,
        "stop_loss_pct": config["stop_loss_pct"],
        "take_profit_pct": config["take_profit_pct"],
        "max_risk_per_trade_pct": config["max_risk_per_trade_pct"]
    })
    return summary

def main():
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    base = {
        "account_equity": 10000.0,
        "max_daily_loss_pct": 0.03,
        "max_position_value_pct": 0.25,
        "max_symbol_exposure_pct": 0.35,
        "max_portfolio_exposure_pct": 0.75
    }

    runs = []
    idx = 0

    for risk in [0.005, 0.01, 0.015]:
        for stop in [0.003, 0.004, 0.006]:
            for take in [0.006, 0.008, 0.012]:
                config = {
                    **base,
                    "max_risk_per_trade_pct": risk,
                    "stop_loss_pct": stop,
                    "take_profit_pct": take
                }

                run_name = f"run_{idx:03d}"
                print(f"Running {run_name}: risk={risk}, stop={stop}, take={take}")
                runs.append(run_engine(config, run_name))
                idx += 1

    df = pd.DataFrame(runs)
    df = df.sort_values(["total_pnl", "max_drawdown"], ascending=[False, False])
    df.to_csv(RESULTS_PATH, index=False)

    print("\nTop strategy configurations:")
    print(df[[
        "run",
        "total_pnl",
        "ending_equity",
        "win_rate",
        "max_drawdown",
        "stop_loss_pct",
        "take_profit_pct",
        "max_risk_per_trade_pct"
    ]].head(10).to_string(index=False))

if __name__ == "__main__":
    main()
