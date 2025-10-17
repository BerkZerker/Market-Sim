from core.order import Order
from core.user import User
from engine.matching_engine import MatchingEngine
from engine.orderbook import OrderBook

def main():
    """
    Runs the market simulation.
    """

    # 1. Setup
    sim_stock_ticker = "SIM"

    user1 = User()
    user2 = User()
    user3 = User()

    # Give users some starting shares to sell
    user2.portfolio[sim_stock_ticker] = 50
    user3.portfolio[sim_stock_ticker] = 50

    print("--- Initial User Status ---")
    print(user1)
    print(user2)
    print(user3)
    print("\n")

    # The market consists of an order book and a matching engine for that book
    market_book = OrderBook(sim_stock_ticker)
    engine = MatchingEngine(market_book)

    # 2. Place some initial orders to populate the book
    # User 2 wants to sell at 101.00
    sell_order_1 = Order(price=101.00, quantity=20, user_id=user2.user_id)
    engine.process_order(sell_order_1, "sell")

    # User 3 wants to sell at 101.50
    sell_order_2 = Order(price=101.50, quantity=30, user_id=user3.user_id)
    engine.process_order(sell_order_2, "sell")

    # User 1 wants to buy, but at a lower price
    buy_order_1 = Order(price=99.50, quantity=25, user_id=user1.user_id)
    engine.process_order(buy_order_1, "buy")

    print("--- Market after initial orders ---")
    print(market_book)

    # 3. A new, aggressive buy order arrives that will cause trades
    print("\n--- User 1 places an aggressive buy order for 30 shares at $102.00 ---")
    aggressive_buy_order = Order(price=102.00, quantity=30, user_id=user1.user_id)
    trades = engine.process_order(aggressive_buy_order, "buy")

    # 4. Process the results of the trades
    if trades:
        print("\n--- Trades Occurred! ---")
        for trade in trades:
            print(f"  > Trade: {trade.quantity} shares @ ${trade.price:.2f}")

            # Find the user objects involved in the trade to update their state
            buyer = next(
                (u for u in [user1, user2, user3] if u.user_id == trade.buyer_id), None
            )
            seller = next(
                (u for u in [user1, user2, user3] if u.user_id == trade.seller_id), None
            )

            if buyer and seller:
                trade_value = trade.price * trade.quantity
                buyer.cash -= trade_value
                buyer.portfolio[sim_stock_ticker] += trade.quantity

                seller.cash += trade_value
                seller.portfolio[sim_stock_ticker] -= trade.quantity

    print("\n--- Final Market Status ---")
    print(market_book)

    print("--- Final User Status ---")
    print(user1)
    print(user2)
    print(user3)

if __name__ == "__main__":
    main()
