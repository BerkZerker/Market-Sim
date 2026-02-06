---
globs:
  - "backend/db/**"
  - "backend/api/**"
---

# Database Rules

- Always use `Depends(get_db)` in route handlers — never import `async_session()` directly. Required for test overrides.
- The in-memory Exchange is the source of truth for order book state. The DB persists users, trades, portfolios, and order records.
- `crud.py` functions take an `AsyncSession` parameter — never create sessions inside them.
- DB models are in `backend/db/models.py`: UserModel, PortfolioHolding, OrderModel, TradeModel.
- SQLite via aiosqlite — no concurrent write support. Matches the single-lock Exchange design.
- When adding new DB operations in routes, wrap related writes in a single `db.commit()` call.
