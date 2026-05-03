from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

OUTPUT = Path("output")
REPORT = OUTPUT / "performance_summary.md"

def max_drawdown(equity):
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    return drawdown.min()

def safe_read_csv(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)

def main():
    trades_path = OUTPUT / "trades.csv"
    decisions_path = OUTPUT / "decisions.csv"
    equity_path = OUTPUT / "equity_curve.csv"

    trades = safe_read_csv(trades_path)
    decisions = safe_read_csv(decisions_path)
    equity = safe_read_csv(equity_path)

    total_trades = len(trades)
    total_decisions = len(decisions)

    accepted = (decisions["decision"] == "ACCEPTED").sum() if total_decisions else 0
    rejected = (decisions["decision"] == "REJECTED").sum() if total_decisions else 0

    total_pnl = trades["pnl"].sum() if total_trades and "pnl" in trades.columns else 0
    win_rate = (trades["pnl"] > 0).mean() * 100 if total_trades and "pnl" in trades.columns else 0
    avg_pnl = trades["pnl"].mean() if total_trades and "pnl" in trades.columns else 0
    best_trade = trades["pnl"].max() if total_trades and "pnl" in trades.columns else 0
    worst_trade = trades["pnl"].min() if total_trades and "pnl" in trades.columns else 0
    ending_equity = equity["equity"].iloc[-1] if len(equity) and "equity" in equity.columns else 10000
    mdd = max_drawdown(equity["equity"]) * 100 if len(equity) and "equity" in equity.columns else 0

    OUTPUT.mkdir(exist_ok=True)

    # Equity curve
    plt.figure(figsize=(10, 5))
    if len(equity) and {"step", "equity"}.issubset(equity.columns):
        plt.plot(equity["step"], equity["equity"])
        plt.title("TradeGuard Equity Curve")
        plt.xlabel("Trade Step")
        plt.ylabel("Equity")
    else:
        plt.text(0.5, 0.5, "No equity data", ha="center", va="center")
        plt.axis("off")
    plt.tight_layout()
    plt.savefig(OUTPUT / "equity_curve.png", dpi=160)
    plt.close()

    # PnL distribution
    plt.figure(figsize=(8, 5))
    if total_trades and "pnl" in trades.columns:
        trades["pnl"].plot(kind="hist", bins=20)
        plt.title("Trade PnL Distribution")
        plt.xlabel("PnL")
    else:
        plt.text(0.5, 0.5, "No executed trades", ha="center", va="center")
        plt.title("Trade PnL Distribution")
        plt.axis("off")
    plt.tight_layout()
    plt.savefig(OUTPUT / "pnl_distribution.png", dpi=160)
    plt.close()

    # Rejection reasons chart
    rejection_reasons = pd.Series(dtype="int64")
    if total_decisions and {"decision", "reason"}.issubset(decisions.columns):
        rejection_reasons = decisions[decisions["decision"] == "REJECTED"]["reason"].value_counts().head(10)

    plt.figure(figsize=(10, 6))
    if len(rejection_reasons):
        rejection_reasons.sort_values().plot(kind="barh")
        plt.title("Top Trade Rejection Reasons")
        plt.xlabel("Count")
    else:
        plt.text(0.5, 0.5, "No rejected setups", ha="center", va="center")
        plt.axis("off")
    plt.tight_layout()
    plt.savefig(OUTPUT / "rejection_reasons.png", dpi=160)
    plt.close()

    # Symbol-level PnL chart
    symbol_summary = pd.DataFrame()
    if total_trades and {"symbol", "pnl"}.issubset(trades.columns):
        symbol_summary = trades.groupby("symbol")["pnl"].agg(["count", "sum", "mean"]).reset_index()

        plt.figure(figsize=(8, 5))
        symbol_summary.plot(x="symbol", y="sum", kind="bar", legend=False)
        plt.title("Total PnL by Symbol")
        plt.xlabel("Symbol")
        plt.ylabel("Total PnL")
        plt.tight_layout()
        plt.savefig(OUTPUT / "symbol_pnl.png", dpi=160)
        plt.close()
    else:
        plt.figure(figsize=(8, 5))
        plt.text(0.5, 0.5, "No symbol PnL data", ha="center", va="center")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(OUTPUT / "symbol_pnl.png", dpi=160)
        plt.close()

    # Decision mix by symbol
    symbol_decisions = pd.DataFrame()
    if total_decisions and {"symbol", "decision"}.issubset(decisions.columns):
        symbol_decisions = decisions.groupby(["symbol", "decision"]).size().unstack(fill_value=0)

        plt.figure(figsize=(9, 5))
        symbol_decisions.plot(kind="bar", stacked=True)
        plt.title("Decision Mix by Symbol")
        plt.xlabel("Symbol")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.savefig(OUTPUT / "symbol_decision_mix.png", dpi=160)
        plt.close()

    with REPORT.open("w") as f:
        f.write("# TradeGuard Engine Performance Summary\n\n")

        f.write("## Core Metrics\n\n")
        f.write(f"- Total decisions: {total_decisions}\n")
        f.write(f"- Accepted trades: {accepted}\n")
        f.write(f"- Rejected setups: {rejected}\n")
        f.write(f"- Executed trades: {total_trades}\n")
        f.write(f"- Ending equity: ${ending_equity:,.2f}\n")
        f.write(f"- Total PnL: ${total_pnl:,.2f}\n")
        f.write(f"- Win rate: {win_rate:.2f}%\n")
        f.write(f"- Average PnL per trade: ${avg_pnl:,.2f}\n")
        f.write(f"- Best trade: ${best_trade:,.2f}\n")
        f.write(f"- Worst trade: ${worst_trade:,.2f}\n")
        f.write(f"- Max drawdown: {mdd:.2f}%\n\n")

        f.write("## Symbol Performance\n\n")
        if len(symbol_summary):
            for _, row in symbol_summary.iterrows():
                f.write(
                    f"- {row['symbol']}: {int(row['count'])} trades, "
                    f"total PnL ${row['sum']:,.2f}, avg PnL ${row['mean']:,.2f}\n"
                )
        else:
            f.write("- No trades executed.\n")

        f.write("\n## Top Rejection Reasons\n\n")
        if len(rejection_reasons):
            for reason, count in rejection_reasons.items():
                f.write(f"- {reason}: {count}\n")
        else:
            f.write("- No rejected setups.\n")

        f.write("\n## Generated Charts\n\n")
        f.write("- `output/equity_curve.png`\n")
        f.write("- `output/pnl_distribution.png`\n")
        f.write("- `output/rejection_reasons.png`\n")
        f.write("- `output/symbol_pnl.png`\n")
        f.write("- `output/symbol_decision_mix.png`\n")

    print(REPORT.read_text())

if __name__ == "__main__":
    main()
