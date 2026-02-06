from api.dependencies import get_current_user, get_db, get_exchange
from core.order import Order
from core.user import User
from db.crud import record_order, record_trade, sync_user_to_db
from engine.exchange import Exchange
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api", tags=["trading"])


class OrderRequest(BaseModel):
    ticker: str
    side: str
    price: float
    quantity: int


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
):
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

    order = Order(
        price=round(req.price, 2),
        quantity=req.quantity,
        user_id=user.user_id,
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
