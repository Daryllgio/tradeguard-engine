from datetime import datetime
from uuid import uuid4

from .base import BrokerAdapter, BrokerFill, BrokerOrder


class SimulatedBrokerAdapter(BrokerAdapter):
    name = "SimulatedBrokerAdapter"

    def __init__(self, starting_equity: float = 10000.0):
        self.starting_equity = starting_equity
        self.cash = starting_equity
        self.orders = []

    def submit_order(self, order: BrokerOrder) -> BrokerFill:
        # Simple simulated fill. Real market price is handled by the C++ engine outputs.
        fill = BrokerFill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            fill_price=0.0,
            status="FILLED_SIMULATED",
            broker_order_id=f"sim-{uuid4()}",
        )

        self.orders.append(
            {
                "submitted_at": datetime.utcnow().isoformat(),
                "order": order.__dict__,
                "fill": fill.__dict__,
            }
        )

        return fill

    def get_account(self) -> dict:
        return {
            "adapter": self.name,
            "mode": "SIMULATED_PAPER",
            "starting_equity": self.starting_equity,
            "cash": self.cash,
            "orders_submitted": len(self.orders),
        }
