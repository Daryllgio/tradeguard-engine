from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


Side = Literal["BUY", "SELL"]


@dataclass
class BrokerOrder:
    symbol: str
    side: Side
    quantity: int
    order_type: str = "market"


@dataclass
class BrokerFill:
    symbol: str
    side: Side
    quantity: int
    fill_price: float
    status: str
    broker_order_id: str


class BrokerAdapter(ABC):
    name: str

    @abstractmethod
    def submit_order(self, order: BrokerOrder) -> BrokerFill:
        raise NotImplementedError

    @abstractmethod
    def get_account(self) -> dict:
        raise NotImplementedError
