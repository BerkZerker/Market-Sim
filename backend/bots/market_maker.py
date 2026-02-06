import asyncio
import logging
import random

from core.order import Order
from core.user import User
from db.crud import cancel_order_db, record_order, record_trade
from engine.exchange import Exchange

logger = logging.getLogger("market-sim.bot")


class MarketMakerBot:
    """
    Background bot that provides liquidity on all tickers.
    Places bid/ask pairs around the current price every few seconds.
    """

    def __init__(
        self,
        exchange: Exchange,
        user: User,
        session_factory=None,
        interval: float = 2.0,
    ):
        self.exchange = exchange
        self.user = user
        self.session_factory = session_factory
        self.interval = interval
        self.spread_pct = 0.01  # 1% spread

    async def run(self):
        logger.info("Market maker bot running")
        while True:
            try:
                for ticker in list(self.exchange.order_books.keys()):
                    await self._quote_ticker(ticker)
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                logger.info("Market maker bot shutting down")
                raise
            except Exception:
                logger.exception("Market maker error")
                await asyncio.sleep(self.interval)

    async def _quote_ticker(self, ticker: str):
        price = self.exchange.get_current_price(ticker)
        if price is None:
            return

        # Cancel stale orders before placing new ones
        cancelled = await self.exchange.cancel_all_for_user(ticker, self.user.user_id)

        spread = price * self.spread_pct
        bid_price = round(price - spread, 2)
        ask_price = round(price + spread, 2)
        quantity = random.randint(5, 20)

        # Place bid
        bid_order = Order(
            price=bid_price,
            quantity=quantity,
            user_id=self.user.user_id,
        )
        bid_trades, bid_status = await self.exchange.place_order(
            ticker, bid_order, "buy"
        )

        # Place ask
        ask_order = Order(
            price=ask_price,
            quantity=quantity,
            user_id=self.user.user_id,
        )
        ask_trades, ask_status = await self.exchange.place_order(
            ticker, ask_order, "sell"
        )

        # Persist to DB
        if self.session_factory is not None:
            try:
                async with self.session_factory() as session:
                    # Record cancelled stale orders
                    for order, _side in cancelled:
                        await cancel_order_db(session, str(order.order_id))

                    # Record bid order
                    bid_filled = sum(t.quantity for t in bid_trades)
                    await record_order(
                        session,
                        order_id=str(bid_order.order_id),
                        user_id=str(self.user.user_id),
                        ticker=ticker,
                        side="buy",
                        price=bid_price,
                        quantity=quantity,
                        filled_quantity=bid_filled,
                        status=bid_status,
                    )

                    # Record ask order
                    ask_filled = sum(t.quantity for t in ask_trades)
                    await record_order(
                        session,
                        order_id=str(ask_order.order_id),
                        user_id=str(self.user.user_id),
                        ticker=ticker,
                        side="sell",
                        price=ask_price,
                        quantity=quantity,
                        filled_quantity=ask_filled,
                        status=ask_status,
                    )

                    # Record trades
                    for trade in bid_trades + ask_trades:
                        await record_trade(
                            session,
                            trade_id=str(trade.trade_id),
                            ticker=trade.ticker,
                            price=trade.price,
                            quantity=trade.quantity,
                            buyer_id=str(trade.buyer_id),
                            seller_id=str(trade.seller_id),
                            buy_order_id=str(trade.buy_order_id),
                            sell_order_id=str(trade.sell_order_id),
                        )

                    await session.commit()
            except Exception:
                logger.exception("Failed to persist MM orders/trades for %s", ticker)
