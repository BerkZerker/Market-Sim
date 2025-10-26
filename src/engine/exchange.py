from collections import defaultdict

from core.order import Order
from engine.matching_engine import MatchingEngine
from engine.orderbook import OrderBook


class Exchange:
    """
    Represents a stock exchange that manages multiple tickers, each with its own
    order book and matching engine.
    """

    def __init__(self):
        # Using defaultdict to simplify the creation of new books/engines
        self.order_books: dict[str, OrderBook] = {}
        self.matching_engines: dict[str, MatchingEngine] = {}
        self.last_trades: dict[str, float] = {}

    def add_ticker(self, ticker: str):
        """
        Adds a new stock ticker to the exchange, creating an order book and
        matching engine for it.
        """
        if ticker not in self.order_books:
            order_book = OrderBook(ticker)
            self.order_books[ticker] = order_book
            self.matching_engines[ticker] = MatchingEngine(order_book)
            print(f"Ticker {ticker} has been added to the exchange.")
        else:
            print(f"Ticker {ticker} already exists on the exchange.")

    def place_order(self, ticker: str, order: Order, side: str) -> list:
        """
        Places an order on the exchange for a specific ticker.

        Args:
            ticker: The stock symbol.
            order: The Order object to be placed.
            side: 'buy' or 'sell'.

        Returns:
            A list of trades that occurred as a result of the order.
        """
        if ticker not in self.matching_engines:
            raise ValueError(f"Ticker '{ticker}' is not listed on this exchange.")

        engine = self.matching_engines[ticker]
        trades = engine.process_order(order, side)

        # If any trades occurred, record the price of the last one
        if trades:
            self.last_trades[ticker] = trades[-1].price

        return trades

    def get_order_book(self, ticker: str) -> OrderBook:
        """Returns the complete order book for a given ticker."""
        if ticker not in self.order_books:
            raise ValueError(f"Ticker '{ticker}' is not listed on this exchange.")
        return self.order_books[ticker]

    def get_current_price(self, ticker: str) -> float | None:
        """
        Gets the most recent price for a ticker.

        It first checks for the last traded price. If no trades have happened,
        it calculates the midpoint of the current best bid and ask.

        Returns:
            The current price as a float, or None if no price can be determined.
        """
        if ticker in self.last_trades:
            return self.last_trades[ticker]

        # If no trades yet, calculate midpoint from order book
        if ticker in self.order_books:
            order_book = self.order_books[ticker]
            if order_book.bids and order_book.asks:
                # Midpoint price
                return (order_book.bids[0].price + order_book.asks[0].price) / 2.0

        return None  # No price data available

    def get_exchange_stats(self) -> dict:
        """
        Provides a summary of the current state of all tickers on the exchange.
        """
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