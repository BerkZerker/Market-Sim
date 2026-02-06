# Market-Sim

Simulated stock market with AI agent trading. FastAPI backend + React frontend.

## Quick Start

```bash
# Backend
uv run uvicorn backend.main:app --reload

# Frontend
cd frontend && npm run dev

# Tests
pytest
```

## Architecture

- **Backend** (`backend/`): FastAPI, SQLAlchemy async, SQLite (`market.db`)
- **Frontend** (`frontend/`): React 18 + Vite + Tailwind + Zustand
- **Engine** (`backend/engine/`): In-memory Exchange → OrderBook → MatchingEngine
- **Auth**: JWT (Bearer header) for browser, API key (X-API-Key) for agents
- **DB** (`backend/db/`): models.py, crud.py, database.py — persists users/trades/portfolios
- **WebSocket** (`backend/ws/manager.py`): channels — `prices`, `trades:{ticker}`, `orderbook:{ticker}`

## API Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | /api/register | No | Create account → api_key + jwt |
| POST | /api/login | No | Login → jwt |
| POST | /api/orders | Yes | Place limit order |
| DELETE | /api/orders/{id} | Yes | Cancel resting order |
| GET | /api/market/tickers | No | All tickers + prices |
| GET | /api/market/{ticker} | No | Ticker detail + depth |
| GET | /api/market/{ticker}/orderbook | No | Aggregated book |
| GET | /api/portfolio | Yes | User holdings + cash |
| GET | /api/leaderboard | No | Top 50 by total value |
| GET | /api/health | No | Health check |
| WS | /ws/{channel} | No | Real-time data |

## Critical Patterns — READ BEFORE EDITING

1. **Exchange singleton**: Set via `api.dependencies.set_exchange()` in lifespan. Access via `Depends(get_exchange)`. Tests MUST call `set_exchange()` manually (lifespan doesn't run in test client).

2. **In-memory source of truth**: The Exchange holds the live order book and user balances. The DB is a persistence layer — don't query it for real-time state.

3. **Escrow model**: Cash (buys) or shares (sells) are deducted at order placement, not fill. Refunds happen on cancel or price improvement.

4. **`process_order` mutates quantity**: `MatchingEngine.process_order()` decrements `incoming_order.quantity` in-place. Always save the original quantity before calling it.

5. **Market maker**: Bot user has `is_market_maker=True` — skips cash/share validation. Quotes all tickers every 2 seconds at ±1% spread.

6. **DB access in routes**: Always use `Depends(get_db)` — never call `async_session()` directly. This is required for test overrides.

7. **Per-ticker locks**: `Exchange` uses `defaultdict(asyncio.Lock)` — each ticker has its own lock. Orders on different tickers can process concurrently.

## Testing

- `pytest` with `asyncio_mode = "auto"` (configured in `pyproject.toml`)
- `pythonpath = ["backend"]` — imports resolve from `backend/`
- 35 tests: 21 engine unit (`test_exchange.py`) + 14 API integration (`test_api.py`)
- `conftest.py` creates an in-memory SQLite DB + fresh Exchange per test

## Code Style

- Ruff: line-length 88, rules E/F/I
- Async/await everywhere — no sync DB calls
- Type hints on function signatures
- FastAPI dependency injection for all shared state

## Frontend

- Vite proxies `/api` → `localhost:8000`, `/ws` → `ws://localhost:8000`
- Zustand store (`stores/useStore.ts`) — user auth, market prices, order book
- Auth persisted to localStorage
- Pages: Dashboard, Ticker detail, Portfolio, Leaderboard, Login, Register

## Known Issues (see ROADMAP.md)

All Phase 1 issues are resolved. See ROADMAP.md for Phase 2+ items.
