from pathlib import Path
from datetime import datetime, timedelta
import random
import math

def generate_ticks(path: str, n_per_symbol: int = 2500) -> None:
    random.seed(42)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    symbols = {
        "AAPL": 100.0,
        "MSFT": 240.0,
        "NVDA": 480.0,
    }

    start = datetime(2026, 1, 2, 9, 30)

    with out.open("w") as f:
        f.write("timestamp,symbol,price,volume\n")

        for i in range(n_per_symbol):
            timestamp = start + timedelta(seconds=i)

            for symbol, base_price in list(symbols.items()):
                trend = 0.00015 * math.sin(i / 90)
                session_push = 0.00035 if 500 < i < 900 else (-0.00028 if 1400 < i < 1750 else 0)
                symbol_bias = {"AAPL": 0.015, "MSFT": 0.01, "NVDA": 0.025}[symbol]
                noise = random.gauss(0, symbol_bias)

                price = max(1, base_price + trend + session_push + noise)
                symbols[symbol] = price

                volume = max(10, random.gauss(800, 180))
                f.write(f"{timestamp.isoformat()},{symbol},{price:.4f},{volume:.2f}\n")

if __name__ == "__main__":
    generate_ticks("data/sample_ticks.csv")
    print("Generated multi-symbol data/sample_ticks.csv")
