import asyncio
from collections.abc import AsyncGenerator

import pytest
from db.models import Base
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with a properly initialized exchange."""
    from api.dependencies import set_exchange
    from config import settings
    from db import database as db_module
    from engine.exchange import Exchange
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    # Override the database to use in-memory SQLite
    test_session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    original_engine = db_module.engine
    original_session = db_module.async_session

    db_module.engine = db_engine
    db_module.async_session = test_session_factory

    # Create and register exchange
    exchange = Exchange()
    for ticker, price in settings.TICKERS.items():
        exchange.add_ticker(ticker, initial_price=price)
    set_exchange(exchange)

    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Restore
    db_module.engine = original_engine
    db_module.async_session = original_session
    set_exchange(None)  # type: ignore
