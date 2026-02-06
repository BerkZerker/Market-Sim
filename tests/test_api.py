import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    resp = await client.post(
        "/api/register",
        json={"username": "testuser", "password": "testpass"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"
    assert "api_key" in data
    assert "jwt_token" in data
    assert data["cash"] == 10000.0

    # Login
    resp = await client.post(
        "/api/login",
        json={"username": "testuser", "password": "testpass"},
    )
    assert resp.status_code == 200
    assert "jwt_token" in resp.json()


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post(
        "/api/register",
        json={"username": "dup_user", "password": "testpass"},
    )
    resp = await client.post(
        "/api/register",
        json={"username": "dup_user", "password": "testpass"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/register",
        json={"username": "logintest", "password": "correct"},
    )
    resp = await client.post(
        "/api/login",
        json={"username": "logintest", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_market_tickers(client: AsyncClient):
    resp = await client.get("/api/market/tickers")
    assert resp.status_code == 200
    tickers = resp.json()["tickers"]
    assert "FUN" in tickers
    assert "MEME" in tickers


@pytest.mark.asyncio
async def test_orderbook(client: AsyncClient):
    resp = await client.get("/api/market/FUN/orderbook")
    assert resp.status_code == 200
    data = resp.json()
    assert "bids" in data
    assert "asks" in data


@pytest.mark.asyncio
async def test_place_order_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/api/orders",
        json={"ticker": "FUN", "side": "buy", "price": 100.0, "quantity": 1},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_place_order_with_api_key(client: AsyncClient):
    # Register
    resp = await client.post(
        "/api/register",
        json={"username": "trader1", "password": "pass1234"},
    )
    api_key = resp.json()["api_key"]

    # Place order
    resp = await client.post(
        "/api/orders",
        json={"ticker": "FUN", "side": "buy", "price": 99.0, "quantity": 5},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "FUN"
    assert data["side"] == "buy"
    assert data["status"] in ("open", "partial", "filled")


@pytest.mark.asyncio
async def test_portfolio(client: AsyncClient):
    resp = await client.post(
        "/api/register",
        json={"username": "portfolio_user", "password": "pass1234"},
    )
    token = resp.json()["jwt_token"]

    resp = await client.get(
        "/api/portfolio",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cash"] == 10000.0
    assert data["username"] == "portfolio_user"


@pytest.mark.asyncio
async def test_leaderboard(client: AsyncClient):
    # Register a user first
    await client.post(
        "/api/register",
        json={"username": "leader_user", "password": "pass1234"},
    )

    resp = await client.get("/api/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "leaderboard" in data
