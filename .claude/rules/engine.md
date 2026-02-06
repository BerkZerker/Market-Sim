---
globs:
  - "backend/engine/**"
  - "backend/core/**"
---

# Engine Rules

- `MatchingEngine.process_order()` mutates `incoming_order.quantity` in-place. Always save original quantity before calling.
- Buy orders match against asks at the ask's price (not the incoming bid price). Same for sells.
- `Exchange` uses per-ticker `asyncio.Lock` via `defaultdict(asyncio.Lock)` — orders on different tickers can process concurrently.
- Escrow is deducted BEFORE matching. Refunds happen after: on cancel, price improvement, or partial fill remainder.
- Market maker users (`is_market_maker=True`) skip cash/share validation entirely.
- `exchange.on_trades` callback fires after matching — used for WebSocket broadcasts.
- OrderBook sorts: bids descending by price, asks ascending by price (price-time priority).
