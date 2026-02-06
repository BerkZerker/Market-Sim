from api.dependencies import get_current_user, get_exchange
from core.user import User
from engine.exchange import Exchange
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api", tags=["portfolio"])


@router.get("/portfolio")
async def get_portfolio(
    user: User = Depends(get_current_user),
    exchange: Exchange = Depends(get_exchange),
):
    holdings = []
    holdings_value = 0.0

    for ticker, qty in user.portfolio.items():
        if qty > 0:
            price = exchange.get_current_price(ticker) or 0.0
            value = price * qty
            holdings_value += value
            holdings.append(
                {
                    "ticker": ticker,
                    "quantity": qty,
                    "current_price": price,
                    "value": round(value, 2),
                }
            )

    # Compute escrowed cash from resting buy orders in the live order books
    escrowed_cash = 0.0
    for ticker, book in exchange.order_books.items():
        for order in book.bids:
            if order.user_id == user.user_id:
                escrowed_cash += order.price * order.quantity

    return {
        "user_id": str(user.user_id),
        "username": user.username,
        "cash": round(user.cash, 2),
        "buying_power": round(user.cash, 2),
        "escrowed_cash": round(escrowed_cash, 2),
        "holdings": holdings,
        "total_value": round(user.cash + escrowed_cash + holdings_value, 2),
    }
