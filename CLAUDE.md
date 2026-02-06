# Market-Sim

Simulated stock market with AI agent trading. FastAPI backend + React frontend.

## Quick Start

```bash
# Backend
uv run uvicorn backend.main:app --reload

# Frontend
cd frontend && npm run dev

# Tests (pytest is not installed globally — always use uv run)
uv run python -m pytest
```

## Architecture

- **Backend** (`backend/`): FastAPI, SQLAlchemy async, SQLite (`market.db`)
- **Frontend** (`frontend/`): React 18 + Vite + Tailwind + Zustand
- **Engine** (`backend/engine/`): In-memory Exchange → OrderBook → MatchingEngine
- **Auth**: JWT (Bearer header) for browser, API key (X-API-Key) for agents
- **DB** (`backend/db/`): models.py, crud.py, database.py — persists users/trades/portfolios
- **WebSocket** (`backend/ws/manager.py`): channels — `prices`, `trades:{ticker}`, `orderbook:{ticker}`

## API Endpoints

| Method | Path                           | Auth | Purpose                                 |
| ------ | ------------------------------ | ---- | --------------------------------------- |
| POST   | /api/register                  | No   | Create account → api_key + jwt          |
| POST   | /api/login                     | No   | Login → jwt                             |
| POST   | /api/orders                    | Yes  | Place order (GTC/IOC/FOK, rate-limited) |
| DELETE | /api/orders/{id}               | Yes  | Cancel resting order (rate-limited)     |
| GET    | /api/orders                    | Yes  | List open/partial orders                |
| GET    | /api/trades                    | Yes  | Trade history (optional ticker filter)  |
| GET    | /api/market/tickers            | No   | All tickers + prices                    |
| GET    | /api/market/{ticker}           | No   | Ticker detail + depth                   |
| GET    | /api/market/{ticker}/orderbook | No   | Aggregated book                         |
| GET    | /api/market/{ticker}/history   | No   | OHLCV candles (1m/5m/15m/1h/1d)         |
| GET    | /api/portfolio                 | Yes  | Holdings + cash + buying_power          |
| GET    | /api/leaderboard               | No   | Top 50 by total value                   |
| GET    | /api/health                    | No   | Health check                            |
| WS     | /ws/{channel}                  | No   | Real-time data                          |

## Workflow — READ BEFORE STARTING ANY TASK

### Observe → Orient → Decide → Act

1. **Observe**: Read the relevant files. Check what imports the code you're about to change. Understand blast radius before touching anything.
2. **Orient**: Contextualize against existing patterns in this file and `.claude/rules/`. Don't reinvent what's already established.
3. **Decide**: For tasks touching 3+ files or introducing a new pattern, use Plan Mode and get approval before writing code. Single-file fixes can go straight to implementation.
4. **Act**: Implement, test, update docs — in that order, as one unit of work.

### Code Quality — Three Questions

Every change must pass these checks:

- **Does it work?** — Tests pass. No regressions. Run the full suite, not just the new test.
- **Can a fresh reader follow it?** — Favor explicit, readable code over clever abstractions. If a function doesn't fit on screen (~30-40 lines), it probably does too many things — look for a natural split. Never extract a helper that's only called once.
- **Can it be changed without cascading breakage?** — New logic should be modular. Define the Pydantic model / interface before implementing the route or engine logic behind it.

### Testing Rules

- Write tests alongside code. For tricky logic (matching edge cases, escrow math), write the test first to clarify expected behavior.
- Every new route gets both a happy-path and an error-case test.
- Every engine logic change gets a test covering the edge case.

### Error Protocol

- **Two-strike rule**: If a fix attempt fails twice, stop. Re-read the error, identify the false assumption, and either try a fundamentally different approach or ask the user. Do not guess-and-retry in a loop.
- **Blast radius awareness**: Before editing a shared file (e.g., `engine/exchange.py`, `conftest.py`), check what depends on it. Scale your caution to how much can break.

### Checkpointing

- After completing a discrete feature (one roadmap item, one bug fix), suggest a commit before starting the next. Don't let working code go uncommitted while starting something new.

## Critical Patterns — READ BEFORE EDITING

1. **Exchange singleton**: Set via `api.dependencies.set_exchange()` in lifespan. Access via `Depends(get_exchange)`. Tests MUST call `set_exchange()` manually (lifespan doesn't run in test client).

2. **In-memory source of truth**: The Exchange holds the live order book and user balances. The DB is a persistence layer — don't query it for real-time state.

3. **Escrow model**: Cash (buys) or shares (sells) are deducted at order placement, not fill. Refunds happen on cancel or price improvement.

4. **`process_order` mutates quantity**: `MatchingEngine.process_order()` decrements `incoming_order.quantity` in-place. Always save the original quantity before calling it.

5. **Market maker**: Bot user has `is_market_maker=True` — skips cash/share validation. Quotes all tickers every 2 seconds at ±1% spread.

6. **DB access in routes**: Always use `Depends(get_db)` — never call `async_session()` directly. This is required for test overrides.

7. **Per-ticker locks**: `Exchange` uses `defaultdict(asyncio.Lock)` — each ticker has its own lock. Orders on different tickers can process concurrently.

8. **Time-in-force**: `Order.time_in_force` controls lifecycle: GTC (rests on book), IOC (fill what you can, refund rest), FOK (fill completely or reject pre-escrow). The `MatchingEngine.process_order()` `add_to_book` param controls whether unfilled remainder goes on the book.

9. **Rate limiting**: `RateLimiter` in `api/rate_limit.py` — sliding window per user ID. Applied to `POST /api/orders` and `DELETE /api/orders/{id}`. Configurable via `config.settings.RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`.

10. **Atomic DB writes**: CRUD helpers use `flush()` (not `commit()`). Route handlers call `db.commit()` once at the end, making all DB writes in a request atomic. The market maker bot commits in its own session after each quote cycle.

11. **WebSocket auth**: `ws_endpoint` accepts optional `token` and `api_key` query params. `_authenticate_ws()` validates them. All channels remain public; auth is stored per-connection for future user-specific channels.

## Testing

- **Run tests**: `uv run python -m pytest` — bare `pytest` won't work (not installed globally)
- `asyncio_mode = "auto"` (configured in `pyproject.toml`)
- `pythonpath = ["backend"]` — imports resolve from `backend/`
- 63 tests: 27 engine unit (`test_exchange.py`) + 36 API integration (`test_api.py`)
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

## Self-Updating Docs

When working on this project, keep documentation in sync with reality:

- **If a command fails** — fix the command in this file, `.claude/rules/`, and `memory/MEMORY.md` so it's never tried again.
- **If you add an endpoint** — add it to the API Endpoints table above and update ROADMAP.md checkboxes.
- **If you add/change a test** — update test counts in this file's Testing section.
- **If you discover a new pitfall** — add it to Common Pitfalls in `memory/MEMORY.md`.
- **If you add a new critical pattern** — add it to the Critical Patterns section above.

Do this as part of the task, not as a separate step.

## Known Issues (see ROADMAP.md)

Phases 1, 2, and 3 are complete. See ROADMAP.md for Phase 4+ items.
