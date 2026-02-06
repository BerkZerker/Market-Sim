from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderResult:
    order_id: str
    ticker: str
    side: str
    price: float
    quantity: int
    filled_quantity: int
    status: str
    trades: list[dict]


@dataclass
class OpenOrder:
    order_id: str
    ticker: str
    side: str
    price: float
    quantity: int
    filled_quantity: int
    status: str
    created_at: str


@dataclass
class TradeResult:
    trade_id: str
    ticker: str
    price: float
    quantity: int
    side: str
    counterparty_id: str
    order_id: str
    created_at: str


@dataclass
class Holding:
    ticker: str
    quantity: int
    current_price: float
    value: float


@dataclass
class Portfolio:
    user_id: str
    username: str
    cash: float
    buying_power: float
    escrowed_cash: float
    holdings: list[Holding]
    total_value: float


@dataclass
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class TickerInfo:
    current_price: Optional[float]
    best_bid: Optional[float]
    best_ask: Optional[float]


@dataclass
class CancelResult:
    order_id: str
    status: str
    message: str
