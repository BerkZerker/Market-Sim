"""Synchronous REST client for the Market-Sim API."""

from __future__ import annotations

import requests

from .models import (
    CancelResult,
    Candle,
    Holding,
    OpenOrder,
    OrderResult,
    Portfolio,
    TickerInfo,
    TradeResult,
)


class MarketSimClient:
    """Sync client wrapping all Market-Sim REST endpoints."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers["X-API-Key"] = api_key

    @classmethod
    def register(
        cls, base_url: str, username: str, password: str
    ) -> "MarketSimClient":
        """Register a new user and return an authenticated client."""
        resp = requests.post(
            f"{base_url.rstrip('/')}/api/register",
            json={"username": username, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()
        return cls(base_url, data["api_key"])

    def _get(self, path: str, **params) -> dict:
        resp = self._session.get(f"{self.base_url}{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json: dict) -> dict:
        resp = self._session.post(f"{self.base_url}{path}", json=json)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str) -> dict:
        resp = self._session.delete(f"{self.base_url}{path}")
        resp.raise_for_status()
        return resp.json()

    # --- Market data (public) ---

    def get_tickers(self) -> dict[str, TickerInfo]:
        data = self._get("/api/market/tickers")
        return {
            ticker: TickerInfo(
                current_price=info["current_price"],
                best_bid=info["best_bid"],
                best_ask=info["best_ask"],
            )
            for ticker, info in data["tickers"].items()
        }

    def get_orderbook(self, ticker: str) -> dict:
        return self._get(f"/api/market/{ticker}/orderbook")

    def get_history(
        self,
        ticker: str,
        interval: str = "5m",
        start: str | None = None,
        end: str | None = None,
    ) -> list[Candle]:
        params: dict = {"interval": interval}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        data = self._get(f"/api/market/{ticker}/history", **params)
        return [
            Candle(
                timestamp=c["timestamp"],
                open=c["open"],
                high=c["high"],
                low=c["low"],
                close=c["close"],
                volume=c["volume"],
            )
            for c in data["candles"]
        ]

    def get_leaderboard(self) -> list[dict]:
        data = self._get("/api/leaderboard")
        return data["leaderboard"]

    # --- Trading (authenticated) ---

    def place_order(
        self,
        ticker: str,
        side: str,
        price: float,
        quantity: int,
        time_in_force: str = "GTC",
    ) -> OrderResult:
        data = self._post(
            "/api/orders",
            json={
                "ticker": ticker,
                "side": side,
                "price": price,
                "quantity": quantity,
                "time_in_force": time_in_force,
            },
        )
        return OrderResult(
            order_id=data["order_id"],
            ticker=data["ticker"],
            side=data["side"],
            price=data["price"],
            quantity=data["quantity"],
            filled_quantity=data["filled_quantity"],
            status=data["status"],
            trades=data["trades"],
        )

    def cancel_order(self, order_id: str) -> CancelResult:
        data = self._delete(f"/api/orders/{order_id}")
        return CancelResult(
            order_id=data["order_id"],
            status=data["status"],
            message=data["message"],
        )

    def get_orders(
        self, limit: int = 50, offset: int = 0
    ) -> list[OpenOrder]:
        data = self._get("/api/orders", limit=limit, offset=offset)
        return [
            OpenOrder(
                order_id=o["order_id"],
                ticker=o["ticker"],
                side=o["side"],
                price=o["price"],
                quantity=o["quantity"],
                filled_quantity=o["filled_quantity"],
                status=o["status"],
                created_at=o["created_at"],
            )
            for o in data
        ]

    def get_trades(
        self,
        ticker: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TradeResult]:
        params: dict = {"limit": limit, "offset": offset}
        if ticker:
            params["ticker"] = ticker
        data = self._get("/api/trades", **params)
        return [
            TradeResult(
                trade_id=t["trade_id"],
                ticker=t["ticker"],
                price=t["price"],
                quantity=t["quantity"],
                side=t["side"],
                counterparty_id=t["counterparty_id"],
                order_id=t["order_id"],
                created_at=t["created_at"],
            )
            for t in data
        ]

    def get_portfolio(self) -> Portfolio:
        data = self._get("/api/portfolio")
        return Portfolio(
            user_id=data["user_id"],
            username=data["username"],
            cash=data["cash"],
            buying_power=data["buying_power"],
            escrowed_cash=data["escrowed_cash"],
            holdings=[
                Holding(
                    ticker=h["ticker"],
                    quantity=h["quantity"],
                    current_price=h["current_price"],
                    value=h["value"],
                )
                for h in data["holdings"]
            ],
            total_value=data["total_value"],
        )
