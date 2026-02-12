# Architecture

Deep dive into Market-Sim's system design, data flow, and key design decisions.

---

## System Overview

```
                    ┌──────────────────────────────────────────────┐
                    │                   Caddy                       │
                    │         (TLS, static files, proxy)            │
                    └────────────┬───────────────┬─────────────────┘
                                 │               │
                          HTTP/REST         WebSocket
                                 │               │
                    ┌────────────▼───────────────▼─────────────────┐
                    │              FastAPI App                      │
                    │                                              │
                    │  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
                    │  │ API      │  │ WS       │  │ Bots      │  │
                    │  │ Routes   │  │ Manager  │  │ (MM Bot)  │  │
                    │  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
                    │       │             │              │         │
                    │  ┌────▼─────────────▼──────────────▼──────┐  │
                    │  │           Exchange (Singleton)          │  │
                    │  │                                        │  │
                    │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │  │
                    │  │  │OrderBook│ │OrderBook│ │OrderBook│  │  │
                    │  │  │  FUN   │ │  MEME  │ │  YOLO  │  │  │
                    │  │  │+Engine │ │+Engine │ │+Engine │  │  │
                    │  │  └────────┘ └────────┘ └────────┘  │  │
                    │  │                                        │  │
                    │  │  Users: dict[UUID, User]               │  │
                    │  │  Locks: defaultdict(asyncio.Lock)      │  │
                    │  └────────────────────────────────────────┘  │
                    │                                              │
                    │  ┌────────────────────────────────────────┐  │
                    │  │          SQLAlchemy (Async)             │  │
                    │  │    Users | Orders | Trades | Holdings   │  │
                    │  └──────────────────┬─────────────────────┘  │
                    └─────────────────────┼────────────────────────┘
                                          │
                                ┌─────────▼─────────┐
                                │   PostgreSQL       │
                                │   (persistence)    │
                                └───────────────────┘
```

---

## Component Breakdown

### 1. Exchange (Source of Truth for Live State)

**File**: `backend/engine/exchange.py`

The Exchange is the central component. It holds:
- All order books (one per ticker)
- All matching engines (one per ticker)
- All registered users (with their cash and portfolio)
- Per-ticker asyncio locks
- Last trade prices

**Key principle**: The in-memory Exchange is the **source of truth** for order book state, user balances, and active orders. The database is a **persistence layer** that records history and survives restarts.

```
Exchange
├── order_books: dict[str, OrderBook]       # Live order books
├── matching_engines: dict[str, MatchingEngine]  # Per-ticker matchers
├── users: dict[UUID, User]                 # All user state (cash, portfolio)
├── last_trades: dict[str, float]           # Latest price per ticker
├── _locks: defaultdict(asyncio.Lock)       # Per-ticker concurrency control
└── on_trades: Callable                     # WebSocket broadcast callback
```

### 2. OrderBook

**File**: `backend/engine/orderbook.py`

Maintains two sorted lists:
- **Bids**: Descending by price, then ascending by timestamp (highest bid first)
- **Asks**: Ascending by price, then ascending by timestamp (lowest ask first)

This implements **price-time priority** (FIFO at each price level).

```
OrderBook("FUN")
├── bids: [Order(99.5, t=1), Order(99.0, t=2), Order(98.0, t=3)]
└── asks: [Order(100.5, t=1), Order(101.0, t=2), Order(102.0, t=3)]
```

### 3. MatchingEngine

**File**: `backend/engine/matching_engine.py`

Stateless processor. Given an incoming order and a side, it:
1. Walks the opposite side of the book
2. Matches at the **resting order's price** (not the incoming order's price)
3. Creates Trade objects for each fill
4. Mutates `incoming_order.quantity` in-place (decrements as it fills)
5. Optionally adds unfilled remainder to the book (`add_to_book` param)

**Critical**: Always save `order.quantity` before calling `process_order()` — it mutates the value.

### 4. API Layer

**File**: `backend/api/` directory

Stateless HTTP handlers. Each route:
1. Validates input (Pydantic models)
2. Gets dependencies via FastAPI DI (`get_exchange`, `get_db`, `get_current_user`)
3. Calls Exchange methods for trading logic
4. Persists to DB via CRUD helpers
5. Commits the DB transaction once at the end (atomic)

```
api/
├── auth.py         # POST /register, POST /login
├── trading.py      # POST/DELETE/GET /orders, GET /trades
├── market.py       # GET /market/tickers, /market/{ticker}, /orderbook, /history
├── portfolio.py    # GET /portfolio
├── leaderboard.py  # GET /leaderboard
├── dependencies.py # DI: get_exchange, get_db, get_current_user, JWT helpers
└── rate_limit.py   # Sliding window rate limiter
```

### 5. Database Layer

**File**: `backend/db/` directory

SQLAlchemy async ORM with these models:

```
UserModel
├── id: str (UUID primary key)
├── username: str (unique)
├── password_hash: str (bcrypt)
├── api_key: str (UUID, unique)
├── cash: float
├── is_market_maker: bool
└── created_at: datetime

PortfolioHolding
├── id: int (autoincrement)
├── user_id: str (FK → users)
├── ticker: str
└── quantity: int
    (unique constraint on user_id + ticker)

OrderModel
├── id: str (UUID primary key)
├── user_id: str (FK → users, indexed)
├── ticker: str (indexed)
├── side: str
├── price: float
├── quantity: int
├── filled_quantity: int
├── status: str ("open", "partial", "filled", "cancelled")
├── time_in_force: str ("GTC", "IOC", "FOK")
└── created_at: datetime

TradeModel
├── id: str (UUID primary key)
├── ticker: str (indexed)
├── price: float
├── quantity: int
├── buyer_id: str (FK → users, indexed)
├── seller_id: str (FK → users, indexed)
├── buy_order_id: str
├── sell_order_id: str
└── created_at: datetime
```

**Key pattern**: CRUD helpers use `flush()` (not `commit()`). Route handlers call `db.commit()` **once** at the end of the request, making all DB writes atomic.

### 6. WebSocket Manager

**File**: `backend/ws/manager.py`

Channel-based pub/sub:
- Clients connect to `/ws/{channel}` (e.g., `/ws/prices`, `/ws/trades:FUN`)
- Manager maintains per-channel connection lists
- Broadcasts are triggered by `Exchange.on_trades` callback
- Order book broadcasts are throttled to 0.5s minimum interval

```
ConnectionManager
├── channels: dict[str, list[WebSocket]]   # channel → subscribers
├── _user_ids: dict[WebSocket, str|None]   # auth info per connection
└── _last_orderbook_broadcast: dict[str, float]  # throttle tracking
```

### 7. Market Maker Bot

**File**: `backend/bots/market_maker.py`

Background asyncio task that provides liquidity:
1. Every 2 seconds, for each ticker:
   - Cancel all existing orders for the MM user
   - Get current price
   - Place bid at `price * 0.99` and ask at `price * 1.01`
   - Random quantity 5-20 shares per side
2. Persists all orders/trades to DB each cycle
3. Uses `is_market_maker=True` — skips cash/share validation

---

## Data Flow

### Order Placement Flow

```
Client → POST /api/orders
    │
    ▼
[Route Handler: validate input, check rate limit]
    │
    ▼
[Exchange.place_order(ticker, order, side)]
    │
    ├── Acquire per-ticker lock
    ├── FOK pre-check (if applicable)
    ├── Escrow: deduct cash (buy) or shares (sell)
    ├── MatchingEngine.process_order()
    │   ├── Walk opposite side of book
    │   ├── Match at resting order's price
    │   └── Return list of Trade objects
    ├── Settle: credit buyer shares, credit seller cash
    ├── Refund: price improvement (buys), IOC remainder
    ├── Release lock
    └── Fire on_trades callback → WebSocket broadcasts
    │
    ▼
[Route Handler: persist to DB]
    ├── record_order()
    ├── record_trade() for each fill
    ├── sync_user_to_db() for all affected users
    ├── update_order_fill() for resting orders that matched
    └── db.commit()  ← single atomic commit
    │
    ▼
[Return OrderResponse to client]
```

### WebSocket Broadcast Flow

```
Exchange.on_trades(ticker, trades)
    │
    ├── asyncio.create_task(manager.broadcast_trades(ticker, trades))
    │   └── Send to all /ws/trades:{ticker} subscribers
    │
    ├── asyncio.create_task(manager.broadcast_prices(exchange))
    │   └── Send to all /ws/prices subscribers
    │
    └── asyncio.create_task(manager.broadcast_orderbook(ticker, exchange))
        └── Send to all /ws/orderbook:{ticker} subscribers
            (throttled: max once per 0.5s per ticker)
```

### Authentication Flow

```
[Request arrives with Authorization or X-API-Key header]
    │
    ▼
[get_current_user() dependency]
    │
    ├── If Authorization: Bearer <token>
    │   └── decode_jwt(token) → user_id
    │
    ├── If X-API-Key: <key>
    │   └── DB lookup: get_user_by_api_key(key) → user_id
    │
    ├── If neither → 401 Unauthorized
    │
    ▼
[Exchange.get_user(UUID(user_id))]
    │
    ├── Found → return User object
    └── Not found → 500 "User not loaded in exchange"
```

---

## Concurrency Model

### Per-Ticker Locking

Each ticker has its own `asyncio.Lock`. This means:
- Orders on FUN and MEME can process **concurrently**
- Orders on the same ticker process **sequentially**
- The market maker bot acquires the same per-ticker locks

```python
self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

async with self._locks[ticker]:
    # Only one coroutine at a time per ticker
    trades = engine.process_order(order, side, add_to_book)
```

### Why Not a Global Lock?

A global lock would serialize ALL orders across ALL tickers. With 5 tickers and high activity, this creates unnecessary contention. Per-ticker locks allow 5x throughput.

### Single-Process Constraint

The Exchange is an in-memory singleton. It **cannot** be shared across multiple Uvicorn workers. This means:
- Production runs a **single worker** (vertically scaled)
- To scale beyond one process, you'd need to externalize state (Redis/shared memory)
- For 100-1,000 users, a single process on a 4-core VPS is sufficient

---

## State Management

### In-Memory (Exchange)

| Data | Lives In | Updated By |
|------|----------|------------|
| Order books (bids/asks) | `Exchange.order_books` | `place_order()`, `cancel_order()` |
| User cash & portfolio | `Exchange.users` | `place_order()`, `cancel_order()` |
| Last trade prices | `Exchange.last_trades` | `place_order()` |
| WebSocket subscriptions | `ConnectionManager.channels` | `connect()`, `disconnect()` |
| Rate limit counters | `RateLimiter._requests` | `check()` |

### Database (PostgreSQL)

| Data | Table | Updated By |
|------|-------|------------|
| User accounts | `users` | Registration, `sync_user_to_db()` |
| Portfolio holdings | `portfolio_holdings` | `sync_user_to_db()` |
| Order records | `orders` | `record_order()`, `update_order_fill()`, `cancel_order_db()` |
| Trade records | `trades` | `record_trade()` |

### Synchronization

- **Startup**: DB → Exchange (load all users with holdings)
- **Runtime**: Exchange is truth, DB writes happen after each request's Exchange mutations
- **Shutdown**: Exchange → DB (persist final user state)
- **Crash**: Last committed DB state is restored on next startup. Any in-flight orders not committed are lost.

---

## Design Decisions & Trade-offs

### Why In-Memory Order Book (Not DB)?

**Speed**. Order matching must be fast (<1ms per order for a good UX). Database queries add 1-10ms of latency per operation. The in-memory approach gives us:
- O(1) best-bid/best-ask lookup
- O(N) matching (where N = depth of fills, usually small)
- No I/O during the critical matching path

**Trade-off**: Data loss on crash. Mitigated by persisting every trade to DB immediately after matching.

### Why SQLite → PostgreSQL?

SQLite uses a single-writer lock. With concurrent HTTP requests + market maker bot + WebSocket broadcasts all writing to the DB, writes serialize and become a bottleneck at ~50 concurrent users. PostgreSQL supports concurrent writes with row-level locking.

### Why Per-Ticker Locks (Not Lock-Free)?

Lock-free data structures are complex to implement correctly in Python. Per-ticker locks give us:
- Correctness: no race conditions within a ticker
- Concurrency: different tickers process in parallel
- Simplicity: standard asyncio.Lock, easy to reason about

For our scale (100-1,000 users), this is sufficient. Lock contention only matters under extreme load on a single ticker.

### Why Single Container (Not Microservices)?

Market-Sim is a monolith by design. The Exchange, API, and WebSocket manager share in-memory state. Splitting them into microservices would require:
- Redis for shared Exchange state
- Message queue for trade events
- Service discovery and health checking

This complexity isn't justified at our scale. A well-structured monolith on a 4-core VPS handles 1,000 users easily.

### Why Caddy (Not Nginx)?

- Automatic HTTPS with zero configuration
- Simpler config syntax (Caddyfile vs nginx.conf)
- Built-in HTTP/2 and HTTP/3
- For our single-VPS deployment, Caddy's simplicity wins over Nginx's flexibility

---

## Performance Characteristics

| Operation | Complexity | Expected Latency |
|-----------|-----------|-----------------|
| Place order (no match) | O(N log N) sort | <1ms |
| Place order (match 1) | O(1) match + O(N log N) sort | <1ms |
| Place order (match K) | O(K) matches | <5ms for K=100 |
| Cancel order | O(N) scan | <1ms for N<1000 |
| Get order book | O(N) aggregation | <1ms |
| Get history (OHLCV) | O(T) where T=trades in range | 10-100ms |
| WebSocket broadcast | O(C) where C=connected clients | <10ms for C<100 |
| DB commit | 1 round-trip to PostgreSQL | 1-5ms |

**Bottlenecks** (in order of likelihood):
1. Database writes (solved by PostgreSQL + connection pooling)
2. History endpoint (solved by caching + proper DB indexes)
3. WebSocket broadcasts with many clients (solved by Redis pub/sub at scale)
4. Order book operations with deep books (solved by bisect optimization)

---

## File Tree

```
backend/
├── main.py                 # App creation, lifespan, WebSocket endpoint
├── config.py               # Environment-based settings
├── api/
│   ├── __init__.py
│   ├── auth.py             # Register, login
│   ├── dependencies.py     # DI: exchange, DB session, current user, JWT
│   ├── leaderboard.py      # Top 50 users
│   ├── market.py           # Tickers, order book, OHLCV history
│   ├── portfolio.py        # User portfolio
│   ├── rate_limit.py       # Sliding window rate limiter
│   └── trading.py          # Place/cancel/list orders, trade history
├── bots/
│   └── market_maker.py     # Background liquidity bot
├── core/
│   ├── order.py            # Order dataclass
│   ├── trade.py            # Trade dataclass
│   └── user.py             # User dataclass (in-memory state)
├── db/
│   ├── crud.py             # All database operations
│   ├── database.py         # Engine, session factory, init
│   └── models.py           # SQLAlchemy ORM models
├── engine/
│   ├── exchange.py         # Exchange: order routing, escrow, settlement
│   ├── matching_engine.py  # Price-time priority matching
│   └── orderbook.py        # Bid/ask list management
└── ws/
    └── manager.py          # WebSocket connection manager

frontend/src/
├── main.tsx                # App entry, routing
├── api/
│   ├── client.ts           # REST API client (fetch wrapper)
│   └── ws.ts               # WebSocket client (auto-reconnect)
├── components/
│   ├── ErrorBoundary.tsx   # React error boundary
│   ├── Navbar.tsx          # Navigation + auth + theme toggle
│   ├── OrderBookView.tsx   # Bid/ask depth display
│   ├── OrderForm.tsx       # Buy/sell order form
│   ├── PriceCard.tsx       # Ticker summary card
│   ├── PriceChart.tsx      # Candlestick chart (lightweight-charts)
│   ├── Spinner.tsx         # Loading spinner
│   ├── Toast.tsx           # Notification toasts
│   └── TradeHistory.tsx    # Recent trades list
├── hooks/
│   └── useTheme.ts         # Dark/light mode with localStorage
├── pages/
│   ├── Dashboard.tsx       # Market overview (price cards grid)
│   ├── History.tsx         # Order & trade history with pagination
│   ├── Leaderboard.tsx     # Top 50 users
│   ├── Login.tsx           # Login form
│   ├── Portfolio.tsx       # Holdings + cash + total value
│   ├── Register.tsx        # Registration form
│   └── Ticker.tsx          # Single ticker: chart, order book, trades
└── stores/
    └── useStore.ts         # Zustand global state

sdk/marketsim/
├── __init__.py             # Exports MarketSimClient, MarketSimWS
├── client.py               # Sync REST client
├── models.py               # Response dataclasses
└── ws.py                   # Async WebSocket client

tests/
├── conftest.py             # Fixtures: in-memory DB, fresh Exchange, AsyncClient
├── test_api.py             # 36 API integration tests
└── test_exchange.py        # 27 engine unit tests
```
