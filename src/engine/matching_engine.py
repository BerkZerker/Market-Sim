from src.core.order import Order
from src.core.trade import Trade
from src.engine.orderbook import OrderBook


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

        if side == "buy":
            # Match against the asks (sell orders), starting with the cheapest
            while (
                incoming_order.quantity > 0
                and self.order_book.asks
                and incoming_order.price >= self.order_book.asks[0].price
            ):
                book_order = self.order_book.asks[0]

                trade_quantity = min(incoming_order.quantity, book_order.quantity)
                trade_price = book_order.price

                # Create a trade record
                trade = Trade(
                    price=trade_price,
                    quantity=trade_quantity,
                    buyer_id=incoming_order.user_id,
                    seller_id=book_order.user_id,
                )
                trades_made.append(trade)

                # Update quantities
                incoming_order.quantity -= trade_quantity
                book_order.quantity -= trade_quantity

                # If the order on the book is completely filled, remove it
                if book_order.quantity == 0:
                    self.order_book.asks.pop(0)

            # If the incoming order is not completely filled, add it to the book
            if incoming_order.quantity > 0:
                self.order_book.add_order(incoming_order, "buy")

        elif side == "sell":
            # Match against the bids (buy orders), starting with the most expensive
            while (
                incoming_order.quantity > 0
                and self.order_book.bids
                and incoming_order.price <= self.order_book.bids[0].price
            ):
                book_order = self.order_book.bids[0]

                trade_quantity = min(incoming_order.quantity, book_order.quantity)
                trade_price = book_order.price

                # Create a trade record
                trade = Trade(
                    price=trade_price,
                    quantity=trade_quantity,
                    buyer_id=book_order.user_id,
                    seller_id=incoming_order.user_id,
                )
                trades_made.append(trade)

                # Update quantities
                incoming_order.quantity -= trade_quantity
                book_order.quantity -= trade_quantity

                # If the order on the book is completely filled, remove it
                if book_order.quantity == 0:
                    self.order_book.bids.pop(0)

            # If the incoming order is not completely filled, add it to the book
            if incoming_order.quantity > 0:
                self.order_book.add_order(incoming_order, "sell")

        return trades_made
