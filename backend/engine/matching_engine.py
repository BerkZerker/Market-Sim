from core.order import Order
from core.trade import Trade
from engine.orderbook import OrderBook


class MatchingEngine:
    """
    Processes incoming orders against the order book and generates trades.
    """

    def __init__(self, order_book: OrderBook):
        self.order_book = order_book

    def process_order(self, incoming_order: Order, side: str) -> list[Trade]:
        """
        Processes a new order and returns a list of trades that occurred.
        """

        trades_made = []
        ticker = self.order_book.ticker

        if side == "buy":
            while (
                incoming_order.quantity > 0
                and self.order_book.asks
                and incoming_order.price >= self.order_book.asks[0].price
            ):
                book_order = self.order_book.asks[0]

                trade_quantity = min(incoming_order.quantity, book_order.quantity)
                trade_price = book_order.price

                trade = Trade(
                    ticker=ticker,
                    price=trade_price,
                    quantity=trade_quantity,
                    buyer_id=incoming_order.user_id,
                    seller_id=book_order.user_id,
                    buy_order_id=incoming_order.order_id,
                    sell_order_id=book_order.order_id,
                )
                trades_made.append(trade)

                incoming_order.quantity -= trade_quantity
                book_order.quantity -= trade_quantity

                if book_order.quantity == 0:
                    self.order_book.asks.pop(0)

            if incoming_order.quantity > 0:
                self.order_book.add_order(incoming_order, "buy")

        elif side == "sell":
            while (
                incoming_order.quantity > 0
                and self.order_book.bids
                and incoming_order.price <= self.order_book.bids[0].price
            ):
                book_order = self.order_book.bids[0]

                trade_quantity = min(incoming_order.quantity, book_order.quantity)
                trade_price = book_order.price

                trade = Trade(
                    ticker=ticker,
                    price=trade_price,
                    quantity=trade_quantity,
                    buyer_id=book_order.user_id,
                    seller_id=incoming_order.user_id,
                    buy_order_id=book_order.order_id,
                    sell_order_id=incoming_order.order_id,
                )
                trades_made.append(trade)

                incoming_order.quantity -= trade_quantity
                book_order.quantity -= trade_quantity

                if book_order.quantity == 0:
                    self.order_book.bids.pop(0)

            if incoming_order.quantity > 0:
                self.order_book.add_order(incoming_order, "sell")

        return trades_made
