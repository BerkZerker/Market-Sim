# Production Plan

Master plan for taking Market-Sim from working prototype to production SaaS.

**Target**: 100-1,000 concurrent users on a single VPS.
**Audience**: AI/ML developers, competitive algo traders, education.
**Hosting**: Single VPS (Hetzner/DigitalOcean) with Caddy reverse proxy.

---

## Current State (Phases 1-5 Complete)

- 14 REST endpoints + WebSocket real-time data
- Matching engine with escrow model, per-ticker locking, price-time priority
- Dual auth (JWT + API key), Python SDK, market maker bot
- React frontend with charts, dark mode, mobile nav, error handling
- 109 tests (63 backend + 46 frontend), CI/CD, Docker
- Known gaps: SQLite, no TLS, open CORS, no migrations, no logging

---

## Phase A: Infrastructure Hardening

_Goal: Make the app safe to expose to the internet._
_Estimated effort: 2 weeks_

### A1. PostgreSQL + Alembic Migration

**Why first**: Everything else depends on a real database. SQLite's single-writer constraint caps us at ~50 concurrent users.

**Tasks**:

1. Add `asyncpg` and `alembic` to `pyproject.toml` dependencies
2. Initialize Alembic with async template: `alembic init -t async alembic`
3. Create initial migration auto-generated from current SQLAlchemy models
4. Update `backend/config.py`:
   - Add `DATABASE_POOL_SIZE` (default 10), `DATABASE_MAX_OVERFLOW` (default 20)
   - Add `DATABASE_ECHO` (default false, true in dev)
5. Update `backend/db/database.py`:
   - Pass pool settings to `create_async_engine()`
   - Add `dispose()` method for clean shutdown
6. Update `docker-compose.yml`:
   - Add `postgres` service (postgres:16-alpine)
   - Update `DATABASE_URL` to `postgresql+asyncpg://...`
   - Add `pgdata` volume for persistence
7. Fix `load_all_users` N+1 query in `crud.py` — use `selectinload(UserModel.holdings)`
8. Run full test suite against PostgreSQL (not just in-memory SQLite)
9. Update `.env.example` with PostgreSQL connection string
10. Test migration workflow: fresh DB → `alembic upgrade head`

**Acceptance criteria**:

- `uv run python -m pytest` passes with PostgreSQL backend
- `alembic upgrade head` creates schema from scratch
- `alembic revision --autogenerate` detects new model changes
- Connection pooling handles 100 concurrent connections

**Files touched**: `pyproject.toml`, `backend/config.py`, `backend/db/database.py`, `backend/db/crud.py`, `docker-compose.yml`, `.env.example`, new `alembic/` directory

---

### A2. Caddy Reverse Proxy

**Why**: TLS termination, static file serving, HTTP/2, automatic HTTPS via Let's Encrypt.

**Tasks**:

1. Create `Caddyfile` in project root:
   ```
   {$DOMAIN:localhost} {
       handle /api/* {
           reverse_proxy market-sim:8000
       }
       handle /ws/* {
           reverse_proxy market-sim:8000
       }
       handle {
           root * /srv/frontend
           file_server
           try_files {path} /index.html
       }
   }
   ```
2. Add `caddy` service to `docker-compose.yml`:
   - Image: `caddy:2-alpine`
   - Ports: `80:80`, `443:443`
   - Volume mount `Caddyfile`, `caddy_data`, `caddy_config`
   - Copy `frontend/dist` into caddy volume
3. Remove port exposure from `market-sim` service (only Caddy is public)
4. Add `DOMAIN` env var to `backend/config.py`
5. Remove static file mounting from `backend/main.py` (Caddy serves frontend now)
6. Test: HTTP → HTTPS redirect, WebSocket upgrade, SPA routing fallback

**Acceptance criteria**:

- `https://yourdomain.com` serves React app
- `https://yourdomain.com/api/health` proxies to backend
- `wss://yourdomain.com/ws/prices` establishes WebSocket
- HTTP requests redirect to HTTPS
- Certificate auto-renews

**Files touched**: new `Caddyfile`, `docker-compose.yml`, `backend/main.py`, `backend/config.py`

---

### A3. CORS Lockdown

**Tasks**:

1. Add `ALLOWED_ORIGINS` to `backend/config.py`:
   ```python
   ALLOWED_ORIGINS: list[str] = field(
       default_factory=lambda: json.loads(
           os.environ.get("ALLOWED_ORIGINS", '["http://localhost:5173"]')
       )
   )
   ```
2. Update `main.py` CORS middleware to use `settings.ALLOWED_ORIGINS`
3. In production, set `ALLOWED_ORIGINS=["https://yourdomain.com"]`

**Files touched**: `backend/config.py`, `backend/main.py`, `.env.example`

---

### A4. Environment-Aware Config

**Tasks**:

1. Add `ENVIRONMENT` setting (`development` / `production`) to `config.py`
2. In production mode, enforce:
   - `JWT_SECRET` must be explicitly set (fail on startup if missing)
   - `ALLOWED_ORIGINS` must not contain `*`
   - `reload=False` in uvicorn
3. Add startup validation method to `Settings`:
   ```python
   def validate(self):
       if self.ENVIRONMENT == "production":
           if "token_hex" in str(type(self.JWT_SECRET)):
               raise RuntimeError("JWT_SECRET must be set in production")
   ```
4. Call `settings.validate()` in lifespan before anything else

**Files touched**: `backend/config.py`, `backend/main.py`, `.env.example`

---

### A5. Structured Logging

**Tasks**:

1. Add `structlog` to `pyproject.toml`
2. Create `backend/logging_config.py`:
   - JSON output in production, colorized pretty-print in development
   - Include: timestamp, level, logger name, request_id
3. Add request ID middleware:
   - Generate UUID per request, attach to all log entries
   - Return as `X-Request-ID` response header
4. Expand `/api/health` to return:
   ```json
   {
     "status": "ok",
     "database": "connected",
     "exchange": { "tickers": 5, "users": 42 },
     "websockets": { "connections": 17 },
     "uptime_seconds": 3600,
     "version": "0.1.0"
   }
   ```
5. Add `/api/health/ready` for load balancer readiness probes
6. Replace all `logger.info(...)` calls with structured equivalents

**Files touched**: `pyproject.toml`, new `backend/logging_config.py`, `backend/main.py`, all files using `logger`

---

### A6. Security Hardening

**Tasks**:

1. **Auth rate limiting**: Apply stricter rate limits to `/api/register` (5/min) and `/api/login` (10/min)
2. **Account lockout**: Track failed login attempts per username in-memory dict; lock for 15 min after 5 failures
3. **Password policy**: Minimum 8 characters, at least one digit
4. **API key rotation**: `POST /api/keys/rotate` — generates new API key, invalidates old one
5. **Self-trade prevention**: Reject orders in `exchange.place_order()` where incoming order would match against the same user's resting order
6. **Input validation**: Add `MAX_ORDER_QUANTITY = 100000` and `MAX_ORDER_PRICE = 1000000` to config; validate in trading route
7. **Security headers**: Configure via Caddy: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`

**Files touched**: `backend/api/auth.py`, `backend/api/trading.py`, `backend/api/rate_limit.py`, `backend/engine/exchange.py`, `backend/config.py`, `Caddyfile`

---

### A7. Deployment Automation

**Tasks**:

1. Create `deploy/setup.sh` — VPS initialization script:
   - Install Docker + Docker Compose
   - Configure UFW firewall (allow 80, 443, 22 only)
   - Install fail2ban
   - Create deploy user with SSH key access
2. Add CD job to `.github/workflows/ci.yml`:
   - On push to `main` after CI passes
   - SSH to VPS, `git pull`, `docker compose up --build -d`
3. Create `.env.production.example` with all required production vars
4. Create `deploy/backup.sh`:
   - `pg_dump` to compressed file
   - Upload to S3/Backblaze B2 (configurable)
   - Retain last 30 daily backups
5. Add `healthcheck` directive to `docker-compose.yml` for each service
6. Set up UptimeRobot monitoring (free tier, checks `/api/health` every 5 min)

**Files touched**: new `deploy/` directory, `.github/workflows/ci.yml`, `docker-compose.yml`, `.env.production.example`

---

## Phase B: Core Business Features

_Goal: Build what makes Market-Sim worth paying for._
_Estimated effort: 3 weeks_
_Depends on: Phase A complete_

### B1. User Profiles & Statistics

**DB changes**:

- Add columns to `UserModel`: `display_name`, `bio`, `avatar_url`, `created_at` (already exists)
- Create Alembic migration

**New endpoints**:

- `GET /api/profile` — current user's profile
- `PATCH /api/profile` — update display_name, bio, avatar_url
- `GET /api/users/{username}` — public profile with trading stats

**Trading statistics** (computed from `TradeModel`):

- Total trades count
- Total volume traded
- Win rate (profitable round-trip trades / total)
- Best single trade P&L
- Current streak (consecutive profitable trades)

**Frontend**:

- Profile settings page
- Public profile linked from leaderboard

---

### B2. Tournament System

See `docs/TOURNAMENT_SPEC.md` for full specification.

**Summary**:

- Isolated Exchange instances per tournament
- Lifecycle: draft → open → active → completed
- Entry via `POST /api/tournaments/{id}/enter`
- Leaderboard snapshots frozen at tournament end
- Free and paid tournaments supported

---

### B3. Transaction Fees

**Config**: `TRADE_FEE_PERCENT` (default 0.1%) and `TRADE_FEE_FLAT` (default 0.0)

**Implementation**:

- Deduct fee from fill proceeds in `Exchange.place_order()` settlement loop
- Credit fees to system "house" account
- Include fee breakdown in trade response
- Display fees on frontend order form ("Estimated fee: $0.10")
- Track total fees collected per tournament for prize pool calculation

---

### B4. Market Orders

**Changes**:

- Add `order_type` field to `OrderRequest`: `"limit"` (default) or `"market"`
- Market orders: `price=None`, always IOC (fill what's available, cancel rest)
- For market buys: escrow at best ask price \* quantity (with 5% slippage buffer)
- For market sells: no price escrow needed (shares are escrowed)
- Refund unused slippage buffer after fill

---

### B5. Anti-Cheat Foundation

**Self-trade prevention**: Reject in matching engine if `incoming_order.user_id == resting_order.user_id`

**Wash trade detection** (batch job, not real-time):

- Query `TradeModel` for circular patterns: A sells to B, B sells to A within 60 seconds
- Flag suspicious accounts in new `UserFlag` table
- Admin reviews flags manually

**Timing analysis**:

- Track order placement timestamps relative to price changes
- Flag accounts with statistically impossible reaction times (<10ms)

---

## Phase C: Monetization

_Goal: Start generating revenue._
_Estimated effort: 2 weeks_
_Depends on: Phase B (tournaments, at minimum)_

### C1. Stripe Integration

- `POST /api/payments/checkout` — create Stripe Checkout session for subscription or tournament entry
- Webhook handler at `/api/webhooks/stripe` for: `checkout.session.completed`, `customer.subscription.updated`, `invoice.payment_failed`
- Store `stripe_customer_id` on `UserModel`
- Use Stripe Checkout (hosted payment page) — no PCI compliance burden

### C2. User Tiers

| Feature            | Free       | Pro ($19/mo)   | Enterprise |
| ------------------ | ---------- | -------------- | ---------- |
| Rate limit         | 30 req/min | 120 req/min    | Custom     |
| Tickers            | 5          | All            | Custom     |
| Tournament entry   | Free only  | Free + paid    | Custom     |
| Trade history      | 30 days    | Unlimited      | Unlimited  |
| OHLCV data export  | No         | CSV/JSON       | API access |
| WebSocket channels | All        | All + priority | Dedicated  |
| Support            | Community  | Email          | Dedicated  |

### C3. Paid Tournaments

- Entry fee: $5-$50, collected via Stripe
- Prize pool = (entries \* fee) - platform cut (15%)
- Top 3 payout: 50% / 30% / 20%
- Payout via Stripe Connect (or manual bank transfer initially)

### C4. Data Products

- Historical OHLCV export endpoint: `GET /api/data/export/{ticker}` (Pro tier)
- Bulk trade data: `GET /api/data/trades/{ticker}` with date range (Pro tier)
- Synthetic data generation for ML training (future)

---

## Phase D: Frontend Overhaul

_Goal: Professional UX that converts visitors to users._
_Estimated effort: 2 weeks_
_Can run in parallel with Phase C_

### D1. Landing Page

- Marketing homepage at `/` (not the dashboard)
- Hero: "Build, Test, and Compete with AI Trading Bots"
- Feature cards, pricing table, social proof
- CTA: "Start Trading Free" → `/register`
- SEO: meta tags, Open Graph, structured data
- Dashboard moves to `/dashboard` (authenticated)

### D2. Dashboard Improvements

- Onboarding wizard for new users (3 steps: see market → place first order → check portfolio)
- P&L chart over time (line chart, daily snapshots)
- Quick-trade widget (market order from dashboard)
- Notification center: fills, tournament events, system announcements
- Tournament banner: "Season 1 starts in 3 days — Enter now"

### D3. Admin Dashboard

- Protected `/admin` route (check `is_admin` flag on user)
- Panels: users list, trading activity, system health, tournament management
- Actions: halt/resume trading, adjust user balance, ban user, create tournament
- Anti-cheat review: flagged accounts with evidence

### D4. Frontend Hardening

- `VITE_API_BASE_URL` environment variable for production builds
- JWT expiry check on client side (preemptive logout before 401)
- Request timeout (30s) + retry with exponential backoff on transient failures
- WebSocket connection pooling (single connection per channel, shared across components)
- Form validation (password strength, order quantity vs. buying power)
- Route guards for authenticated pages (redirect to `/login`)
- 404 page
- Error reporting to Sentry

---

## Phase E: Growth Engine

_Goal: Build community and organic acquisition._
_Estimated effort: 2 weeks_
_Can start during Phase D_

### E1. Example Bots (HIGHEST ROI marketing asset)

Create `examples/` directory with 5 standalone bots:

1. `simple_sma.py` — Moving average crossover
2. `mean_reversion.py` — Buy low, sell high around rolling mean
3. `market_maker.py` — Spread-based liquidity provision
4. `momentum.py` — Follow price trends
5. `random_baseline.py` — Random trades for comparison

Each bot: <100 lines, well-commented, uses the SDK, runnable with `python examples/simple_sma.py`.

### E2. Documentation Site

- Docusaurus or MkDocs at `docs.yourdomain.com`
- Sections: Getting Started, SDK Reference, API Reference, Tutorials, Tournament Rules
- Auto-generated API docs from OpenAPI spec
- Tutorial: "Build Your First Trading Bot in 10 Minutes"

### E3. Community

- Discord server: #announcements, #strategies, #help, #tournaments
- Discord bot: post tournament results, leaderboard updates
- GitHub Discussions for SDK feature requests

### E4. Content Marketing

- Blog posts targeting: "algo trading tutorial", "simulated stock market API", "AI trading bot Python"
- Cross-post: Dev.to, Hacker News Show HN, Reddit (r/algotrading, r/python)
- Monthly newsletter: tournament highlights, top performers, new features

### E5. Education Partnerships

- Free classroom licenses (bulk registration, private tournaments)
- Curriculum materials: assignments mapped to CS/finance courses
- Student Pro tier discount (50% off)

---

## Phase F: Scale & Advanced Features

_Goal: Handle growth beyond single VPS._
_Estimated effort: Ongoing_
_Only build when demand requires it_

### F1. Redis

- Rate limiter backend (replace in-memory dict)
- Leaderboard cache (recompute every 30s, serve from cache)
- Session cache for faster auth lookups
- Pub/sub for multi-process WebSocket broadcasts

### F2. CDN Frontend

- Deploy frontend to Cloudflare Pages or Vercel
- API stays on VPS, frontend at edge globally
- Reduces VPS bandwidth, improves load times worldwide

### F3. Background Task Queue

- ARQ (async Redis queue) for: tournament scoring, data exports, email notifications, daily P&L snapshots, anti-cheat batch analysis
- Periodic tasks: nightly DB cleanup, weekly leaderboard emails

### F4. Advanced Order Types

- Stop-loss / take-profit (conditional trigger orders)
- Trailing stops
- Bracket orders (entry + stop + target as atomic unit)

### F5. Dynamic Tickers & Market Events

- Admin endpoint: `POST /api/admin/tickers` to add/remove at runtime
- Market events: earnings surprises, dividends, stock splits
- News feed (randomized) that affects prices

### F6. Agent Hosting (Long-term)

- Sandboxed Docker containers per user bot
- Resource limits: 256MB RAM, 0.5 CPU, 60s timeout
- Code upload via web UI or API
- Only build if tournament participation justifies the infrastructure cost

---

## Revenue Projections

| Milestone        | Users  | MRR           | Timeline   |
| ---------------- | ------ | ------------- | ---------- |
| Launch (free)    | 50     | $0            | Month 1-2  |
| First tournament | 100    | $200-500      | Month 3    |
| Pro tier launch  | 200    | $500-1,500    | Month 4-5  |
| Steady state     | 500+   | $2,000-5,000  | Month 6-9  |
| Education deals  | 1,000+ | $5,000-10,000 | Month 9-12 |

**Fixed costs**: ~$20/mo (VPS $15 + domain $1 + backups $1 + monitoring free)
**Variable costs**: Stripe 2.9% + $0.30 per transaction

---

## Dependencies

```
Phase A ──┬── A1 (PostgreSQL) ← everything depends on this
          ├── A2 (Caddy) ← A3 (CORS) depends on knowing the domain
          ├── A3 (CORS)
          ├── A4 (Config)
          ├── A5 (Logging)
          ├── A6 (Security)
          └── A7 (Deployment) ← depends on A1-A6

Phase B ──┬── B1 (Profiles)
          ├── B2 (Tournaments) ← B5 depends on this
          ├── B3 (Fees)
          ├── B4 (Market Orders)
          └── B5 (Anti-Cheat) ← depends on B2

Phase C ──┬── C1 (Stripe) ← C2, C3 depend on this
          ├── C2 (Tiers) ← depends on C1
          ├── C3 (Paid Tournaments) ← depends on C1 + B2
          └── C4 (Data Products) ← depends on C2

Phase D ──── runs in parallel with B/C
Phase E ──── runs in parallel with C/D
Phase F ──── on demand
```

---

## Success Criteria

**Phase A complete when**:

- App runs on VPS with HTTPS, PostgreSQL, automated deploys
- 0 critical security findings in manual review
- Structured logs visible in `docker compose logs`

**Phase B complete when**:

- Tournament can be created, entered, played, and completed end-to-end
- Anti-cheat catches self-trading automatically

**Phase C complete when**:

- First paying customer (Pro subscription or tournament entry)
- Stripe webhook handles payment lifecycle correctly

**Phase D complete when**:

- Landing page converts at >5% visitor → registration
- Lighthouse score >90 on mobile

**Phase E complete when**:

- 100+ GitHub stars on example bots repo
- Active Discord community (50+ members)
