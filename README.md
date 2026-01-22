# Market Sim

A Python-based stock market simulation engine. This project simulates a continuous double auction market where agents place buy and sell orders, and a matching engine executes trades based on price-time priority.

## Features

- **Order Book**: Manages bids (buy orders) and asks (sell orders) for simulated assets.
- **Matching Engine**: Automatically matches compatible orders, handling full and partial fills.
- **Agents**: Automated trading agents that generate random market activity to drive the simulation.
- **Core Entities**: detailed models for Orders, Trades, and Users (traders) with portfolio management.
- **Exchange Logic**: Support for multiple tickers and centralized exchange statistics (via the `Exchange` class).

## Getting Started

### Prerequisites

- Python 3.7+
- [uv](https://github.com/astral-sh/uv) (for dependency and virtual environment management)

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd market-sim
   ```

2. **Set up the environment:**
   Create a virtual environment and install dependencies using `uv`:

   ```bash
   uv venv
   source .venv/bin/activate # On Windows use `.venv\Scripts\activate`
   uv pip install -e .
   ```

## Usage

To start the simulation with the default configuration (100 agents trading a single "SIM" ticker):

```bash
market-sim
```

Or run the module directly:

```bash
python src/main.py
```

You will see real-time output in your terminal showing the last traded price and the most recent order placed by an agent.

## Architecture

The project is organized into modular components to separate data structures, logic, and simulation control.

### Project Structure

```text
src/
├── agent.py            # Automated trading agent logic
├── main.py             # Entry point for the simulation script
├── core/               # Data models
│   ├── order.py        # Order data structure and sorting logic
│   ├── trade.py        # Trade records
│   └── user.py         # User identity and portfolio state
└── engine/             # Market mechanics
    ├── exchange.py     # High-level exchange management (multi-ticker support)
    ├── matching_engine.py # Core logic for matching buy/sell orders
    └── orderbook.py    # Management of sorted Bids and Asks
```

### Key Components

- **`OrderBook`**: Maintains two sorted lists of orders:
  - **Bids**: Sorted descending by price (highest bid first).
  - **Asks**: Sorted ascending by price (lowest ask first).
- **`MatchingEngine`**: The core logic processor. It accepts an incoming order and attempts to match it against the contra-side of the `OrderBook`. If no match is found, the order is added to the book.
- **`Agent`**: Represents a market participant. Currently, agents place random buy/sell orders around the last traded price to create market noise and liquidity.
- **`Exchange`**: A wrapper class designed to manage multiple `OrderBook` and `MatchingEngine` instances, facilitating a multi-asset simulation.

## Development

This project uses modern Python tooling for code quality.

### Linting & Formatting

We use [Ruff](https://docs.astral.sh/ruff/) to maintain code style.

- **Check for errors:**

  ```bash
  ruff check
  ```

- **Auto-format code:**

  ```bash
  ruff format
  ```
