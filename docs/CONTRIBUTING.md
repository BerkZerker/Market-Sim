# Contributing to Market-Sim

Guide for developers contributing to the project.

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Backend

```bash
# Install Python dependencies (including dev tools)
uv sync --all-extras

# Run the backend
uv run uvicorn backend.main:app --reload

# Run tests
uv run python -m pytest

# Run tests with coverage
uv run python -m pytest --cov=backend --cov-report=term-missing

# Lint
uv run ruff check backend/
uv run ruff format --check backend/
```

### Frontend

```bash
cd frontend

# Install dependencies
npm ci

# Run dev server (proxies /api and /ws to localhost:8000)
npm run dev

# Run tests
npm test

# Type check
npx tsc --noEmit

# Production build
npm run build
```

### Full Stack (Docker)

```bash
docker compose up --build
# App available at http://localhost:8000
```

---

## Project Structure

```
Market-Sim/
├── backend/          # FastAPI application
│   ├── api/          # HTTP route handlers
│   ├── bots/         # Market maker bot
│   ├── core/         # Domain objects (Order, Trade, User)
│   ├── db/           # SQLAlchemy models, CRUD, session
│   ├── engine/       # Exchange, OrderBook, MatchingEngine
│   └── ws/           # WebSocket connection manager
├── frontend/         # React + Vite + Tailwind
│   └── src/
│       ├── api/      # REST + WebSocket clients
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       └── stores/   # Zustand state
├── sdk/              # Python SDK for bot developers
├── tests/            # Backend test suite
├── docs/             # Documentation
└── deploy/           # Deployment scripts
```

See `docs/ARCHITECTURE.md` for detailed architecture documentation.

---

## Workflow

### Before Starting

1. Read `CLAUDE.md` — it has critical patterns you must follow
2. Read the relevant `.claude/rules/` file for the area you're working in
3. Check `ROADMAP.md` for context on what's been done and what's planned

### Making Changes

1. **Understand first**: Read the files you'll modify. Check what imports them. Understand blast radius.
2. **Write tests alongside code**: Every new route needs happy-path + error-case tests. Every engine change needs an edge-case test.
3. **One commit per feature**: Don't mix unrelated changes.
4. **Run the full suite**: `uv run python -m pytest` (backend) and `cd frontend && npm test` (frontend). Don't skip unrelated tests.

### Code Style

**Backend (Python)**:
- Ruff enforced: line length 88, rules E/F/I
- Async/await everywhere — no sync DB calls
- Type hints on function signatures
- FastAPI dependency injection for shared state
- CRUD helpers use `flush()` — route handlers call `commit()` once

**Frontend (TypeScript)**:
- Tailwind for styling — no CSS modules
- Zustand for state — no Redux or Context for global state
- React Router v6 for routing
- Vitest + React Testing Library for tests

### Critical Rules

These will save you debugging time:

1. **Never import `async_session()` directly in route handlers** — use `Depends(get_db)`. Required for test overrides.

2. **Save `order.quantity` before calling `process_order()`** — it mutates the value in-place.

3. **Market maker users skip validation** — `is_market_maker=True` bypasses cash/share checks.

4. **Tests must call `set_exchange()`** — the app lifespan doesn't run under the test client.

5. **Always use `uv run python -m pytest`** — bare `pytest` is not installed globally.

6. **Schema changes require DB wipe** (until Alembic is added) — `rm market.db` before restarting.

---

## Testing

### Backend Tests (63 tests)

```bash
uv run python -m pytest                    # Run all
uv run python -m pytest tests/test_exchange.py  # Engine only (27 tests)
uv run python -m pytest tests/test_api.py       # API only (36 tests)
uv run python -m pytest -k "test_place"         # Filter by name
uv run python -m pytest -x                      # Stop on first failure
```

**Test architecture**:
- `conftest.py` creates in-memory SQLite DB + fresh Exchange per test
- Engine tests (`test_exchange.py`) test the Exchange directly — no HTTP, no DB
- API tests (`test_api.py`) use `httpx.AsyncClient` with the FastAPI app

**When to add tests**:
- New route → happy-path + error-case in `test_api.py`
- New engine logic → edge case in `test_exchange.py`
- Bug fix → regression test proving the fix

### Frontend Tests (46 tests)

```bash
cd frontend
npm test                    # Run all
npm run test:watch          # Watch mode
```

**Test architecture**:
- Vitest + React Testing Library + jsdom
- Mocks for fetch, WebSocket, localStorage, lightweight-charts
- Store mocks in `src/test/mocks.ts`

---

## Adding a New API Endpoint

Step-by-step:

### 1. Define the Pydantic models

```python
# In the relevant api/ file
class MyRequest(BaseModel):
    field: str

class MyResponse(BaseModel):
    result: str
```

### 2. Write the route handler

```python
@router.get("/my-endpoint", response_model=MyResponse)
async def my_endpoint(
    user: User = Depends(get_current_user),  # if auth required
    db: AsyncSession = Depends(get_db),
    exchange: Exchange = Depends(get_exchange),
):
    # Your logic here
    return MyResponse(result="ok")
```

### 3. Write tests

```python
# In tests/test_api.py
async def test_my_endpoint(client):
    # Register a user first
    resp = await client.post("/api/register", json={"username": "test", "password": "testpass"})
    token = resp.json()["jwt_token"]

    # Call your endpoint
    resp = await client.get("/api/my-endpoint", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["result"] == "ok"

async def test_my_endpoint_unauthorized(client):
    resp = await client.get("/api/my-endpoint")
    assert resp.status_code == 401
```

### 4. Update documentation

- Add to the API Endpoints table in `CLAUDE.md`
- Update test counts in `CLAUDE.md` and `memory/MEMORY.md`
- Check `ROADMAP.md` box if this completes a roadmap item

---

## Adding Engine Logic

Step-by-step for changes to the matching/order/escrow logic:

### 1. Write the test first

```python
# In tests/test_exchange.py
async def test_my_edge_case(exchange, buyer, seller):
    # Set up the scenario
    sell_order = Order(price=100.0, quantity=10, user_id=seller.user_id)
    await exchange.place_order("FUN", sell_order, "sell")

    # Execute the action
    buy_order = Order(price=100.0, quantity=5, user_id=buyer.user_id)
    trades, status = await exchange.place_order("FUN", buy_order, "buy")

    # Assert the expected outcome
    assert status == "filled"
    assert len(trades) == 1
    assert buyer.cash == 9500.0  # 10000 - (100 * 5)
```

### 2. Implement the logic

Make the test pass. Key files:
- `backend/engine/exchange.py` — escrow, settlement, refunds
- `backend/engine/matching_engine.py` — order matching
- `backend/engine/orderbook.py` — book management

### 3. Run full suite

```bash
uv run python -m pytest
```

Engine changes can have subtle effects on escrow math. Always run all tests.

---

## Pull Request Checklist

Before submitting:

- [ ] All backend tests pass: `uv run python -m pytest`
- [ ] All frontend tests pass: `cd frontend && npm test`
- [ ] Linting passes: `uv run ruff check backend/ && uv run ruff format --check backend/`
- [ ] TypeScript compiles: `cd frontend && npx tsc --noEmit`
- [ ] New endpoints have both happy-path and error-case tests
- [ ] New engine logic has edge-case tests
- [ ] Documentation updated (CLAUDE.md, ROADMAP.md if applicable)
- [ ] No hardcoded secrets or credentials
- [ ] No `print()` statements (use `logging`)

---

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| `pytest` not found | Use `uv run python -m pytest` |
| Test fails with "Exchange not initialized" | Call `set_exchange()` in test fixture |
| `async_session` import fails in test | Override via `db_module.async_session` in conftest |
| Schema changed, old DB incompatible | Delete `market.db` and restart |
| Frontend mock WebSocket fails | Use `class` syntax, not `vi.fn()` |
| `useTheme` test flaky | Wrap assertions in async `act()` |
| `uv sync --dev` misses deps | Use `uv sync --all-extras` instead |
