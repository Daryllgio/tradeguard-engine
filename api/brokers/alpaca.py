import os
from pathlib import Path

from dotenv import load_dotenv

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from .base import BrokerAdapter, BrokerFill, BrokerOrder


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


class AlpacaBrokerAdapter(BrokerAdapter):
    name = "AlpacaBrokerAdapter"

    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.secret_key)

    def _client(self) -> TradingClient:
        if not self.is_configured():
            raise RuntimeError("Alpaca paper trading keys are not configured.")
        return TradingClient(self.api_key, self.secret_key, paper=self.paper)

    def get_account(self) -> dict:
        if not self.is_configured():
            return {
                "adapter": self.name,
                "mode": "ALPACA_PAPER",
                "configured": False,
                "message": "Missing ALPACA_API_KEY or ALPACA_SECRET_KEY.",
            }

        account = self._client().get_account()

        return {
            "adapter": self.name,
            "mode": "ALPACA_PAPER" if self.paper else "ALPACA_LIVE",
            "configured": True,
            "account_number": getattr(account, "account_number", None),
            "status": str(getattr(account, "status", "")),
            "currency": getattr(account, "currency", "USD"),
            "cash": float(getattr(account, "cash", 0) or 0),
            "portfolio_value": float(getattr(account, "portfolio_value", 0) or 0),
            "buying_power": float(getattr(account, "buying_power", 0) or 0),
            "equity": float(getattr(account, "equity", 0) or 0),
            "paper": self.paper,
        }

    def list_orders(self, limit: int = 20) -> list[dict]:
        if not self.is_configured():
            return []

        orders = self._client().get_orders()
        results = []

        for order in orders[:limit]:
            results.append(
                {
                    "id": str(order.id),
                    "symbol": order.symbol,
                    "side": str(order.side),
                    "qty": str(order.qty),
                    "type": str(order.type),
                    "status": str(order.status),
                    "submitted_at": str(order.submitted_at),
                }
            )

        return results

    def submit_order(self, order: BrokerOrder) -> BrokerFill:
        client = self._client()

        side = OrderSide.BUY if order.side == "BUY" else OrderSide.SELL

        request = MarketOrderRequest(
            symbol=order.symbol,
            qty=order.quantity,
            side=side,
            time_in_force=TimeInForce.DAY,
        )

        submitted = client.submit_order(order_data=request)

        return BrokerFill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            fill_price=0.0,
            status=str(submitted.status),
            broker_order_id=str(submitted.id),
        )
