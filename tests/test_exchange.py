import asyncio
import uuid

import pytest
from core.order import Order
from core.user import User
from engine.exchange import Exchange
from engine.orderbook import OrderBook


@pytest.fixture
def exchange():
    exchange = Exchange()
    exchange.add_ticker("TEST", initial_price=100.0)
    return exchange


@pytest.fixture
def buyer(exchange):
    user = User(user_id=uuid.uuid4(), username="buyer", cash=10000.0)
    exchange.register_user(user)
    return user


@pytest.fixture
def seller(exchange):
    user = User(user_id=uuid.uuid4(), username="seller", cash=10000.0)
    user.portfolio["TEST"] = 100
    exchange.register_user(user)
    return user


@pytest.fixture
def market_maker(exchange):
    user = User(
        user_id=uuid.uuid4(),
        username="mm",
        cash=0.0,
        is_market_maker=True,
    )
    exchange.register_user(user)
    return user


@pytest.mark.asyncio
async def test_buy_order_insufficient_funds(exchange, buyer):
    order = Order(price=200.0, quantity=100, user_id=buyer.user_id)
    with pytest.raises(ValueError, match="Insufficient funds"):
        await exchange.place_order("TEST", order, "buy")


@pytest.mark.asyncio
async def test_sell_order_insufficient_shares(exchange, buyer):
    # buyer has no shares
    order = Order(price=100.0, quantity=10, user_id=buyer.user_id)
    with pytest.raises(ValueError, match="Insufficient shares"):
        await exchange.place_order("TEST", order, "sell")


@pytest.mark.asyncio
async def test_market_maker_skips_validation(exchange, market_maker):
    # Market maker can place orders without funds or shares
    buy_order = Order(price=99.0, quantity=10, user_id=market_maker.user_id)
    trades, status = await exchange.place_order("TEST", buy_order, "buy")
    assert status == "open"

    sell_order = Order(price=101.0, quantity=10, user_id=market_maker.user_id)
    trades, status = await exchange.place_order("TEST", sell_order, "sell")
    assert status == "open"


@pytest.mark.asyncio
async def test_order_matching_and_settlement(exchange, buyer, market_maker):
    # Market maker places an ask
    ask = Order(price=100.0, quantity=5, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    # Buyer places a matching bid
    initial_cash = buyer.cash
    bid = Order(price=100.0, quantity=5, user_id=buyer.user_id)
    trades, status = await exchange.place_order("TEST", bid, "buy")

    assert status == "filled"
    assert len(trades) == 1
    assert trades[0].quantity == 5
    assert trades[0].price == 100.0

    # Buyer got shares, lost cash
    assert buyer.portfolio["TEST"] == 5
    assert buyer.cash == initial_cash - 500.0


@pytest.mark.asyncio
async def test_partial_fill(exchange, buyer, market_maker):
    # Market maker places small ask
    ask = Order(price=100.0, quantity=3, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    # Buyer wants more than available
    bid = Order(price=100.0, quantity=10, user_id=buyer.user_id)
    trades, status = await exchange.place_order("TEST", bid, "buy")

    assert status == "partial"
    assert len(trades) == 1
    assert trades[0].quantity == 3
    assert buyer.portfolio["TEST"] == 3


@pytest.mark.asyncio
async def test_sell_settlement(exchange, seller, market_maker):
    # Market maker places a bid
    bid = Order(price=95.0, quantity=10, user_id=market_maker.user_id)
    await exchange.place_order("TEST", bid, "buy")

    # Seller sells into it
    initial_cash = seller.cash
    ask = Order(price=95.0, quantity=10, user_id=seller.user_id)
    trades, status = await exchange.place_order("TEST", ask, "sell")

    assert status == "filled"
    assert seller.portfolio["TEST"] == 90  # had 100, sold 10
    assert seller.cash == initial_cash + 950.0  # 10 * 95


@pytest.mark.asyncio
async def test_unregistered_user(exchange):
    order = Order(price=100.0, quantity=1, user_id=uuid.uuid4())
    with pytest.raises(ValueError, match="User not registered"):
        await exchange.place_order("TEST", order, "buy")


@pytest.mark.asyncio
async def test_invalid_ticker(exchange, buyer):
    order = Order(price=100.0, quantity=1, user_id=buyer.user_id)
    with pytest.raises(ValueError, match="not listed"):
        await exchange.place_order("FAKE", order, "buy")


@pytest.mark.asyncio
async def test_on_trades_callback(exchange, buyer, market_maker):
    callback_data = []

    def on_trades(ticker, trades):
        callback_data.append((ticker, trades))

    exchange.on_trades = on_trades

    ask = Order(price=100.0, quantity=5, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    bid = Order(price=100.0, quantity=5, user_id=buyer.user_id)
    await exchange.place_order("TEST", bid, "buy")

    assert len(callback_data) == 1
    assert callback_data[0][0] == "TEST"
    assert len(callback_data[0][1]) == 1


# --- Order cancellation tests ---


def test_orderbook_remove_order():
    book = OrderBook("TEST")
    order = Order(price=100.0, quantity=10, user_id=uuid.uuid4())
    book.add_order(order, "buy")
    assert len(book.bids) == 1

    # Remove existing
    removed = book.remove_order(order.order_id, "buy")
    assert removed is not None
    assert removed.order_id == order.order_id
    assert len(book.bids) == 0

    # Remove nonexistent returns None
    assert book.remove_order(uuid.uuid4(), "buy") is None


@pytest.mark.asyncio
async def test_cancel_buy_order(exchange, buyer):
    initial_cash = buyer.cash
    order = Order(price=100.0, quantity=5, user_id=buyer.user_id)
    trades, status = await exchange.place_order("TEST", order, "buy")
    assert status == "open"
    assert buyer.cash == initial_cash - 500.0

    # Cancel — cash should be restored
    remaining = await exchange.cancel_order(
        "TEST", order.order_id, "buy", buyer.user_id
    )
    assert remaining == 5
    assert buyer.cash == initial_cash
    assert len(exchange.order_books["TEST"].bids) == 0


@pytest.mark.asyncio
async def test_cancel_sell_order(exchange, seller):
    initial_shares = seller.portfolio["TEST"]
    order = Order(price=105.0, quantity=10, user_id=seller.user_id)
    trades, status = await exchange.place_order("TEST", order, "sell")
    assert status == "open"
    assert seller.portfolio["TEST"] == initial_shares - 10

    # Cancel — shares should be restored
    remaining = await exchange.cancel_order(
        "TEST", order.order_id, "sell", seller.user_id
    )
    assert remaining == 10
    assert seller.portfolio["TEST"] == initial_shares
    assert len(exchange.order_books["TEST"].asks) == 0


@pytest.mark.asyncio
async def test_cancel_partial_order(exchange, buyer, market_maker):
    # Market maker posts a small ask
    ask = Order(price=100.0, quantity=3, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    # Buyer wants 10, gets partial fill of 3
    initial_cash = buyer.cash
    bid = Order(price=100.0, quantity=10, user_id=buyer.user_id)
    trades, status = await exchange.place_order("TEST", bid, "buy")
    assert status == "partial"
    assert len(trades) == 1
    assert trades[0].quantity == 3
    # Escrowed 10*100=1000, got 3 shares
    assert buyer.cash == initial_cash - 1000.0

    # Cancel the remaining 7 on the book
    remaining = await exchange.cancel_order("TEST", bid.order_id, "buy", buyer.user_id)
    assert remaining == 7
    # Refund 7*100=700
    assert buyer.cash == initial_cash - 300.0  # net: paid for 3 shares
    assert buyer.portfolio["TEST"] == 3


@pytest.mark.asyncio
async def test_cancel_nonexistent_order(exchange, buyer):
    with pytest.raises(ValueError, match="Order not found"):
        await exchange.cancel_order("TEST", uuid.uuid4(), "buy", buyer.user_id)


# --- Price improvement refund tests ---


@pytest.mark.asyncio
async def test_partial_fill_price_improvement_refund(exchange, buyer, market_maker):
    """Partial fill at a better price should refund the price difference immediately."""
    # MM posts ask at 95
    ask = Order(price=95.0, quantity=3, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    # Buyer bids 100 for 10 — gets 3 filled at 95, 7 resting
    initial_cash = buyer.cash
    bid = Order(price=100.0, quantity=10, user_id=buyer.user_id)
    trades, status = await exchange.place_order("TEST", bid, "buy")

    assert status == "partial"
    assert len(trades) == 1
    assert trades[0].price == 95.0
    assert trades[0].quantity == 3

    # Escrowed: 10 * 100 = 1000
    # Filled cost: 3 * 95 = 285
    # Refund on filled portion: 3 * 100 - 285 = 15
    # Remaining escrow: 7 * 100 = 700 (still on book)
    # Cash = 10000 - 1000 + 15 = 9015
    assert buyer.cash == initial_cash - 1000.0 + 15.0
    assert buyer.portfolio["TEST"] == 3


@pytest.mark.asyncio
async def test_full_fill_price_improvement_refund(exchange, buyer, market_maker):
    """Full fill at a better price should refund the price difference (regression)."""
    # MM posts ask at 90
    ask = Order(price=90.0, quantity=5, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    # Buyer bids 100 for 5 — fully filled at 90
    initial_cash = buyer.cash
    bid = Order(price=100.0, quantity=5, user_id=buyer.user_id)
    trades, status = await exchange.place_order("TEST", bid, "buy")

    assert status == "filled"
    assert trades[0].price == 90.0

    # Escrowed: 5 * 100 = 500, cost: 5 * 90 = 450, refund: 50
    assert buyer.cash == initial_cash - 450.0
    assert buyer.portfolio["TEST"] == 5


@pytest.mark.asyncio
async def test_sell_sweeps_multiple_bid_levels(exchange, seller, market_maker):
    """Incoming sell matches multiple resting bids at different prices."""
    # MM places two bids at different prices
    bid1 = Order(price=105.0, quantity=5, user_id=market_maker.user_id)
    await exchange.place_order("TEST", bid1, "buy")
    bid2 = Order(price=100.0, quantity=5, user_id=market_maker.user_id)
    await exchange.place_order("TEST", bid2, "buy")

    # Seller sells 8 at 99 — sweeps 5@105 + 3@100
    initial_cash = seller.cash
    initial_shares = seller.portfolio["TEST"]
    ask = Order(price=99.0, quantity=8, user_id=seller.user_id)
    trades, status = await exchange.place_order("TEST", ask, "sell")

    assert status == "filled"
    assert len(trades) == 2
    assert trades[0].price == 105.0
    assert trades[0].quantity == 5
    assert trades[1].price == 100.0
    assert trades[1].quantity == 3

    # Seller escrowed 8 shares, received 5*105 + 3*100 = 825
    assert seller.portfolio["TEST"] == initial_shares - 8
    assert seller.cash == initial_cash + 825.0


# --- Cancel all for user tests ---


@pytest.mark.asyncio
async def test_cancel_all_for_user(exchange, market_maker):
    """cancel_all_for_user removes all orders from the book."""
    bid = Order(price=99.0, quantity=10, user_id=market_maker.user_id)
    await exchange.place_order("TEST", bid, "buy")
    ask = Order(price=101.0, quantity=10, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    book = exchange.order_books["TEST"]
    assert len(book.bids) == 1
    assert len(book.asks) == 1

    removed = await exchange.cancel_all_for_user("TEST", market_maker.user_id)
    assert len(removed) == 2
    assert len(book.bids) == 0
    assert len(book.asks) == 0


@pytest.mark.asyncio
async def test_cancel_all_preserves_other_users(exchange, buyer, market_maker):
    """cancel_all_for_user only removes the target user's orders."""
    mm_bid = Order(price=99.0, quantity=10, user_id=market_maker.user_id)
    await exchange.place_order("TEST", mm_bid, "buy")
    buyer_bid = Order(price=98.0, quantity=5, user_id=buyer.user_id)
    await exchange.place_order("TEST", buyer_bid, "buy")

    book = exchange.order_books["TEST"]
    assert len(book.bids) == 2

    await exchange.cancel_all_for_user("TEST", market_maker.user_id)
    assert len(book.bids) == 1
    assert book.bids[0].user_id == buyer.user_id


@pytest.mark.asyncio
async def test_cancel_all_refunds_non_market_maker(exchange, buyer, seller):
    """cancel_all_for_user refunds escrowed cash/shares for regular users."""
    initial_cash = buyer.cash
    initial_shares = seller.portfolio["TEST"]

    bid = Order(price=100.0, quantity=5, user_id=buyer.user_id)
    await exchange.place_order("TEST", bid, "buy")
    assert buyer.cash == initial_cash - 500.0

    ask = Order(price=110.0, quantity=10, user_id=seller.user_id)
    await exchange.place_order("TEST", ask, "sell")
    assert seller.portfolio["TEST"] == initial_shares - 10

    await exchange.cancel_all_for_user("TEST", buyer.user_id)
    assert buyer.cash == initial_cash  # cash refunded

    await exchange.cancel_all_for_user("TEST", seller.user_id)
    assert seller.portfolio["TEST"] == initial_shares  # shares refunded


# --- Per-ticker lock tests ---


@pytest.mark.asyncio
async def test_concurrent_orders_different_tickers(exchange, market_maker):
    """Orders on different tickers can process concurrently with per-ticker locks."""
    exchange.add_ticker("OTHER", initial_price=50.0)

    user = User(user_id=uuid.uuid4(), username="trader", cash=100000.0)
    user.portfolio["TEST"] = 100
    user.portfolio["OTHER"] = 100
    exchange.register_user(user)

    # MM provides asks on both tickers
    ask1 = Order(price=100.0, quantity=10, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask1, "sell")
    ask2 = Order(price=50.0, quantity=10, user_id=market_maker.user_id)
    await exchange.place_order("OTHER", ask2, "sell")

    # Place buys on both tickers concurrently
    bid1 = Order(price=100.0, quantity=5, user_id=user.user_id)
    bid2 = Order(price=50.0, quantity=5, user_id=user.user_id)

    results = await asyncio.gather(
        exchange.place_order("TEST", bid1, "buy"),
        exchange.place_order("OTHER", bid2, "buy"),
    )

    trades1, status1 = results[0]
    trades2, status2 = results[1]

    assert status1 == "filled"
    assert status2 == "filled"
    assert len(trades1) == 1
    assert len(trades2) == 1
    assert user.portfolio["TEST"] == 105
    assert user.portfolio["OTHER"] == 105


# --- IOC (Immediate-or-Cancel) tests ---


@pytest.mark.asyncio
async def test_ioc_full_fill(exchange, buyer, market_maker):
    """IOC order fully fills when enough liquidity exists."""
    ask = Order(price=100.0, quantity=5, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    initial_cash = buyer.cash
    bid = Order(price=100.0, quantity=5, user_id=buyer.user_id, time_in_force="IOC")
    trades, status = await exchange.place_order("TEST", bid, "buy")

    assert status == "filled"
    assert len(trades) == 1
    assert buyer.portfolio["TEST"] == 5
    assert buyer.cash == initial_cash - 500.0


@pytest.mark.asyncio
async def test_ioc_partial_fill(exchange, buyer, market_maker):
    """IOC order partially fills; remainder is refunded, not placed on book."""
    ask = Order(price=100.0, quantity=3, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    initial_cash = buyer.cash
    bid = Order(price=100.0, quantity=10, user_id=buyer.user_id, time_in_force="IOC")
    trades, status = await exchange.place_order("TEST", bid, "buy")

    assert status == "filled"
    assert len(trades) == 1
    assert trades[0].quantity == 3
    assert buyer.portfolio["TEST"] == 3
    # Escrowed 1000, filled 300, refunded 700
    assert buyer.cash == initial_cash - 300.0
    # Nothing on the book
    assert len(exchange.order_books["TEST"].bids) == 0


@pytest.mark.asyncio
async def test_ioc_no_fill(exchange, buyer):
    """IOC with no liquidity results in cancellation and full refund."""
    initial_cash = buyer.cash
    bid = Order(price=100.0, quantity=5, user_id=buyer.user_id, time_in_force="IOC")
    trades, status = await exchange.place_order("TEST", bid, "buy")

    assert status == "cancelled"
    assert len(trades) == 0
    assert buyer.cash == initial_cash
    assert len(exchange.order_books["TEST"].bids) == 0


# --- FOK (Fill-or-Kill) tests ---


@pytest.mark.asyncio
async def test_fok_full_fill(exchange, buyer, market_maker):
    """FOK order fully fills when exact or more liquidity exists."""
    ask = Order(price=100.0, quantity=10, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    initial_cash = buyer.cash
    bid = Order(price=100.0, quantity=5, user_id=buyer.user_id, time_in_force="FOK")
    trades, status = await exchange.place_order("TEST", bid, "buy")

    assert status == "filled"
    assert len(trades) == 1
    assert trades[0].quantity == 5
    assert buyer.portfolio["TEST"] == 5
    assert buyer.cash == initial_cash - 500.0


@pytest.mark.asyncio
async def test_fok_rejected_insufficient_liquidity(exchange, buyer):
    """FOK raises ValueError when not enough liquidity, no escrow deducted."""
    initial_cash = buyer.cash
    bid = Order(price=100.0, quantity=5, user_id=buyer.user_id, time_in_force="FOK")
    with pytest.raises(ValueError, match="FOK order cannot be fully filled"):
        await exchange.place_order("TEST", bid, "buy")

    assert buyer.cash == initial_cash
    assert len(exchange.order_books["TEST"].bids) == 0


@pytest.mark.asyncio
async def test_fok_exact_fill(exchange, buyer, market_maker):
    """FOK exactly fills available liquidity."""
    ask = Order(price=95.0, quantity=5, user_id=market_maker.user_id)
    await exchange.place_order("TEST", ask, "sell")

    initial_cash = buyer.cash
    bid = Order(price=100.0, quantity=5, user_id=buyer.user_id, time_in_force="FOK")
    trades, status = await exchange.place_order("TEST", bid, "buy")

    assert status == "filled"
    assert len(trades) == 1
    assert trades[0].price == 95.0
    assert buyer.portfolio["TEST"] == 5
    # Price improvement: escrowed 500, paid 475, refund 25
    assert buyer.cash == initial_cash - 475.0
