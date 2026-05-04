from pathlib import Path
import pandas as pd

OUTPUT = Path("output")
REPORT = OUTPUT / "performance_summary.md"
BENCHMARK = OUTPUT / "benchmark_report.txt"

def safe_read_csv(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)

def max_drawdown_from_equity(equity_series):
    if equity_series.empty:
        return 0.0
    peak = equity_series.cummax()
    drawdown = (equity_series - peak) / peak
    return float(drawdown.min() * 100)

def main():
    OUTPUT.mkdir(exist_ok=True)

    trades = safe_read_csv(OUTPUT / "trades.csv")
    decisions = safe_read_csv(OUTPUT / "decisions.csv")
    equity = safe_read_csv(OUTPUT / "equity_curve.csv")

    total_trades = len(trades)
    total_decisions = len(decisions)

    accepted = int((decisions["decision"] == "ACCEPTED").sum()) if total_decisions and "decision" in decisions.columns else 0
    rejected = int((decisions["decision"] == "REJECTED").sum()) if total_decisions and "decision" in decisions.columns else 0

    if total_trades and "pnl" in trades.columns:
        total_pnl = float(trades["pnl"].sum())
        win_rate = float((trades["pnl"] > 0).mean() * 100)
        avg_pnl = float(trades["pnl"].mean())
        best_trade = float(trades["pnl"].max())
        worst_trade = float(trades["pnl"].min())
    else:
        total_pnl = 0.0
        win_rate = 0.0
        avg_pnl = 0.0
        best_trade = 0.0
        worst_trade = 0.0

    ending_equity = float(equity["equity"].iloc[-1]) if len(equity) and "equity" in equity.columns else 10000.0 + total_pnl
    max_drawdown = max_drawdown_from_equity(equity["equity"]) if len(equity) and "equity" in equity.columns else 0.0

    report = f"""# TradeGuard Performance Summary

## Engine Summary

| Metric | Value |
|---|---:|
| Total Decisions | {total_decisions:,} |
| Accepted Trades | {accepted:,} |
| Rejected Setups | {rejected:,} |
| Executed Trades | {total_trades:,} |
| Ending Equity | ${ending_equity:,.2f} |
| Total PnL | ${total_pnl:,.2f} |
| Win Rate | {win_rate:.2f}% |
| Average PnL | ${avg_pnl:,.2f} |
| Best Trade | ${best_trade:,.2f} |
| Worst Trade | ${worst_trade:,.2f} |
| Max Drawdown | {max_drawdown:.2f}% |

Deployment-safe analytics mode is active. Chart image generation is skipped on the hosted backend.
"""

    REPORT.write_text(report)
    BENCHMARK.write_text(report)

    print("Analytics report generated successfully without matplotlib.")

if __name__ == "__main__":
    main()
