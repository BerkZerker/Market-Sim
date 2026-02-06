from api.dependencies import get_exchange
from engine.exchange import Exchange
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/tickers")
async def get_tickers(exchange: Exchange = Depends(get_exchange)):
    tickers = {}
    for ticker in exchange.order_books:
        price = exchange.get_current_price(ticker)
        book = exchange.order_books[ticker]
        tickers[ticker] = {
            "current_price": price,
            "best_bid": book.bids[0].price if book.bids else None,
            "best_ask": book.asks[0].price if book.asks else None,
        }
    return {"tickers": tickers}


@router.get("/{ticker}")
async def get_ticker(ticker: str, exchange: Exchange = Depends(get_exchange)):
    if ticker not in exchange.order_books:
        return {"error": f"Ticker '{ticker}' not found"}

    price = exchange.get_current_price(ticker)
    book = exchange.order_books[ticker]
    return {
        "ticker": ticker,
        "current_price": price,
        "best_bid": book.bids[0].price if book.bids else None,
        "best_ask": book.asks[0].price if book.asks else None,
        "bid_depth": len(book.bids),
        "ask_depth": len(book.asks),
    }


@router.get("/{ticker}/orderbook")
async def get_orderbook(ticker: str, exchange: Exchange = Depends(get_exchange)):
    if ticker not in exchange.order_books:
        return {"error": f"Ticker '{ticker}' not found"}

    book = exchange.order_books[ticker]

    # Aggregate by price level (no user IDs exposed)
    bid_levels: dict[float, int] = {}
    for order in book.bids:
        bid_levels[order.price] = bid_levels.get(order.price, 0) + order.quantity

    ask_levels: dict[float, int] = {}
    for order in book.asks:
        ask_levels[order.price] = ask_levels.get(order.price, 0) + order.quantity

    return {
        "ticker": ticker,
        "bids": [
            {"price": p, "quantity": q}
            for p, q in sorted(bid_levels.items(), reverse=True)
        ],
        "asks": [
            {"price": p, "quantity": q}
            for p, q in sorted(ask_levels.items())
        ],
    }
