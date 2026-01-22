import random
import time

from agent import Agent
from engine.matching_engine import MatchingEngine
from engine.orderbook import OrderBook


def main():
    """
    Runs the market simulation.
    """

    sim_stock_ticker = "SIM"
    market_book = OrderBook(sim_stock_ticker)
    engine = MatchingEngine(market_book)

    agents = [Agent() for _ in range(100)]
    last_price = 1000.0

    while True:
        # Choose a random agent to create an order
        agent = random.choice(agents)
        order, side = agent.create_random_order(sim_stock_ticker, last_price)

        # Process the order
        trades = engine.process_order(order, side)

        if trades:
            last_price = trades[-1].price

        # Print the most recent price and order placed
        print(
            f"Last Price: {last_price:.2f} | Order: {side.upper()} {order.quantity} @ \
                {order.price:.2f}"
        )

        time.sleep(0.1)


if __name__ == "__main__":
    main()
