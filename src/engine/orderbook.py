from core.order import Order


class OrderBook:
    """
    Manages the collection of buy (bid) and sell (ask) orders for a single stock.
    """

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.bids: list[Order] = []  # List of buy orders
        self.asks: list[Order] = []  # List of sell orders

    def add_order(self, order: Order, side: str):
        """Adds an order to the book and keeps it sorted."""
        if side == "buy":
            self.bids.append(order)
            # Sort bids from highest to lowest price (descending).
            # If prices are equal, the older order (smaller timestamp) comes first.
            self.bids.sort(key=lambda o: (-o.price, o.timestamp))
        elif side == "sell":
            self.asks.append(order)
            # Sort asks from lowest to highest price (ascending).
            # If prices are equal, the older order (smaller timestamp) comes first.
            self.asks.sort(key=lambda o: (o.price, o.timestamp))

    def __repr__(self):
        """Provides a string representation for easy visualization of the order book."""
        book_str = f"--- Order Book for {self.ticker} ---\n"
        book_str += "BIDS:\n"
        if not self.bids:
            book_str += "  (Empty)\n"
        else:
            for order in self.bids:
                book_str += f"  Price: {order.price:<8.2f} Qty: {order.quantity:<5} User: {str(order.user_id)[-4:]}\n"

        book_str += "ASKS:\n"
        if not self.asks:
            book_str += "  (Empty)\n"
        else:
            for order in self.asks:
                book_str += f"  Price: {order.price:<8.2f} Qty: {order.quantity:<5} User: {str(order.user_id)[-4:]}\n"

        return book_str
