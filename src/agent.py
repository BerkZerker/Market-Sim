
import random
import uuid

from core.order import Order
from core.user import User


class Agent:
    """
    Represents a trading agent that can generate random orders.
    """

    def __init__(self):
        self.user = User()

    def create_random_order(self, ticker: str, last_price: float) -> tuple[Order, str]:
        """
        Generates a random buy or sell order.
        """
        side = random.choice(["buy", "sell"])
        
        # Generate a price with a small deviation from the last price
        price_deviation = random.uniform(-0.5, 0.5) * last_price
        price = round(last_price + price_deviation, 2)
        
        quantity = random.randint(1, 100)

        order = Order(
            price=price,
            quantity=quantity,
            user_id=self.user.user_id,
        )
        return order, side
