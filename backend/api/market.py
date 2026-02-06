from datetime import datetime, timedelta, timezone

from api.dependencies import get_db, get_exchange
from db.crud import get_trades_for_ticker
from engine.exchange import Exchange
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/market", tags=["market"])

VALID_INTERVALS = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "1d": 86400}


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
        "asks": [{"price": p, "quantity": q} for p, q in sorted(ask_levels.items())],
    }


class CandleResponse(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoryResponse(BaseModel):
    ticker: str
    interval: str
    candles: list[CandleResponse]


@router.get("/{ticker}/history", response_model=HistoryResponse)
async def get_history(
    ticker: str,
    interval: str = Query(default="5m"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    exchange: Exchange = Depends(get_exchange),
    db: AsyncSession = Depends(get_db),
):
    if ticker not in exchange.order_books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker '{ticker}' not found",
        )
    if interval not in VALID_INTERVALS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid interval. Must be one of: {', '.join(VALID_INTERVALS)}",
        )

    now = datetime.now(timezone.utc)
    if end is None:
        end = now
    if start is None:
        start = end - timedelta(hours=24)

    trades = await get_trades_for_ticker(db, ticker, start=start, end=end)

    # Bucket trades into candles
    interval_seconds = VALID_INTERVALS[interval]
    candles: list[CandleResponse] = []
    epoch = datetime(2020, 1, 1, tzinfo=timezone.utc)

    def _ensure_tz(dt: datetime) -> datetime:
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

    def _bucket_for(dt: datetime) -> datetime:
        dt = _ensure_tz(dt)
        s = (dt - epoch).total_seconds()
        return epoch + timedelta(seconds=(s // interval_seconds) * interval_seconds)

    if trades:
        bucket_trades: list = []
        bucket_start = _bucket_for(trades[0].created_at)

        for trade in trades:
            trade_bucket = _bucket_for(trade.created_at)
            if trade_bucket != bucket_start:
                # Flush previous bucket
                if bucket_trades:
                    candles.append(
                        CandleResponse(
                            timestamp=bucket_start.isoformat(),
                            open=bucket_trades[0].price,
                            high=max(t.price for t in bucket_trades),
                            low=min(t.price for t in bucket_trades),
                            close=bucket_trades[-1].price,
                            volume=sum(t.quantity for t in bucket_trades),
                        )
                    )
                bucket_start = trade_bucket
                bucket_trades = []
            bucket_trades.append(trade)

        # Flush last bucket
        if bucket_trades:
            candles.append(
                CandleResponse(
                    timestamp=bucket_start.isoformat(),
                    open=bucket_trades[0].price,
                    high=max(t.price for t in bucket_trades),
                    low=min(t.price for t in bucket_trades),
                    close=bucket_trades[-1].price,
                    volume=sum(t.quantity for t in bucket_trades),
                )
            )

    return HistoryResponse(ticker=ticker, interval=interval, candles=candles)
