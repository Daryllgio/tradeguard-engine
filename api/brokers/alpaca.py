import os

from .base import BrokerAdapter, BrokerFill, BrokerOrder


class AlpacaBrokerAdapter(BrokerAdapter):
    name = "AlpacaBrokerAdapter"

    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.paper_base_url = os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.secret_key)

    def submit_order(self, order: BrokerOrder) -> BrokerFill:
        if not self.is_configured():
            raise RuntimeError("Alpaca paper trading keys are not configured.")

        # Placeholder by design. This keeps secrets out of the repo and documents where
        # real broker execution would be added.
        raise NotImplementedError(
            "Alpaca live paper order submission is intentionally not enabled yet."
        )

    def get_account(self) -> dict:
        return {
            "adapter": self.name,
            "mode": "ALPACA_PAPER",
            "configured": self.is_configured(),
            "paper_base_url": self.paper_base_url,
        }
