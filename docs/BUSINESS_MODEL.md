# Business Model

How Market-Sim makes money.

---

## Value Proposition

Market-Sim is a **simulated stock exchange** where AI agents and humans trade against each other in a realistic market. It serves three audiences:

1. **AI/ML developers** — A sandbox to build, test, and benchmark trading algorithms without real money risk. The SDK makes it trivial to connect a bot.

2. **Competitive algo traders** — Tournament platform where participants compete for prizes using their strategies. Like Kaggle for trading.

3. **Educators** — A hands-on tool for teaching market microstructure, algorithmic trading, and financial engineering. Universities get bulk licenses and private tournaments.

---

## Revenue Streams

### 1. Tournament Entry Fees (Primary — Month 3+)

Paid competitions with cash prizes.

- **Entry fee**: $5-$50 per participant
- **Platform cut**: 15% of prize pool
- **Frequency**: 2-4 tournaments per month
- **Example**: 50 participants x $20 entry = $1,000 pool, $150 platform revenue

**Why this works**: Competitions are inherently viral. Winners share results, losers try again. Low barrier to entry ($5-20), high perceived value (compete against real people + AIs).

### 2. Pro Subscriptions (Secondary — Month 4+)

Monthly subscription for power users.

- **Price**: $19/mo (annual: $15/mo)
- **Features**: Higher rate limits, full history, data exports, paid tournament access
- **Target**: Serious bot developers who need more API access

### 3. Education Licenses (Tertiary — Month 9+)

Bulk licenses for universities and bootcamps.

- **Price**: $500-2,000/semester per class (20-50 students)
- **Features**: Private tournaments, bulk account creation, custom tickers, curriculum materials
- **Sales**: Direct outreach to CS/finance professors

### 4. Data Products (Future)

- Historical OHLCV data exports for backtesting
- Real-time data firehose for ML training
- Synthetic market data generation API

---

## Pricing

### Free Tier

Everything needed to start:
- 30 API requests per minute
- 5 default tickers
- Free tournament entry
- 30-day trade history
- Full WebSocket access
- Python SDK

### Pro Tier — $19/month

For serious developers:
- 120 API requests per minute
- All tickers (including tournament-specific)
- Free + paid tournament entry
- Unlimited trade history
- OHLCV data export (CSV/JSON)
- Priority WebSocket (reduced latency)
- Email support

### Enterprise — Custom Pricing

For organizations:
- Custom rate limits
- Custom tickers and market configuration
- Dedicated tournaments
- Self-hosted option
- API access for data products
- Dedicated support
- SLA guarantee

---

## Unit Economics

### Cost Structure

| Item | Monthly Cost | Notes |
|------|-------------|-------|
| Hetzner VPS (CPX21) | $8 | 2 vCPU, 4GB RAM — handles 500+ users |
| Domain | $1 | Annual cost amortized |
| Backblaze B2 backups | $1 | Daily PostgreSQL dumps |
| Stripe fees | 2.9% + $0.30/txn | On revenue only |
| UptimeRobot | $0 | Free tier |
| SSL (Let's Encrypt) | $0 | Automatic via Caddy |
| **Total fixed** | **~$10/mo** | |

### Revenue Scenarios

**Scenario 1: Conservative (Month 6)**
- 200 users, 20 Pro subscribers, 2 tournaments (50 participants each, $10 entry)
- Pro revenue: 20 x $19 = $380
- Tournament revenue: 2 x 50 x $10 x 0.15 = $150
- **Total MRR: $530** — Costs: $10 + $15 Stripe = $25 → **Profit: $505**

**Scenario 2: Moderate (Month 9)**
- 500 users, 60 Pro subscribers, 4 tournaments (80 participants, $20 entry)
- Pro revenue: 60 x $19 = $1,140
- Tournament revenue: 4 x 80 x $20 x 0.15 = $960
- **Total MRR: $2,100** — Costs: $15 (upgraded VPS) + $60 Stripe = $75 → **Profit: $2,025**

**Scenario 3: Growth (Month 12)**
- 1,000 users, 150 Pro subscribers, 1 education deal
- Pro revenue: 150 x $19 = $2,850
- Tournament revenue: $1,500
- Education: $1,000 (one class)
- **Total MRR: $5,350** — Costs: $15 + $155 Stripe = $170 → **Profit: $5,180**

---

## Growth Strategy

### Phase 1: Build (Month 1-2)

- Ship production app with tournaments
- Create 5 example bots (best marketing asset)
- Write "Build Your First Trading Bot" tutorial
- Set up Discord server

### Phase 2: Launch (Month 3)

- Show HN post: "I built a simulated stock exchange for AI trading bots"
- Post to r/algotrading, r/python, r/machinelearning
- Run first free tournament (Season 0) to test infrastructure
- Collect feedback, fix bugs

### Phase 3: Monetize (Month 4-5)

- Launch Pro tier
- Run first paid tournament ($5 entry, low stakes)
- Blog post: "Season 0 Results — What We Learned"
- Cross-post to Dev.to

### Phase 4: Scale (Month 6-9)

- Regular tournament schedule (weekly sprint + monthly championship)
- Education outreach (cold email 50 CS professors)
- SEO content: tutorials, strategy guides, market analysis
- Discord community events (strategy workshops, AMAs)

### Phase 5: Expand (Month 9-12)

- Education partnerships
- Advanced features based on user demand
- Consider agent hosting (if tournament demand justifies it)
- Explore data product revenue

---

## Competitive Landscape

| Competitor | What They Do | Our Advantage |
|-----------|-------------|---------------|
| QuantConnect | Backtesting + paper trading | Simpler API, real-time multi-agent market, tournaments |
| Alpaca Paper Trading | Paper trading on real market data | AI-focused, competitive element, custom tickers |
| Kaggle Competitions | ML competitions with static datasets | Live, continuous market (not batch), trading-specific |
| TradingView Paper | Chart-based paper trading | API-first, bot-friendly, programmatic access |

**Our niche**: The intersection of **AI agent development** and **competitive trading**. No existing platform does both well.

---

## Key Metrics to Track

| Metric | Target (Month 6) | How to Measure |
|--------|------------------|----------------|
| Registered users | 200+ | DB count |
| Monthly active traders | 50+ | Users with >1 trade in 30 days |
| Pro subscribers | 20+ | Stripe dashboard |
| Tournament participants | 50+ per event | DB count |
| API requests/day | 10,000+ | Structured logs |
| Retention (30-day) | >40% | Cohort analysis |
| NPS | >50 | Survey |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Nobody cares about simulated trading | Fatal | Validate with Show HN before building Pro tier |
| Cheating undermines tournament integrity | High | Anti-cheat system (self-trade prevention, wash trade detection) |
| Platform goes down during tournament | High | Automated backups, health monitoring, tournament pause ability |
| Someone finds an exploit in the matching engine | High | Extensive test suite (63 backend tests), admin kill switch |
| Price war from QuantConnect/Alpaca | Medium | Stay focused on AI agent niche, community, tournaments |
| VPS can't handle load | Medium | Upgrade VPS ($8→$15), add Redis, optimize hot paths |
| Legal issues with "prize money" | Medium | Consult lawyer before paid tournaments; structure as skill-based competition |

---

## Legal Considerations

Before launching paid tournaments:

1. **Terms of Service**: Required. Cover: acceptable use, tournament rules, prize distribution, dispute resolution.
2. **Privacy Policy**: Required (GDPR if EU users). Cover: what data we collect, how it's used, data retention.
3. **Prize money legality**: Skill-based competitions are generally legal in most US states (unlike gambling). Consult a lawyer.
4. **Stripe compliance**: Stripe handles PCI compliance for payments. Follow their TOS.
5. **Tax obligations**: Prize money may be taxable income for winners. Document: "Winners are responsible for their own tax obligations."
