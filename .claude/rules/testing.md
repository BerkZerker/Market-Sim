---
globs:
  - "tests/**"
---

# Testing Rules

- `conftest.py` creates an in-memory SQLite DB and a fresh Exchange per test — `set_exchange()` is called there since the app lifespan doesn't run under `AsyncClient`.
- Run tests with `uv run python -m pytest` — bare `pytest` is not installed globally. `asyncio_mode = "auto"` and `pythonpath = ["backend"]` are set in `pyproject.toml`.
- Engine tests (`test_exchange.py`) test the Exchange directly — no HTTP, no DB.
- API tests (`test_api.py`) use `httpx.AsyncClient` with the FastAPI app — test the full request cycle.
- Always run the full suite after changes: `uv run python -m pytest`. Don't skip unrelated tests.
- When adding a new route, add both a happy-path and an error-case test in `test_api.py`.
- When changing matching logic, add a case in `test_exchange.py` covering the edge case.
