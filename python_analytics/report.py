from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

OUTPUT = Path("output")
REPORT = OUTPUT / "performance_summary.md"

def max_drawdown(equity):
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    return drawdown.min()

def main():
    trades_path = OUTPUT / "trades.csv"
    decisions_path = OUTPUT / "decisions.csv"
    equity_path = OUTPUT / "equity_curve.csv"

    trades = pd.read_csv(trades_path)
    decisions = pd.read_csv(decisions_path)
    equity = pd.read_csv(equity_path)

    total_trades = len(trades)
    accepted = (decisions["decision"] == "ACCEPTED").sum()
    rejected = (decisions["decision"] == "REJECTED").sum()

    total_pnl = trades["pnl"].sum() if total_trades else 0
    win_rate = (trades["pnl"] > 0).mean() * 100 if total_trades else 0
    avg_pnl = trades["pnl"].mean() if total_trades else 0
    best_trade = trades["pnl"].max() if total_trades else 0
    worst_trade = trades["pnl"].min() if total_trades else 0
    ending_equity = equity["equity"].iloc[-1] if len(equity) else 10000
    mdd = max_drawdown(equity["equity"]) * 100 if len(equity) else 0

    OUTPUT.mkdir(exist_ok=True)

    plt.figure(figsize=(10, 5))
    plt.plot(equity["step"], equity["equity"])
    plt.title("TradeGuard Equity Curve")
    plt.xlabel("Trade Step")
    plt.ylabel("Equity")
    plt.tight_layout()
    plt.savefig(OUTPUT / "equity_curve.png", dpi=160)
    plt.close()

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


    symbol_summary = trades.groupby("symbol")["pnl"].agg(["count", "sum", "mean"]).reset_index() if total_trades else pd.DataFrame()

    rejection_reasons = decisions[decisions["decision"] == "REJECTED"]["reason"].value_counts().head(8)

    with REPORT.open("w") as f:
        f.write("# TradeGuard Engine Performance Summary\n\n")
        f.write("## Core Metrics\n\n")
        f.write(f"- Total decisions: {len(decisions)}\n")
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
        if total_trades:
            for _, row in symbol_summary.iterrows():
                f.write(f"- {row['symbol']}: {int(row['count'])} trades, total PnL ${row['sum']:,.2f}, avg PnL ${row['mean']:,.2f}\n")
        else:
            f.write("- No trades executed.\n")

        f.write("\n## Top Rejection Reasons\n\n")
        for reason, count in rejection_reasons.items():
            f.write(f"- {reason}: {count}\n")

        f.write("\n## Generated Charts\n\n")
        f.write("- `output/equity_curve.png`\n")
        f.write("- `output/pnl_distribution.png`\n")

    print(REPORT.read_text())

if __name__ == "__main__":
    main()
