# Market Sim

A stock market simulation platform where AI agents trade via API, with a live React dashboard. Features a continuous double auction market with real-time WebSocket price feeds, order book visualization, and a leaderboard.

## Features

- **Trading API**: Register, authenticate (JWT or API key), and place limit orders
- **5 Tickers**: FUN, MEME, YOLO, HODL, PUMP — each with configurable starting prices
- **Market Makers**: Automated bots provide liquidity on all tickers
- **Order Validation**: Escrow model — cash/shares deducted when orders are placed
- **Real-time WebSocket**: Live price feeds, order book updates, and trade notifications
- **React Dashboard**: Price cards, charts, order books, portfolio, and leaderboard
- **Dual Auth**: JWT for browser sessions, API keys for AI agents

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

## API Endpoints

| Method | Endpoint                         | Auth | Description                 |
| ------ | -------------------------------- | ---- | --------------------------- |
| POST   | `/api/register`                  | No   | Create account, get API key |
| POST   | `/api/login`                     | No   | Login, get JWT token        |
| POST   | `/api/orders`                    | Yes  | Place a limit order         |
| GET    | `/api/market/tickers`            | No   | All tickers with prices     |
| GET    | `/api/market/{ticker}`           | No   | Single ticker info          |
| GET    | `/api/market/{ticker}/orderbook` | No   | Aggregated order book       |
| GET    | `/api/portfolio`                 | Yes  | Your cash and holdings      |
| GET    | `/api/leaderboard`               | No   | Top 50 by portfolio value   |
| GET    | `/api/health`                    | No   | Health check                |

### Authentication

Include one of these headers:

- `Authorization: Bearer <jwt_token>` (from login)
- `X-API-Key: <api_key>` (from registration)

### WebSocket Channels

Connect to `ws://localhost:8000/ws/{channel}`:

- `prices` — all ticker prices on every trade
- `trades:{ticker}` — individual trades for a ticker
- `orderbook:{ticker}` — throttled order book snapshots

## Example: AI Agent

```bash
uv add requests
uv run python examples/simple_agent.py
```

This registers an agent, checks prices, places random orders, and displays the portfolio.

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
├── core/                   # Data models
│   ├── order.py            # Order dataclass
│   ├── trade.py            # Trade dataclass
│   └── user.py             # User dataclass
├── engine/                 # Market mechanics
│   ├── exchange.py         # Multi-ticker exchange with validation
│   ├── matching_engine.py  # Price-time priority matching
│   └── orderbook.py        # Sorted bid/ask lists
├── db/                     # Persistence (SQLAlchemy + SQLite)
│   ├── database.py         # Async engine and session
│   ├── models.py           # DB tables
│   └── crud.py             # Database operations
├── bots/
│   └── market_maker.py     # Liquidity bot
└── ws/
    └── manager.py          # WebSocket broadcast manager

frontend/                   # React + Vite + Tailwind
├── src/
│   ├── pages/              # Dashboard, Ticker, Portfolio, Leaderboard, Auth
│   ├── components/         # PriceChart, OrderBookView, OrderForm, etc.
│   ├── stores/             # Zustand state management
│   └── api/                # HTTP client and WebSocket client
```

## Development

```bash
# Linting
ruff check backend/
ruff format backend/

# Tests
uv run pytest tests/ -v
```

## Design Decisions

- **SQLite** — no external database needed, keeps deployment simple
- **In-memory order book** — Exchange is source of truth; DB persists users/trades/portfolios
- **Escrow model** — cash/shares deducted on order placement, not on fill
- **asyncio.Lock** — serializes all order processing (sufficient for this scale)
- **Market makers are infrastructure** — they start with the server and rebuild the order book
