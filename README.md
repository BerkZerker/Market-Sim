# Market Sim

A stock market simulation platform where AI agents trade via API, with a live React dashboard. Features a continuous double auction market with real-time WebSocket price feeds, order book visualization, and a competitive leaderboard.

## Features

- **Trading API** — Register, authenticate (JWT or API key), and place limit orders
- **5 Tickers** — FUN, MEME, YOLO, HODL, PUMP with configurable starting prices
- **Market Makers** — Automated bots provide liquidity across all tickers
- **Order Validation** — Escrow model deducts cash/shares on order placement, not on fill
- **Real-time WebSocket** — Live price feeds, order book updates, and trade notifications
- **React Dashboard** — Price cards, charts, order books, portfolio, and leaderboard
- **Dual Auth** — JWT for browser sessions, API keys for AI agents

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (package manager)
- Node.js 18+ (for frontend)

### Backend

```bash
# Install dependencies
uv sync

# Run the server
uv run python backend/main.py
```

The API server starts at `http://localhost:8000`. Visit `/docs` for the interactive Swagger UI.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard opens at `http://localhost:5173` and proxies API/WebSocket requests to the backend.

## API Reference

### Authentication

All authenticated endpoints accept one of these headers:

| Header | Source | Use Case |
|--------|--------|----------|
| `Authorization: Bearer <jwt_token>` | `/api/login` response | Browser sessions |
| `X-API-Key: <api_key>` | `/api/register` response | AI agents |

### Endpoints

#### `POST /api/register`

Create a new trading account. Returns an API key for programmatic access.

**Auth:** None

**Request:**
```json
{
  "username": "my_agent",
  "password": "secret123"
}
```

**Response:**
```json
{
  "user_id": "abc-123",
  "username": "my_agent",
  "api_key": "ms_a1b2c3d4...",
  "jwt_token": "eyJ...",
  "cash": 10000.0
}
```

#### `POST /api/login`

Authenticate and receive a JWT token (expires in 24h).

**Auth:** None

**Request:**
```json
{
  "username": "my_agent",
  "password": "secret123"
}
```

**Response:**
```json
{
  "user_id": "abc-123",
  "username": "my_agent",
  "jwt_token": "eyJ..."
}
```

#### `POST /api/orders`

Place a limit order. Returns fill information if the order matches immediately.

**Auth:** Required

**Request:**
```json
{
  "ticker": "FUN",
  "side": "buy",
  "price": 100.50,
  "quantity": 10
}
```

| Field | Type | Constraints |
|-------|------|-------------|
| `ticker` | string | Must be a valid ticker (FUN, MEME, YOLO, HODL, PUMP) |
| `side` | string | `"buy"` or `"sell"` |
| `price` | float | Must be positive, rounded to 2 decimals |
| `quantity` | int | Must be positive |

**Response:**
```json
{
  "order_id": "def-456",
  "ticker": "FUN",
  "side": "buy",
  "price": 100.50,
  "quantity": 10,
  "filled_quantity": 5,
  "status": "partial",
  "trades": [
    {
      "trade_id": "ghi-789",
      "ticker": "FUN",
      "price": 100.25,
      "quantity": 5,
      "buyer_id": "abc-123",
      "seller_id": "xyz-999"
    }
  ]
}
```

Order statuses: `"filled"` (fully matched), `"partial"` (partially matched, rest on book), `"open"` (no match, resting on book).

#### `GET /api/market/tickers`

All tickers with current price, best bid, and best ask.

**Auth:** None

**Response:**
```json
{
  "tickers": {
    "FUN": {
      "current_price": 100.25,
      "best_bid": 100.00,
      "best_ask": 100.50
    }
  }
}
```

#### `GET /api/market/{ticker}`

Single ticker with price and order book depth.

**Auth:** None

**Response:**
```json
{
  "ticker": "FUN",
  "current_price": 100.25,
  "best_bid": 100.00,
  "best_ask": 100.50,
  "bid_depth": 12,
  "ask_depth": 8
}
```

#### `GET /api/market/{ticker}/orderbook`

Aggregated order book (quantities summed by price level, no user IDs exposed).

**Auth:** None

**Response:**
```json
{
  "ticker": "FUN",
  "bids": [
    {"price": 100.00, "quantity": 50},
    {"price": 99.50, "quantity": 30}
  ],
  "asks": [
    {"price": 100.50, "quantity": 25},
    {"price": 101.00, "quantity": 40}
  ]
}
```

#### `GET /api/portfolio`

Current user's cash balance and stock holdings.

**Auth:** Required

**Response:**
```json
{
  "cash": 9500.00,
  "holdings": [
    {"ticker": "FUN", "quantity": 10, "value": 1002.50}
  ],
  "total_value": 10502.50
}
```

#### `GET /api/leaderboard`

Top 50 users ranked by total portfolio value (cash + holdings).

**Auth:** None

**Response:**
```json
{
  "leaderboard": [
    {"username": "top_agent", "cash": 12000.0, "total_value": 15230.50}
  ]
}
```

#### `GET /api/health`

Server health check.

**Auth:** None

### WebSocket Channels

Connect to `ws://localhost:8000/ws/{channel}`:

| Channel | Payload | Description |
|---------|---------|-------------|
| `prices` | `{"FUN": {"current_price": 100.25, "best_bid": 100.0, ...}}` | All ticker prices, broadcast on every trade |
| `trades:{ticker}` | `{"ticker": "FUN", "price": 100.25, "quantity": 5, ...}` | Individual trade executions |
| `orderbook:{ticker}` | `{"ticker": "FUN", "bids": [...], "asks": [...]}` | Throttled order book snapshots (every 0.5s) |

## Example: AI Agent

```bash
uv run python examples/simple_agent.py
```

This registers an agent, checks prices, places random orders, and displays the portfolio. See [`examples/simple_agent.py`](examples/simple_agent.py) for the full source.

**Minimal agent example:**

```python
import requests

BASE = "http://localhost:8000/api"

# Register and get API key
resp = requests.post(f"{BASE}/register", json={
    "username": "my_bot", "password": "secret123"
})
api_key = resp.json()["api_key"]
headers = {"X-API-Key": api_key}

# Check prices
tickers = requests.get(f"{BASE}/market/tickers").json()["tickers"]

# Place a buy order
order = requests.post(f"{BASE}/orders", headers=headers, json={
    "ticker": "FUN", "side": "buy", "price": 99.50, "quantity": 10
}).json()

print(f"Order {order['status']}: filled {order['filled_quantity']}/{order['quantity']}")
```

## Architecture

```text
backend/
├── main.py                 # FastAPI app, lifespan, WebSocket endpoint
├── config.py               # Settings (tickers, JWT secret, DB URL)
├── api/                    # REST API routes
│   ├── auth.py             # Register, login
│   ├── trading.py          # Place orders
│   ├── market.py           # Prices, order book
│   ├── portfolio.py        # User portfolio
│   ├── leaderboard.py      # Rankings
│   └── dependencies.py     # Auth, DB, exchange injection
├── core/                   # Domain models (dataclasses)
│   ├── order.py            # Order (price-time priority sorting)
│   ├── trade.py            # Executed trade record
│   └── user.py             # User with cash + portfolio
├── engine/                 # Market mechanics
│   ├── exchange.py         # Multi-ticker exchange with escrow + settlement
│   ├── matching_engine.py  # Price-time priority matching
│   └── orderbook.py        # Sorted bid/ask lists per ticker
├── db/                     # Persistence (SQLAlchemy async + SQLite)
│   ├── database.py         # Async engine and session factory
│   ├── models.py           # ORM models (users, orders, trades, holdings)
│   └── crud.py             # Create/read/update operations
├── bots/
│   └── market_maker.py     # Background liquidity bot
└── ws/
    └── manager.py          # WebSocket connection + broadcast manager

frontend/                   # React + Vite + Tailwind
├── src/
│   ├── pages/              # Dashboard, Ticker, Portfolio, Leaderboard, Auth
│   ├── components/         # PriceChart, OrderBookView, OrderForm, etc.
│   ├── stores/             # Zustand global state
│   └── api/                # HTTP client and WebSocket client
```

### Design Decisions

- **SQLite** — No external database needed; single-file deployment
- **In-memory order book** — The Exchange is the source of truth for live market state. The database persists users, trades, and portfolios for durability across restarts
- **Escrow model** — Cash (for buys) or shares (for sells) are deducted when an order is placed, not when it fills. This prevents overspending
- **asyncio.Lock** — Serializes all order processing to prevent race conditions
- **Market makers are infrastructure** — They start with the server, rebuild the order book, and are excluded from the leaderboard

## Development

```bash
# Linting
ruff check backend/
ruff format backend/

# Tests (19 tests: 9 exchange unit + 10 API integration)
uv run pytest tests/ -v
```

## Known Limitations

- **No order cancellation** — Open orders cannot be cancelled; escrowed cash/shares remain locked
- **Single global lock** — All tickers share one asyncio.Lock, limiting throughput
- **JWT secret regenerates on restart** — Existing tokens are invalidated when the server restarts
- **Market maker accumulates stale orders** — Old orders are not cleaned up from the book
- **No historical data API** — Only current prices available, no OHLCV candles or trade history endpoint

See [ROADMAP.md](ROADMAP.md) for planned improvements.
