from pathlib import Path
from datetime import datetime, timedelta
import random
import math

def generate_ticks(path: str, n: int = 2500) -> None:
    random.seed(42)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    price = 100.0
    start = datetime(2026, 1, 2, 9, 30)

    with out.open("w") as f:
        f.write("timestamp,price,volume\n")

        for i in range(n):
            trend = 0.00015 * math.sin(i / 90)
            session_push = 0.00035 if 500 < i < 900 else (-0.00028 if 1400 < i < 1750 else 0)
            noise = random.gauss(0, 0.045)

            price = max(1, price + trend + session_push + noise)
            volume = max(10, random.gauss(800, 180))

            timestamp = start + timedelta(seconds=i)
            f.write(f"{timestamp.isoformat()},{price:.4f},{volume:.2f}\n")

if __name__ == "__main__":
    generate_ticks("data/sample_ticks.csv")
    print("Generated data/sample_ticks.csv")
