import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from api.auth import router as auth_router
from api.dependencies import set_exchange
from api.leaderboard import router as leaderboard_router
from api.market import router as market_router
from api.portfolio import router as portfolio_router
from api.trading import router as trading_router
from config import settings
from core.user import User
from db.crud import create_user, load_all_users
from db.database import async_session, init_db
from engine.exchange import Exchange
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from ws.manager import manager

logger = logging.getLogger("market-sim")


async def _ensure_market_maker(exchange: Exchange) -> User:
    """Create or load the market maker bot user."""
    async with async_session() as session:
        from db.crud import get_user_by_username

        db_user = await get_user_by_username(session, "__market_maker__")
        if db_user is None:
            from api.dependencies import hash_password

            db_user = await create_user(
                session, "__market_maker__", hash_password("bot")
            )
            from db.models import UserModel
            from sqlalchemy import update

            await session.execute(
                update(UserModel)
                .where(UserModel.id == db_user.id)
                .values(is_market_maker=True)
            )
            await session.commit()
            await session.refresh(db_user)

        mm_user = User(
            user_id=UUID(db_user.id),
            username="__market_maker__",
            cash=0,
            is_market_maker=True,
        )
        exchange.register_user(mm_user)
        return mm_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init DB
    await init_db()
    logger.info("Database initialized")

    # Create exchange
    exchange = Exchange()
    for ticker, price in settings.TICKERS.items():
        exchange.add_ticker(ticker, initial_price=price)
    logger.info("Exchange created with tickers: %s", list(settings.TICKERS.keys()))

    # Load existing users into exchange
    async with async_session() as session:
        users = await load_all_users(session)
        for user in users:
            exchange.register_user(user)
        logger.info("Loaded %d users from database", len(users))

    # Set up market maker
    mm_user = await _ensure_market_maker(exchange)

    # Set singleton
    set_exchange(exchange)

    # Wire WebSocket broadcasts on trades
    def on_trades(ticker: str, trades):
        asyncio.create_task(manager.broadcast_trades(ticker, trades))
        asyncio.create_task(manager.broadcast_prices(exchange))
        asyncio.create_task(manager.broadcast_orderbook(ticker, exchange))

    exchange.on_trades = on_trades

    # Start market maker bots
    from bots.market_maker import MarketMakerBot

    bot = MarketMakerBot(exchange, mm_user)
    bot_task = asyncio.create_task(bot.run())
    logger.info("Market maker bot started")

    yield

    # Shutdown
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass

    # Persist all user state
    async with async_session() as session:
        from db.crud import sync_user_to_db

        for user in exchange.users.values():
            if not user.is_market_maker:
                await sync_user_to_db(session, user)
    logger.info("User state persisted to database")


app = FastAPI(
    title="Market Sim",
    description="AI-powered stock market simulation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(auth_router)
app.include_router(trading_router)
app.include_router(market_router)
app.include_router(portfolio_router)
app.include_router(leaderboard_router)


@app.websocket("/ws/{channel}")
async def ws_endpoint(websocket: WebSocket, channel: str):
    await manager.connect(websocket, channel)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


# Serve frontend in production
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True))


@app.get("/api/health")
async def health():
    return {"status": "ok"}


def main():
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
