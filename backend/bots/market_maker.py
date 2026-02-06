import asyncio
import logging
import random

from core.order import Order
from core.user import User
from engine.exchange import Exchange

logger = logging.getLogger("market-sim.bot")


class MarketMakerBot:
    """
    Background bot that provides liquidity on all tickers.
    Places bid/ask pairs around the current price every few seconds.
    """

    def __init__(self, exchange: Exchange, user: User, interval: float = 2.0):
        self.exchange = exchange
        self.user = user
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
        await self.exchange.cancel_all_for_user(ticker, self.user.user_id)

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
        await self.exchange.place_order(ticker, bid_order, "buy")

        # Place ask
        ask_order = Order(
            price=ask_price,
            quantity=quantity,
            user_id=self.user.user_id,
        )
        await self.exchange.place_order(ticker, ask_order, "sell")
