from api.dependencies import get_exchange
from engine.exchange import Exchange
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api", tags=["leaderboard"])


@router.get("/leaderboard")
async def get_leaderboard(exchange: Exchange = Depends(get_exchange)):
    # Calculate total value for each non-market-maker user
    entries = []
    for user in exchange.users.values():
        if user.is_market_maker:
            continue

        total_value = user.cash
        holdings = []
        for ticker, qty in user.portfolio.items():
            if qty > 0:
                price = exchange.get_current_price(ticker) or 0.0
                total_value += price * qty
                holdings.append({"ticker": ticker, "quantity": qty})

        entries.append(
            {
                "user_id": str(user.user_id),
                "username": user.username,
                "cash": round(user.cash, 2),
                "holdings": holdings,
                "total_value": round(total_value, 2),
            }
        )

    entries.sort(key=lambda e: e["total_value"], reverse=True)
    return {"leaderboard": entries[:50]}
