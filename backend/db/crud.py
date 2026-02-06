import uuid
from collections import defaultdict

from core.user import User
from db.models import OrderModel, PortfolioHolding, TradeModel, UserModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user(
    session: AsyncSession,
    username: str,
    password_hash: str,
) -> UserModel:
    user_id = str(uuid.uuid4())
    api_key = str(uuid.uuid4())
    db_user = UserModel(
        id=user_id,
        username=username,
        password_hash=password_hash,
        api_key=api_key,
    )
    session.add(db_user)
    await session.flush()
    await session.refresh(db_user)
    return db_user


async def get_user_by_username(
    session: AsyncSession, username: str
) -> UserModel | None:
    result = await session.execute(
        select(UserModel).where(UserModel.username == username)
    )
    return result.scalar_one_or_none()


async def get_user_by_api_key(session: AsyncSession, api_key: str) -> UserModel | None:
    result = await session.execute(
        select(UserModel).where(UserModel.api_key == api_key)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> UserModel | None:
    result = await session.execute(select(UserModel).where(UserModel.id == user_id))
    return result.scalar_one_or_none()


async def update_user_cash(session: AsyncSession, user_id: str, cash: float) -> None:
    await session.execute(
        update(UserModel).where(UserModel.id == user_id).values(cash=cash)
    )
    await session.flush()


async def get_holdings(session: AsyncSession, user_id: str) -> list[PortfolioHolding]:
    result = await session.execute(
        select(PortfolioHolding).where(PortfolioHolding.user_id == user_id)
    )
    return list(result.scalars().all())


async def update_holding(
    session: AsyncSession, user_id: str, ticker: str, quantity: int
) -> None:
    result = await session.execute(
        select(PortfolioHolding).where(
            PortfolioHolding.user_id == user_id,
            PortfolioHolding.ticker == ticker,
        )
    )
    holding = result.scalar_one_or_none()
    if holding:
        holding.quantity = quantity
    else:
        holding = PortfolioHolding(user_id=user_id, ticker=ticker, quantity=quantity)
        session.add(holding)
    await session.flush()


async def record_order(
    session: AsyncSession,
    order_id: str,
    user_id: str,
    ticker: str,
    side: str,
    price: float,
    quantity: int,
    filled_quantity: int,
    status: str,
    time_in_force: str = "GTC",
) -> OrderModel:
    db_order = OrderModel(
        id=order_id,
        user_id=user_id,
        ticker=ticker,
        side=side,
        price=price,
        quantity=quantity,
        filled_quantity=filled_quantity,
        status=status,
        time_in_force=time_in_force,
    )
    session.add(db_order)
    await session.flush()
    return db_order


async def record_trade(
    session: AsyncSession,
    trade_id: str,
    ticker: str,
    price: float,
    quantity: int,
    buyer_id: str,
    seller_id: str,
    buy_order_id: str,
    sell_order_id: str,
) -> TradeModel:
    db_trade = TradeModel(
        id=trade_id,
        ticker=ticker,
        price=price,
        quantity=quantity,
        buyer_id=buyer_id,
        seller_id=seller_id,
        buy_order_id=buy_order_id,
        sell_order_id=sell_order_id,
    )
    session.add(db_trade)
    await session.flush()
    return db_trade


async def get_user_trades(
    session: AsyncSession,
    user_id: str,
    ticker: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[TradeModel]:
    from sqlalchemy import or_

    stmt = select(TradeModel).where(
        or_(TradeModel.buyer_id == user_id, TradeModel.seller_id == user_id)
    )
    if ticker is not None:
        stmt = stmt.where(TradeModel.ticker == ticker)
    stmt = stmt.order_by(TradeModel.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_trades_for_ticker(
    session: AsyncSession,
    ticker: str,
    start=None,
    end=None,
) -> list[TradeModel]:
    stmt = select(TradeModel).where(TradeModel.ticker == ticker)
    if start is not None:
        stmt = stmt.where(TradeModel.created_at >= start)
    if end is not None:
        stmt = stmt.where(TradeModel.created_at <= end)
    stmt = stmt.order_by(TradeModel.created_at.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_leaderboard(session: AsyncSession, limit: int = 50) -> list[dict]:
    from sqlalchemy.orm import selectinload

    result = await session.execute(
        select(UserModel)
        .where(UserModel.is_market_maker.is_(False))
        .options(selectinload(UserModel.holdings))
        .order_by(UserModel.cash.desc())
        .limit(limit)
    )
    users = result.scalars().unique().all()
    leaderboard = []
    for user in users:
        leaderboard.append(
            {
                "user_id": user.id,
                "username": user.username,
                "cash": user.cash,
                "holdings": [
                    {"ticker": h.ticker, "quantity": h.quantity}
                    for h in user.holdings
                    if h.quantity > 0
                ],
            }
        )
    return leaderboard


async def load_all_users(session: AsyncSession) -> list[User]:
    """Load all users from DB into in-memory User objects."""
    result = await session.execute(select(UserModel))
    db_users = result.scalars().all()
    users = []
    for db_user in db_users:
        holdings = await get_holdings(session, db_user.id)
        portfolio = defaultdict(int)
        for h in holdings:
            portfolio[h.ticker] = h.quantity
        user = User(
            user_id=uuid.UUID(db_user.id),
            username=db_user.username,
            cash=db_user.cash,
            portfolio=portfolio,
            is_market_maker=db_user.is_market_maker,
        )
        users.append(user)
    return users


async def get_open_orders(
    session: AsyncSession,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[OrderModel]:
    result = await session.execute(
        select(OrderModel)
        .where(
            OrderModel.user_id == user_id,
            OrderModel.status.in_(["open", "partial"]),
        )
        .order_by(OrderModel.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_order_by_id(session: AsyncSession, order_id: str) -> OrderModel | None:
    result = await session.execute(select(OrderModel).where(OrderModel.id == order_id))
    return result.scalar_one_or_none()


async def update_order_fill(
    session: AsyncSession, order_id: str, filled_quantity: int, status: str
) -> None:
    await session.execute(
        update(OrderModel)
        .where(OrderModel.id == order_id)
        .values(filled_quantity=filled_quantity, status=status)
    )
    await session.flush()


async def cancel_order_db(session: AsyncSession, order_id: str) -> None:
    await session.execute(
        update(OrderModel).where(OrderModel.id == order_id).values(status="cancelled")
    )
    await session.flush()


async def sync_user_to_db(session: AsyncSession, user: User) -> None:
    """Sync in-memory user state back to DB."""
    await update_user_cash(session, str(user.user_id), user.cash)
    for ticker, qty in user.portfolio.items():
        await update_holding(session, str(user.user_id), ticker, qty)
