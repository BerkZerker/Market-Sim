# Agent Development Guide

Build AI trading bots for Market-Sim using the Python SDK.

---

## Quick Start

### 1. Install the SDK

```bash
cd sdk
pip install -e .
```

Or install directly from the project:

```bash
pip install ./sdk
```

### 2. Register an Account

```python
from marketsim import MarketSimClient

# Register and get an authenticated client
client = MarketSimClient.register(
    base_url="https://marketsim.example.com",
    username="my_bot",
    password="secure_password_123"
)

# Save the API key — you'll need it to reconnect
print(f"API Key: {client._session.headers['X-API-Key']}")
```

Or connect with an existing API key:

```python
client = MarketSimClient(
    base_url="https://marketsim.example.com",
    api_key="your-api-key-here"
)
```

### 3. Place Your First Trade

```python
# Check market prices
tickers = client.get_tickers()
for name, info in tickers.items():
    print(f"{name}: ${info.current_price:.2f} (bid: {info.best_bid}, ask: {info.best_ask})")

# Buy 10 shares of FUN at $100
result = client.place_order(
    ticker="FUN",
    side="buy",
    price=100.00,
    quantity=10,
)
print(f"Order {result.order_id}: {result.status} ({result.filled_quantity}/{result.quantity} filled)")

# Check your portfolio
portfolio = client.get_portfolio()
print(f"Cash: ${portfolio.cash:.2f}")
print(f"Total Value: ${portfolio.total_value:.2f}")
for h in portfolio.holdings:
    print(f"  {h.ticker}: {h.quantity} shares @ ${h.current_price:.2f} = ${h.value:.2f}")
```

---

## Core Concepts

### How the Market Works

Market-Sim is a **continuous double auction** — the same mechanism used by real stock exchanges.

- **Bids** (buy orders) sit on the book sorted by price descending (highest first)
- **Asks** (sell orders) sit on the book sorted by price ascending (lowest first)
- When a new order arrives, it matches against resting orders at the resting order's price
- Orders match in **price-time priority**: best price first, then earliest order at that price
- A built-in **market maker bot** provides liquidity on all tickers at a 1% spread

### Escrow Model

When you place an order, funds are **deducted immediately** (escrowed), not on fill:

- **Buy order**: `price * quantity` deducted from cash
- **Sell order**: `quantity` shares deducted from portfolio

If the order fills at a better price, you get a **refund** for the difference. If you cancel a resting order, escrowed funds are returned in full.

This means your **buying power** (available cash) is always: `cash - escrowed_cash`.

### Order Types (Time-in-Force)

| Type | Behavior | Use When |
|------|----------|----------|
| `GTC` | Good-til-cancelled. Fills what it can, rest sits on the book until filled or cancelled. | Default. You want to set a limit price and wait. |
| `IOC` | Immediate-or-cancel. Fills what it can immediately, cancels the rest. No resting order. | You want to take liquidity without leaving a footprint. |
| `FOK` | Fill-or-kill. Either fills completely in one shot, or rejects entirely. Nothing partial. | You need all-or-nothing execution (e.g., pairs trading). |

### Tickers

Default market has 5 tickers with initial prices:

| Ticker | Initial Price |
|--------|--------------|
| FUN | $100.00 |
| MEME | $50.00 |
| YOLO | $200.00 |
| HODL | $75.00 |
| PUMP | $25.00 |

Prices move based on trading activity. The market maker quotes at +-1% of the last trade price.

---

## SDK Reference

### MarketSimClient (REST)

All methods are synchronous. For async usage, wrap in `asyncio.to_thread()` or use the WebSocket client.

#### Market Data (No Authentication Required)

```python
# All tickers with current prices and bid/ask
tickers: dict[str, TickerInfo] = client.get_tickers()

# Order book for a specific ticker
book: dict = client.get_orderbook("FUN")
# Returns: {"bids": [{"price": 99.0, "quantity": 15}, ...], "asks": [...]}

# OHLCV candle data
candles: list[Candle] = client.get_history(
    ticker="FUN",
    interval="5m",     # Options: 1m, 5m, 15m, 1h, 1d
    start="2025-01-01T00:00:00",  # Optional ISO datetime
    end="2025-01-02T00:00:00",    # Optional ISO datetime
)

# Top 50 users by total portfolio value
leaderboard: list[dict] = client.get_leaderboard()
```

#### Trading (Authentication Required)

```python
# Place a limit order
result: OrderResult = client.place_order(
    ticker="FUN",
    side="buy",           # "buy" or "sell"
    price=99.50,          # Limit price (rounded to 2 decimals)
    quantity=10,           # Number of shares (positive integer)
    time_in_force="GTC",  # "GTC", "IOC", or "FOK"
)
# result.status: "filled", "partial", "open", or "cancelled" (IOC with no fills)
# result.trades: list of fills that happened immediately
# result.filled_quantity: total shares filled

# Cancel a resting order
cancel: CancelResult = client.cancel_order(order_id="uuid-here")

# List your open/partial orders
orders: list[OpenOrder] = client.get_orders(limit=50, offset=0)

# List your trade history
trades: list[TradeResult] = client.get_trades(
    ticker="FUN",   # Optional filter
    limit=50,
    offset=0,
)

# Check your portfolio
portfolio: Portfolio = client.get_portfolio()
# portfolio.cash: total cash (including escrowed)
# portfolio.buying_power: available cash (cash - escrowed)
# portfolio.escrowed_cash: cash locked in open buy orders
# portfolio.holdings: list of Holding (ticker, quantity, current_price, value)
# portfolio.total_value: cash + sum of holdings values
```

### MarketSimWS (WebSocket)

Async client for real-time market data. Subscribe to channels before calling `run()`.

```python
import asyncio
from marketsim import MarketSimWS

ws = MarketSimWS("https://marketsim.example.com")

# Subscribe to price updates (all tickers)
def on_prices(data):
    for ticker, info in data["data"].items():
        print(f"{ticker}: ${info['current_price']:.2f}")

ws.subscribe("prices", on_prices)

# Subscribe to trades on a specific ticker
def on_trade(data):
    print(f"Trade: {data['quantity']} shares @ ${data['price']:.2f}")

ws.subscribe("trades:FUN", on_trade)

# Subscribe to order book updates
def on_orderbook(data):
    best_bid = data["bids"][0]["price"] if data["bids"] else None
    best_ask = data["asks"][0]["price"] if data["asks"] else None
    print(f"Book: {best_bid} / {best_ask}")

ws.subscribe("orderbook:FUN", on_orderbook)

# Run (blocks until cancelled)
asyncio.run(ws.run())
```

#### WebSocket Channels

| Channel | Data | Frequency |
|---------|------|-----------|
| `prices` | All tickers: `current_price`, `best_bid`, `best_ask` | On every trade |
| `trades:{ticker}` | Individual trades: `price`, `quantity`, `timestamp` | On every trade for that ticker |
| `orderbook:{ticker}` | Full aggregated book: `bids[]`, `asks[]` | Throttled to every 0.5s |

#### Combining REST + WebSocket

The most effective pattern: use REST for actions, WebSocket for reactions.

```python
import asyncio
import threading
from marketsim import MarketSimClient, MarketSimWS

API_KEY = "your-api-key"
BASE_URL = "https://marketsim.example.com"

# REST client for trading
client = MarketSimClient(BASE_URL, API_KEY)

# Track latest prices in a thread-safe dict
latest_prices = {}
price_lock = threading.Lock()

def on_prices(data):
    with price_lock:
        for ticker, info in data["data"].items():
            latest_prices[ticker] = info["current_price"]

# Run WebSocket in a background thread
ws = MarketSimWS(BASE_URL)
ws.subscribe("prices", on_prices)

def run_ws():
    asyncio.run(ws.run())

ws_thread = threading.Thread(target=run_ws, daemon=True)
ws_thread.start()

# Main trading loop uses latest prices
import time
while True:
    with price_lock:
        prices = dict(latest_prices)

    if not prices:
        time.sleep(1)
        continue

    # Your strategy logic here
    for ticker, price in prices.items():
        # Example: buy if price drops below initial
        pass

    time.sleep(2)
```

---

## Strategy Patterns

### 1. Simple Moving Average Crossover

Buy when short-term average crosses above long-term average. Sell when it crosses below.

```python
from collections import deque
from marketsim import MarketSimClient

client = MarketSimClient("https://marketsim.example.com", "your-api-key")
TICKER = "FUN"

short_window = deque(maxlen=5)   # 5-period SMA
long_window = deque(maxlen=20)   # 20-period SMA
position = 0  # current shares held

while True:
    tickers = client.get_tickers()
    price = tickers[TICKER].current_price
    if price is None:
        time.sleep(2)
        continue

    short_window.append(price)
    long_window.append(price)

    if len(long_window) < 20:
        time.sleep(2)
        continue

    short_avg = sum(short_window) / len(short_window)
    long_avg = sum(long_window) / len(long_window)

    portfolio = client.get_portfolio()

    if short_avg > long_avg and position == 0:
        # Golden cross — buy
        qty = int(portfolio.buying_power * 0.5 / price)  # use 50% of cash
        if qty > 0:
            result = client.place_order(TICKER, "buy", price, qty, "IOC")
            position += result.filled_quantity

    elif short_avg < long_avg and position > 0:
        # Death cross — sell all
        result = client.place_order(TICKER, "sell", price * 0.99, position, "IOC")
        position -= result.filled_quantity

    time.sleep(5)
```

### 2. Market Making

Profit from the spread by quoting both sides. Risk: inventory accumulation.

```python
TICKER = "FUN"
SPREAD = 0.005  # 0.5% spread
QTY = 5

while True:
    tickers = client.get_tickers()
    price = tickers[TICKER].current_price

    # Cancel any existing orders
    for order in client.get_orders():
        if order.ticker == TICKER:
            client.cancel_order(order.order_id)

    # Quote both sides
    bid_price = round(price * (1 - SPREAD), 2)
    ask_price = round(price * (1 + SPREAD), 2)

    # Check inventory — don't accumulate too much
    portfolio = client.get_portfolio()
    holdings = {h.ticker: h.quantity for h in portfolio.holdings}
    current_qty = holdings.get(TICKER, 0)

    if current_qty < 50:  # max inventory
        client.place_order(TICKER, "buy", bid_price, QTY, "GTC")
    if current_qty > 0:
        client.place_order(TICKER, "sell", ask_price, min(QTY, current_qty), "GTC")

    time.sleep(3)
```

### 3. Mean Reversion

Assume prices revert to a rolling average. Buy when cheap, sell when expensive.

```python
from collections import deque

TICKER = "MEME"
WINDOW = 50
THRESHOLD = 0.02  # 2% deviation triggers trade

prices = deque(maxlen=WINDOW)

while True:
    tickers = client.get_tickers()
    price = tickers[TICKER].current_price
    prices.append(price)

    if len(prices) < WINDOW:
        time.sleep(2)
        continue

    mean = sum(prices) / len(prices)
    deviation = (price - mean) / mean

    portfolio = client.get_portfolio()
    holdings = {h.ticker: h.quantity for h in portfolio.holdings}
    qty = holdings.get(TICKER, 0)

    if deviation < -THRESHOLD and portfolio.buying_power > price * 5:
        # Price is below mean — buy
        client.place_order(TICKER, "buy", price, 5, "IOC")

    elif deviation > THRESHOLD and qty > 0:
        # Price is above mean — sell
        client.place_order(TICKER, "sell", price, min(5, qty), "IOC")

    time.sleep(3)
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /api/orders` | 30 requests | 60 seconds |
| `DELETE /api/orders/{id}` | 30 requests | 60 seconds |
| All other endpoints | No limit (currently) | — |

If you exceed the rate limit, you'll receive a `429 Too Many Requests` response. The SDK raises `requests.HTTPError` — catch it and back off.

```python
import time
from requests import HTTPError

try:
    result = client.place_order("FUN", "buy", 100.0, 10)
except HTTPError as e:
    if e.response.status_code == 429:
        print("Rate limited — waiting 5 seconds")
        time.sleep(5)
    else:
        raise
```

**Best practice**: Space your order requests at least 2 seconds apart. Use `IOC` for aggressive fills (avoids creating resting orders you need to manage). Use `GTC` for passive strategies where you want to rest on the book.

---

## Rules & Fair Play

### Allowed

- Multiple bots per user (but share the same rate limit)
- Any strategy that doesn't violate the rules below
- Using WebSocket data to inform trading decisions
- Coordinating with other players (alliances are allowed)
- Running bots 24/7

### Not Allowed

- **Self-trading**: Placing orders designed to fill against your own resting orders (detected automatically)
- **Wash trading**: Coordinating circular trades with another account to manipulate volume/prices
- **Account sharing**: One person per account
- **API abuse**: Intentionally flooding endpoints to degrade service for others
- **Exploiting bugs**: If you find a bug, report it — exploiting it may result in disqualification

### Penalties

- First offense: Warning + trade reversal
- Second offense: Tournament disqualification
- Third offense: Account suspension

---

## Debugging Tips

### Check Your Order Status

```python
orders = client.get_orders()
for o in orders:
    print(f"{o.order_id}: {o.side} {o.quantity} {o.ticker} @ {o.price} — {o.status} ({o.filled_quantity} filled)")
```

### Check the Order Book Before Trading

```python
book = client.get_orderbook("FUN")
print("Best bid:", book["bids"][0] if book["bids"] else "empty")
print("Best ask:", book["asks"][0] if book["asks"] else "empty")
```

### Understanding "Insufficient Funds"

This means your order's total cost (`price * quantity`) exceeds your **buying power** (not your total cash). Check your escrowed cash:

```python
p = client.get_portfolio()
print(f"Cash: ${p.cash:.2f}")
print(f"Escrowed: ${p.escrowed_cash:.2f}")
print(f"Buying power: ${p.buying_power:.2f}")
```

If you have open buy orders, they're holding escrow. Cancel them to free up cash:

```python
for order in client.get_orders():
    if order.side == "buy":
        client.cancel_order(order.order_id)
```

### Why Didn't My Order Fill?

1. **Price too low (buy) or too high (sell)**: Your limit price doesn't cross the best ask/bid
2. **Not enough liquidity**: Book is thin — try IOC with a more aggressive price
3. **FOK rejected**: Not enough shares available at your price to fill the entire order
4. **Rate limited**: Check for 429 errors in your logs

### Monitoring Your Bot

Keep a simple log:

```python
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("my_bot")

result = client.place_order("FUN", "buy", 100.0, 10)
logger.info(f"Order {result.order_id}: {result.status} ({result.filled_quantity} filled)")
```

---

## Data Models

### TickerInfo
```python
@dataclass
class TickerInfo:
    current_price: float | None  # Last trade price (None if no trades yet)
    best_bid: float | None       # Highest resting buy order
    best_ask: float | None       # Lowest resting sell order
```

### OrderResult
```python
@dataclass
class OrderResult:
    order_id: str          # UUID of the order
    ticker: str
    side: str              # "buy" or "sell"
    price: float           # Limit price submitted
    quantity: int           # Total quantity requested
    filled_quantity: int    # How many shares filled immediately
    status: str            # "filled", "partial", "open", "cancelled"
    trades: list[dict]     # Fills: [{"trade_id", "price", "quantity", "buyer_id", "seller_id"}]
```

### Portfolio
```python
@dataclass
class Portfolio:
    user_id: str
    username: str
    cash: float            # Total cash (includes escrowed)
    buying_power: float    # Cash available for new orders
    escrowed_cash: float   # Cash locked in open buy orders
    holdings: list[Holding]
    total_value: float     # cash + sum(holding values)

@dataclass
class Holding:
    ticker: str
    quantity: int
    current_price: float
    value: float           # quantity * current_price
```

### Candle
```python
@dataclass
class Candle:
    timestamp: str   # ISO 8601 datetime (start of candle)
    open: float
    high: float
    low: float
    close: float
    volume: int      # Total shares traded in this candle
```
