# Tournament System Specification

Design document for Market-Sim's competitive tournament feature.

---

## Overview

Tournaments are time-boxed trading competitions where participants start with equal cash and compete for the highest portfolio value. Each tournament runs on an **isolated Exchange instance** — trades in a tournament don't affect the global market, and vice versa.

---

## Data Model

### Tournament

```python
class TournamentModel(Base):
    __tablename__ = "tournaments"

    id: str               # UUID primary key
    name: str             # Display name ("Season 1: The Opening Bell")
    description: str      # Rich text description, rules, prizes
    status: str           # "draft", "open", "active", "completed", "cancelled"
    created_by: str       # FK → users (admin who created it)

    # Timing
    registration_opens: datetime  # When users can start entering
    starts_at: datetime           # When trading begins
    ends_at: datetime             # When trading stops and rankings freeze

    # Configuration
    starting_cash: float          # Cash each participant starts with (e.g., 10000.0)
    tickers: str                  # JSON: {"FUN": 100.0, "MEME": 50.0}
    max_participants: int | None  # None = unlimited
    entry_fee_cents: int          # 0 = free tournament, >0 = paid (in cents)
    prize_pool_cents: int         # Total prize pool (may include platform contribution)

    # Results
    final_rankings: str | None    # JSON array of final rankings (set on completion)

    created_at: datetime
    updated_at: datetime
```

### TournamentEntry

```python
class TournamentEntryModel(Base):
    __tablename__ = "tournament_entries"

    id: str               # UUID primary key
    tournament_id: str    # FK → tournaments
    user_id: str          # FK → users
    status: str           # "registered", "active", "completed", "disqualified"

    # Final state (populated when tournament ends)
    final_cash: float | None
    final_portfolio_value: float | None
    final_rank: int | None

    # Payment
    payment_id: str | None        # Stripe payment intent ID (if paid tournament)
    payout_amount_cents: int      # Prize money awarded (0 if none)
    payout_status: str            # "none", "pending", "paid"

    entered_at: datetime

    __table_args__ = (
        UniqueConstraint("tournament_id", "user_id", name="uq_tournament_user"),
    )
```

### TournamentTrade

```python
class TournamentTradeModel(Base):
    __tablename__ = "tournament_trades"

    # Same schema as TradeModel, plus:
    tournament_id: str    # FK → tournaments
    # ... (all TradeModel fields)
```

---

## Tournament Lifecycle

```
draft ──→ open ──→ active ──→ completed
  │         │                     │
  └─cancel  └─cancel              └─ rankings frozen
```

### States

| Status | Description | User Actions |
|--------|-------------|-------------|
| `draft` | Admin has created but not published. Not visible to users. | None |
| `open` | Registration is open. Visible on tournament list. | Enter/withdraw |
| `active` | Trading has started. No new entries. | Trade, view standings |
| `completed` | Trading ended. Rankings frozen. Prizes awarded. | View results |
| `cancelled` | Tournament cancelled. Entry fees refunded. | None |

### Transitions

**draft → open**: Admin publishes. Happens manually or at `registration_opens` time.

**open → active**: Automatic at `starts_at`. System:
1. Creates isolated Exchange instance with tournament tickers
2. Registers all entered users with `starting_cash`
3. Starts a tournament-specific market maker bot
4. Locks entries — no new registrations

**active → completed**: Automatic at `ends_at`. System:
1. Stops the tournament market maker
2. Cancels all resting orders
3. Calculates final portfolio value for each participant
4. Generates rankings (sorted by total value descending)
5. Stores `final_rankings` JSON on tournament
6. Distributes prizes (if paid tournament)

**any → cancelled**: Admin action. Refunds all entry fees.

---

## API Endpoints

### Admin Endpoints (require `is_admin=True`)

```
POST   /api/admin/tournaments              # Create tournament
PATCH  /api/admin/tournaments/{id}         # Update tournament (only in draft/open)
POST   /api/admin/tournaments/{id}/publish # draft → open
POST   /api/admin/tournaments/{id}/cancel  # any → cancelled
GET    /api/admin/tournaments/{id}/entries # List all entries with details
```

### Public Endpoints

```
GET    /api/tournaments                    # List tournaments (filterable by status)
GET    /api/tournaments/{id}               # Tournament details
GET    /api/tournaments/{id}/standings     # Live standings (active) or final rankings (completed)
```

### Authenticated Endpoints

```
POST   /api/tournaments/{id}/enter         # Enter a tournament
DELETE /api/tournaments/{id}/enter         # Withdraw (only while status=open)
```

### Tournament Trading Endpoints

When a tournament is active, participants trade via tournament-prefixed endpoints:

```
POST   /api/tournaments/{id}/orders        # Place order in tournament
DELETE /api/tournaments/{id}/orders/{oid}  # Cancel order in tournament
GET    /api/tournaments/{id}/orders        # List open orders in tournament
GET    /api/tournaments/{id}/portfolio     # Portfolio in tournament
GET    /api/tournaments/{id}/market/tickers # Tournament market data
```

These mirror the global trading endpoints but operate on the tournament's isolated Exchange.

---

## Isolated Exchange Architecture

Each active tournament gets its own:
- `Exchange` instance with tournament-specific tickers and initial prices
- `MarketMakerBot` instance providing liquidity
- User registrations with tournament `starting_cash`

```python
# In tournament lifecycle manager
tournament_exchanges: dict[str, Exchange] = {}

async def start_tournament(tournament_id: str):
    exchange = Exchange()
    for ticker, price in tournament.tickers.items():
        exchange.add_ticker(ticker, initial_price=price)

    for entry in entries:
        user = User(user_id=entry.user_id, cash=tournament.starting_cash)
        exchange.register_user(user)

    tournament_exchanges[tournament_id] = exchange

    # Start MM bot for this tournament
    mm_user = User(user_id=MM_UUID, is_market_maker=True)
    exchange.register_user(mm_user)
    bot = MarketMakerBot(exchange, mm_user)
    asyncio.create_task(bot.run())
```

**Memory impact**: Each Exchange is lightweight (~1KB base + users + orders). 10 concurrent tournaments with 100 users each ≈ 10MB. Well within single-VPS limits.

---

## Scoring

**Primary metric**: Total portfolio value at tournament end.

```
total_value = cash + sum(quantity * last_trade_price for each holding)
```

**Tiebreaker**: If two participants have identical total values:
1. Higher cash balance wins (less risk taken)
2. If still tied, earlier registration time wins

### Live Standings

During an active tournament, standings are computed on-demand from the tournament Exchange. Cached for 10 seconds to avoid recomputation on every request.

### Final Rankings

At tournament end, rankings are computed once and stored as JSON on the tournament record. This is the authoritative result — it cannot change.

```json
{
  "final_rankings": [
    {"rank": 1, "user_id": "abc", "username": "alice", "total_value": 12500.00, "cash": 3000.00},
    {"rank": 2, "user_id": "def", "username": "bob", "total_value": 11200.00, "cash": 5000.00}
  ]
}
```

---

## Prize Distribution

### Free Tournaments

No entry fee, no cash prizes. Winners get:
- Leaderboard recognition (profile badge)
- Bragging rights

### Paid Tournaments

```
Prize Pool = (entry_fee * participants) * (1 - platform_cut)
Platform Cut = 15%
```

**Default payout structure** (top 3):

| Place | Share |
|-------|-------|
| 1st | 50% |
| 2nd | 30% |
| 3rd | 20% |

For tournaments with <10 participants, only 1st place is paid (100%).
For tournaments with 10-29 participants, 1st and 2nd are paid (60/40).
For tournaments with 30+ participants, standard top-3 split.

**Payout method**:
- Phase 1: Manual bank transfer (admin reviews results, sends money)
- Phase 2: Stripe Connect (automated payouts to verified accounts)

---

## Anti-Cheat

### Automated Detection

1. **Self-trading**: Orders matched against the same user's resting orders. Blocked at the matching engine level — not just detected, **prevented**.

2. **Wash trading**: Circular trades between two accounts within a short window.
   - Detection: Query `tournament_trades` for patterns where user A buys from B, then B buys from A within 60 seconds.
   - Threshold: >3 circular patterns in a tournament = auto-flag.

3. **Multi-accounting**: Multiple accounts controlled by the same person.
   - Detection: Same IP address placing coordinated trades.
   - Phase 1: Manual review. Phase 2: IP fingerprinting.

4. **Market manipulation**: Placing and immediately cancelling large orders to move prices.
   - Detection: Orders cancelled within 1 second of placement, with quantity >10x average.
   - Threshold: >10 instances per hour = auto-flag.

### Manual Review

All auto-flagged accounts go to admin dashboard for review. Admin can:
- View flagged trades with timestamps
- Compare activity patterns between suspected accounts
- Disqualify participant (removes from rankings, refunds entry fee)
- Ban account (permanent)

### Appeal Process

Disqualified participants can appeal via email. Admin reviews and responds within 48 hours.

---

## Frontend Integration

### Tournament List Page (`/tournaments`)

- Tabs: Upcoming, Active, Completed
- Cards showing: name, dates, entry fee, participants, prize pool
- "Enter" button for open tournaments
- "View Standings" for active tournaments
- "View Results" for completed tournaments

### Tournament Detail Page (`/tournaments/{id}`)

- Tournament info: description, rules, schedule
- Participant count and max capacity
- Prize breakdown
- Entry button or "You're entered" status

### Tournament Trading Page (`/tournaments/{id}/trade`)

- Same layout as global Ticker page but:
  - Uses tournament-specific API endpoints
  - Shows tournament-specific prices and order book
  - Banner: "Tournament: Season 1 — Ends in 2h 15m"
  - Tournament standings sidebar

### Tournament Results Page (`/tournaments/{id}/results`)

- Final rankings table with medal icons
- Each row: rank, username, total value, P&L vs starting cash
- Prize amounts for top finishers
- Link to winner profiles

---

## Tournament Configuration Examples

### Beginner Friendly (Free)
```json
{
  "name": "Starter Cup",
  "starting_cash": 10000.0,
  "tickers": {"FUN": 100.0, "MEME": 50.0},
  "entry_fee_cents": 0,
  "max_participants": null,
  "duration": "7 days"
}
```

### Competitive (Paid)
```json
{
  "name": "Season 1 Championship",
  "starting_cash": 50000.0,
  "tickers": {"FUN": 100.0, "MEME": 50.0, "YOLO": 200.0, "HODL": 75.0, "PUMP": 25.0},
  "entry_fee_cents": 1000,
  "max_participants": 100,
  "duration": "30 days"
}
```

### Sprint (Quick)
```json
{
  "name": "Friday Night Sprint",
  "starting_cash": 5000.0,
  "tickers": {"FUN": 100.0},
  "entry_fee_cents": 500,
  "max_participants": 50,
  "duration": "2 hours"
}
```
