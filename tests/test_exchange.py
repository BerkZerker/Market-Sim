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
    remaining = await exchange.cancel_order("TEST", order.order_id, "buy", buyer.user_id)
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
    remaining = await exchange.cancel_order("TEST", order.order_id, "sell", seller.user_id)
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
