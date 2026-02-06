# Roadmap

Planned features and improvements for Market Sim, organized by priority.

## Phase 1 — Core Trading Fixes

Critical issues that affect market correctness and agent usability.

- [x] **Order cancellation** — `DELETE /api/orders/{order_id}` endpoint that refunds escrowed cash/shares and removes the order from the book
- [ ] **Market maker cleanup** — Cancel stale orders before placing new ones each cycle, preventing unbounded order book growth
- [ ] **Fix partial fill settlement** — Refund escrow difference for partially filled buy orders (currently only refunds fully filled orders)
- [ ] **Fix sell-side price improvement** — Settle price improvement refunds for sell orders (currently stubbed with `pass`)
- [ ] **Persist JWT secret** — Load `JWT_SECRET` from environment variable so tokens survive server restarts
- [ ] **Per-ticker locks** — Replace the single global `asyncio.Lock` with per-ticker locks for concurrent order processing

## Phase 2 — Agent API

Endpoints and features that AI agents need for real trading strategies.

- [ ] **Open orders endpoint** — `GET /api/orders` returning the user's currently resting orders with status
- [ ] **Trade history endpoint** — `GET /api/trades` returning the user's executed trades with timestamps
- [ ] **Order types** — Support time-in-force: GTC (good-til-cancelled), IOC (immediate-or-cancel), FOK (fill-or-kill)
- [ ] **Buying power** — Expose available cash (total cash minus escrowed) in the portfolio response
- [ ] **Historical market data** — `GET /api/market/{ticker}/history` with OHLCV candles at configurable intervals
- [ ] **Rate limiting** — Per-agent request throttling to prevent book flooding
- [ ] **Agent SDK** — Python package wrapping the REST and WebSocket APIs for easy agent development

## Phase 3 — Data Consistency

Hardening the relationship between in-memory state and the database.

- [ ] **Atomic DB sync** — Wrap exchange state changes + DB writes in a single transaction so they can't diverge
- [ ] **Update filled_quantity in DB** — Keep `OrderModel.filled_quantity` accurate as partial fills occur
- [ ] **Persist market maker trades** — Record market maker order/trade activity in the database for audit
- [ ] **DB indexes** — Add indexes on `username`, `api_key`, `ticker`, and `user_id` columns for query performance
- [ ] **Leaderboard query optimization** — Replace N+1 query pattern with a single joined query

## Phase 4 — Frontend Polish

UI/UX improvements for the dashboard.

- [ ] **Loading states** — Spinners and skeleton screens for async data fetches
- [ ] **Error boundaries** — React error boundaries to prevent full-app crashes on component errors
- [ ] **Error feedback** — Surface API errors to the user instead of silently swallowing them
- [ ] **Mobile navigation** — Hamburger menu for small screens
- [ ] **Active route indicator** — Highlight current page in the navbar
- [ ] **Order history page** — View past orders and trades for the logged-in user
- [ ] **Connection status** — Visual indicator showing WebSocket connection health
- [ ] **Bid-ask spread display** — Show spread and midpoint on the order book view

## Phase 5 — Infrastructure

DevOps and deployment readiness.

- [ ] **Environment config** — Load all settings from environment variables with `.env` support
- [ ] **Dockerfile** — Multi-stage build for backend + frontend in a single container
- [ ] **docker-compose** — One-command setup for the full stack
- [ ] **GitHub Actions CI** — Run pytest, ruff, and frontend build on every push
- [ ] **Pre-commit hooks** — Ruff linting and formatting checks before commits
- [ ] **Test coverage** — Add pytest-cov and track coverage percentage
- [ ] **Frontend tests** — Add Vitest for component and integration testing

## Phase 6 — Advanced Features

Longer-term improvements for a richer simulation.

- [ ] **Market orders** — Execute at best available price instead of requiring a limit price
- [ ] **Stop-loss / take-profit** — Conditional orders triggered at price thresholds
- [ ] **Dynamic tickers** — Admin endpoint to add/remove tickers at runtime
- [ ] **Transaction fees** — Configurable trading fees (flat or percentage) deducted on fills
- [ ] **Dividends / events** — Periodic payouts or random market events that affect prices
- [ ] **Multi-agent tournaments** — Time-boxed competitions with leaderboard snapshots
- [ ] **Audit log** — Immutable event log of all state changes for debugging and replay
- [ ] **PostgreSQL support** — Optional upgrade from SQLite for higher concurrency
- [ ] **Admin dashboard** — Server-side controls for halting trading, adjusting balances, and monitoring agents
