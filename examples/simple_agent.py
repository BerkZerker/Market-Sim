"""
Simple AI Trading Agent Example

Demonstrates how to connect to Market Sim via the API:
1. Register a new account
2. Check market prices
3. Place buy/sell orders
4. Check portfolio

Usage:
    pip install requests
    python examples/simple_agent.py
"""

import random
import time

import requests

BASE_URL = "http://localhost:8000/api"


def main():
    # 1. Register
    username = f"agent_{random.randint(1000, 9999)}"
    print(f"Registering as {username}...")
    resp = requests.post(
        f"{BASE_URL}/register",
        json={"username": username, "password": "secret123"},
    )
    resp.raise_for_status()
    data = resp.json()
    api_key = data["api_key"]
    print(f"  User ID: {data['user_id']}")
    print(f"  API Key: {api_key}")
    print(f"  Cash: ${data['cash']:.2f}")

    headers = {"X-API-Key": api_key}

    # 2. Check market prices
    print("\nMarket prices:")
    resp = requests.get(f"{BASE_URL}/market/tickers", headers=headers)
    resp.raise_for_status()
    tickers = resp.json()["tickers"]
    for ticker, info in tickers.items():
        price = info["current_price"]
        print(f"  {ticker}: ${price:.2f}" if price else f"  {ticker}: no price")

    # 3. Place some orders
    for _ in range(5):
        ticker = random.choice(list(tickers.keys()))
        price = tickers[ticker]["current_price"]
        if price is None:
            continue

        side = random.choice(["buy", "sell"])
        # Small deviation from market price
        order_price = round(price * random.uniform(0.98, 1.02), 2)
        quantity = random.randint(1, 10)

        print(f"\nPlacing {side} order: {quantity} {ticker} @ ${order_price:.2f}")
        resp = requests.post(
            f"{BASE_URL}/orders",
            json={
                "ticker": ticker,
                "side": side,
                "price": order_price,
                "quantity": quantity,
            },
            headers=headers,
        )
        if resp.ok:
            result = resp.json()
            print(f"  Status: {result['status']}, Filled: {result['filled_quantity']}/{result['quantity']}")
            for trade in result["trades"]:
                print(f"  Trade: {trade['quantity']} @ ${trade['price']:.2f}")
        else:
            print(f"  Error: {resp.json().get('detail', resp.text)}")

        time.sleep(0.5)

    # 4. Check portfolio
    print("\nPortfolio:")
    resp = requests.get(f"{BASE_URL}/portfolio", headers=headers)
    resp.raise_for_status()
    portfolio = resp.json()
    print(f"  Cash: ${portfolio['cash']:.2f}")
    for holding in portfolio["holdings"]:
        print(
            f"  {holding['ticker']}: {holding['quantity']} shares "
            f"(${holding['value']:.2f})"
        )
    print(f"  Total Value: ${portfolio['total_value']:.2f}")

    # 5. Check leaderboard
    print("\nLeaderboard:")
    resp = requests.get(f"{BASE_URL}/leaderboard", headers=headers)
    resp.raise_for_status()
    for i, entry in enumerate(resp.json()["leaderboard"][:10], 1):
        print(f"  #{i} {entry['username']}: ${entry['total_value']:.2f}")


if __name__ == "__main__":
    main()
