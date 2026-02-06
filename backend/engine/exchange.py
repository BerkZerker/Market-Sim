import asyncio
from collections.abc import Callable
from uuid import UUID

from core.order import Order
from core.trade import Trade
from core.user import User
from engine.matching_engine import MatchingEngine
from engine.orderbook import OrderBook


class Exchange:
    """
    Manages multiple tickers, each with its own order book and matching engine.
    Handles user registration, order validation (escrow), and settlement.
    """

    def __init__(self):
        self.order_books: dict[str, OrderBook] = {}
        self.matching_engines: dict[str, MatchingEngine] = {}
        self.last_trades: dict[str, float] = {}
        self.users: dict[UUID, User] = {}
        self._lock = asyncio.Lock()
        self.on_trades: Callable[[str, list[Trade]], None] | None = None

    def add_ticker(self, ticker: str, initial_price: float | None = None):
        if ticker not in self.order_books:
            order_book = OrderBook(ticker)
            self.order_books[ticker] = order_book
            self.matching_engines[ticker] = MatchingEngine(order_book)
            if initial_price is not None:
                self.last_trades[ticker] = initial_price

    def register_user(self, user: User):
        self.users[user.user_id] = user

    def get_user(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    async def place_order(
        self, ticker: str, order: Order, side: str
    ) -> tuple[list[Trade], str]:
        """
        Validates, escrows, matches, and settles an order.
        Returns (trades, status) where status is 'filled', 'partial', or 'open'.
        """
        if ticker not in self.matching_engines:
            raise ValueError(f"Ticker '{ticker}' is not listed on this exchange.")

        user = self.users.get(order.user_id)
        if user is None:
            raise ValueError("User not registered on exchange.")

        async with self._lock:
            original_qty = order.quantity

            # Escrow: debit funds/shares upfront (skip for market makers)
            if not user.is_market_maker:
                if side == "buy":
                    cost = order.price * order.quantity
                    if user.cash < cost:
                        raise ValueError(
                            f"Insufficient funds: need ${cost:.2f}, "
                            f"have ${user.cash:.2f}"
                        )
                    user.cash -= cost
                elif side == "sell":
                    if user.portfolio[ticker] < order.quantity:
                        raise ValueError(
                            f"Insufficient shares: need {order.quantity} "
                            f"{ticker}, have {user.portfolio[ticker]}"
                        )
                    user.portfolio[ticker] -= order.quantity

            # Match
            engine = self.matching_engines[ticker]
            trades = engine.process_order(order, side)

            # Update last trade price
            if trades:
                self.last_trades[ticker] = trades[-1].price

            # Settle trades: credit the other side
            for trade in trades:
                buyer = self.users.get(trade.buyer_id)
                seller = self.users.get(trade.seller_id)

                if buyer and buyer.user_id != order.user_id:
                    # Buyer was on the book — deduct escrowed at book price,
                    # but trade may execute at a different price for partial
                    # Actually buyer already escrowed at their order price;
                    # trade price may be lower. Refund difference handled below.
                    pass

                if seller and seller.user_id != order.user_id:
                    pass

                # Credit buyer's shares
                if buyer:
                    buyer.portfolio[ticker] += trade.quantity
                # Credit seller's cash
                if seller:
                    seller.cash += trade.price * trade.quantity

            # Refund un-filled portion of escrow
            remaining_qty = order.quantity  # after matching, this is unfilled qty
            filled_qty = original_qty - remaining_qty

            if not user.is_market_maker and remaining_qty == 0 and side == "buy":
                # Fully filled — refund difference between escrowed price and
                # actual execution prices
                total_escrowed = order.price * original_qty
                total_cost = sum(
                    t.price * t.quantity
                    for t in trades
                    if t.buyer_id == order.user_id
                )
                refund = total_escrowed - total_cost
                if refund > 0:
                    user.cash += refund

            # Determine status
            if filled_qty == original_qty:
                status = "filled"
            elif filled_qty > 0:
                status = "partial"
            else:
                status = "open"

        # Fire callback outside the lock
        if trades and self.on_trades:
            self.on_trades(ticker, trades)

        return trades, status

    def get_order_book(self, ticker: str) -> OrderBook:
        if ticker not in self.order_books:
            raise ValueError(f"Ticker '{ticker}' is not listed on this exchange.")
        return self.order_books[ticker]

    def get_current_price(self, ticker: str) -> float | None:
        if ticker in self.last_trades:
            return self.last_trades[ticker]

        if ticker in self.order_books:
            order_book = self.order_books[ticker]
            if order_book.bids and order_book.asks:
                return (order_book.bids[0].price + order_book.asks[0].price) / 2.0

        return None

    def get_exchange_stats(self) -> dict:
        stats = {}
        for ticker, book in self.order_books.items():
            stats[ticker] = {
                "current_price": self.get_current_price(ticker),
                "best_bid": book.bids[0].price if book.bids else None,
                "best_ask": book.asks[0].price if book.asks else None,
                "total_bids": len(book.bids),
                "total_asks": len(book.asks),
            }
        return stats
