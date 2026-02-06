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
    total_value = user.cash

    for ticker, qty in user.portfolio.items():
        if qty > 0:
            price = exchange.get_current_price(ticker) or 0.0
            value = price * qty
            total_value += value
            holdings.append(
                {
                    "ticker": ticker,
                    "quantity": qty,
                    "current_price": price,
                    "value": round(value, 2),
                }
            )

    return {
        "user_id": str(user.user_id),
        "username": user.username,
        "cash": round(user.cash, 2),
        "holdings": holdings,
        "total_value": round(total_value, 2),
    }
