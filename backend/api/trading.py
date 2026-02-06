from datetime import datetime
from uuid import UUID

from api.dependencies import get_current_user, get_db, get_exchange
from api.rate_limit import RateLimiter, get_rate_limiter
from core.order import Order
from core.user import User
from db.crud import (
    cancel_order_db,
    get_open_orders,
    get_order_by_id,
    get_user_trades,
    record_order,
    record_trade,
    sync_user_to_db,
)
from engine.exchange import Exchange
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api", tags=["trading"])


VALID_TIF = {"GTC", "IOC", "FOK"}


class OrderRequest(BaseModel):
    ticker: str
    side: str
    price: float
    quantity: int
    time_in_force: str = "GTC"


class TradeResponse(BaseModel):
    trade_id: str
    ticker: str
    price: float
    quantity: int
    buyer_id: str
    seller_id: str


class OrderResponse(BaseModel):
    order_id: str
    ticker: str
    side: str
    price: float
    quantity: int
    filled_quantity: int
    status: str
    trades: list[TradeResponse]


@router.post("/orders", response_model=OrderResponse)
async def place_order(
    req: OrderRequest,
    user: User = Depends(get_current_user),
    exchange: Exchange = Depends(get_exchange),
    db: AsyncSession = Depends(get_db),
    limiter: RateLimiter = Depends(get_rate_limiter),
):
    limiter.check(user.user_id)
    if req.side not in ("buy", "sell"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Side must be 'buy' or 'sell'",
        )
    if req.price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be positive",
        )
    if req.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be positive",
        )
    if req.ticker not in exchange.order_books:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticker '{req.ticker}' not found",
        )
    if req.time_in_force not in VALID_TIF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"time_in_force must be one of: {', '.join(sorted(VALID_TIF))}",
        )

    order = Order(
        price=round(req.price, 2),
        quantity=req.quantity,
        user_id=user.user_id,
        time_in_force=req.time_in_force,
    )

    try:
        trades, order_status = await exchange.place_order(
            req.ticker, order, req.side
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    filled_qty = sum(t.quantity for t in trades)

    # Persist to DB
    await record_order(
        db,
        order_id=str(order.order_id),
        user_id=str(user.user_id),
        ticker=req.ticker,
        side=req.side,
        price=req.price,
        quantity=req.quantity,
        filled_quantity=filled_qty,
        status=order_status,
        time_in_force=req.time_in_force,
    )

    for trade in trades:
        await record_trade(
            db,
            trade_id=str(trade.trade_id),
            ticker=trade.ticker,
            price=trade.price,
            quantity=trade.quantity,
            buyer_id=str(trade.buyer_id),
            seller_id=str(trade.seller_id),
            buy_order_id=str(trade.buy_order_id),
            sell_order_id=str(trade.sell_order_id),
        )

    # Sync user state
    await sync_user_to_db(db, user)

    # Also sync counterparties
    for trade in trades:
        for uid in (trade.buyer_id, trade.seller_id):
            if uid != user.user_id:
                counterparty = exchange.get_user(uid)
                if counterparty and not counterparty.is_market_maker:
                    await sync_user_to_db(db, counterparty)

    trade_responses = [
        TradeResponse(
            trade_id=str(t.trade_id),
            ticker=t.ticker,
            price=t.price,
            quantity=t.quantity,
            buyer_id=str(t.buyer_id),
            seller_id=str(t.seller_id),
        )
        for t in trades
    ]

    return OrderResponse(
        order_id=str(order.order_id),
        ticker=req.ticker,
        side=req.side,
        price=req.price,
        quantity=req.quantity,
        filled_quantity=filled_qty,
        status=order_status,
        trades=trade_responses,
    )


class CancelResponse(BaseModel):
    order_id: str
    status: str
    message: str


@router.delete("/orders/{order_id}", response_model=CancelResponse)
async def cancel_order(
    order_id: str,
    user: User = Depends(get_current_user),
    exchange: Exchange = Depends(get_exchange),
    db: AsyncSession = Depends(get_db),
    limiter: RateLimiter = Depends(get_rate_limiter),
):
    limiter.check(user.user_id)
    # 1. Look up order in DB
    db_order = await get_order_by_id(db, order_id)
    if db_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # 2. Ownership check
    if db_order.user_id != str(user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot cancel another user's order",
        )

    # 3. Status check — only open or partial orders can be cancelled
    if db_order.status not in ("open", "partial"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status '{db_order.status}'",
        )

    # 4. Remove from in-memory book and refund escrow
    try:
        await exchange.cancel_order(
            ticker=db_order.ticker,
            order_id=UUID(order_id),
            side=db_order.side,
            user_id=user.user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # 5. Update DB status
    await cancel_order_db(db, order_id)

    # 6. Persist refunded balance
    await sync_user_to_db(db, user)

    return CancelResponse(
        order_id=order_id,
        status="cancelled",
        message="Order cancelled successfully",
    )


class OpenOrderResponse(BaseModel):
    order_id: str
    ticker: str
    side: str
    price: float
    quantity: int
    filled_quantity: int
    status: str
    created_at: datetime


@router.get("/orders", response_model=list[OpenOrderResponse])
async def list_orders(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    orders = await get_open_orders(db, str(user.user_id), limit, offset)
    return [
        OpenOrderResponse(
            order_id=o.id,
            ticker=o.ticker,
            side=o.side,
            price=o.price,
            quantity=o.quantity,
            filled_quantity=o.filled_quantity,
            status=o.status,
            created_at=o.created_at,
        )
        for o in orders
    ]


class TradeHistoryResponse(BaseModel):
    trade_id: str
    ticker: str
    price: float
    quantity: int
    side: str
    counterparty_id: str
    order_id: str
    created_at: datetime


@router.get("/trades", response_model=list[TradeHistoryResponse])
async def list_trades(
    ticker: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    trades = await get_user_trades(
        db, str(user.user_id), ticker=ticker, limit=limit, offset=offset
    )
    uid = str(user.user_id)
    return [
        TradeHistoryResponse(
            trade_id=t.id,
            ticker=t.ticker,
            price=t.price,
            quantity=t.quantity,
            side="buy" if t.buyer_id == uid else "sell",
            counterparty_id=t.seller_id if t.buyer_id == uid else t.buyer_id,
            order_id=t.buy_order_id if t.buyer_id == uid else t.sell_order_id,
            created_at=t.created_at,
        )
        for t in trades
    ]
