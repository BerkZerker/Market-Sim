import json
import logging
import time
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger("market-sim.ws")


class ConnectionManager:
    """Manages WebSocket connections with channel-based subscriptions."""

    def __init__(self):
        self.channels: dict[str, list[WebSocket]] = defaultdict(list)
        self._user_ids: dict[WebSocket, str | None] = {}
        self._last_orderbook_broadcast: dict[str, float] = {}
        self._orderbook_throttle = 0.5  # seconds

    async def connect(
        self, websocket: WebSocket, channel: str, user_id: str | None = None
    ):
        await websocket.accept()
        self.channels[channel].append(websocket)
        self._user_ids[websocket] = user_id
        logger.info(
            "WebSocket connected to channel: %s (user: %s)",
            channel,
            user_id or "anonymous",
        )

    def disconnect(self, websocket: WebSocket, channel: str):
        if websocket in self.channels[channel]:
            self.channels[channel].remove(websocket)
        self._user_ids.pop(websocket, None)
        logger.info("WebSocket disconnected from channel: %s", channel)

    async def _broadcast(self, channel: str, data: dict):
        dead = []
        for ws in self.channels[channel]:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.channels[channel]:
                self.channels[channel].remove(ws)

    async def broadcast_trades(self, ticker: str, trades):
        channel = f"trades:{ticker}"
        for trade in trades:
            await self._broadcast(
                channel,
                {
                    "type": "trade",
                    "ticker": ticker,
                    "price": trade.price,
                    "quantity": trade.quantity,
                    "timestamp": trade.timestamp,
                },
            )

    async def broadcast_prices(self, exchange):
        prices = {}
        for ticker in exchange.order_books:
            price = exchange.get_current_price(ticker)
            book = exchange.order_books[ticker]
            prices[ticker] = {
                "current_price": price,
                "best_bid": book.bids[0].price if book.bids else None,
                "best_ask": book.asks[0].price if book.asks else None,
            }
        await self._broadcast(
            "prices",
            {"type": "prices", "data": prices},
        )

    async def broadcast_orderbook(self, ticker: str, exchange):
        now = time.time()
        last = self._last_orderbook_broadcast.get(ticker, 0)
        if now - last < self._orderbook_throttle:
            return
        self._last_orderbook_broadcast[ticker] = now

        channel = f"orderbook:{ticker}"
        book = exchange.order_books.get(ticker)
        if not book:
            return

        bid_levels: dict[float, int] = {}
        for order in book.bids:
            bid_levels[order.price] = bid_levels.get(order.price, 0) + order.quantity

        ask_levels: dict[float, int] = {}
        for order in book.asks:
            ask_levels[order.price] = ask_levels.get(order.price, 0) + order.quantity

        await self._broadcast(
            channel,
            {
                "type": "orderbook",
                "ticker": ticker,
                "bids": [
                    {"price": p, "quantity": q}
                    for p, q in sorted(bid_levels.items(), reverse=True)
                ],
                "asks": [
                    {"price": p, "quantity": q} for p, q in sorted(ask_levels.items())
                ],
            },
        )


manager = ConnectionManager()
