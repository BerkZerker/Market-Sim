import time
import random
from collections import deque
from itertools import zip_longest

from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.text import Text

from agent import Agent
from core.order import Order
from engine.matching_engine import MatchingEngine
from engine.orderbook import OrderBook

def create_layout() -> Layout:
    """
    Creates the layout for the terminal UI.
    """
    layout = Layout()
    layout.split_column(
        Layout(name="header", ratio=2),
        Layout(ratio=1, name="main"),
    )
    layout["main"].split_row(
        Layout(name="order_book", ratio=1),
        Layout(name="charts", ratio=2),
    )
    layout["charts"].split_column(
        Layout(name="ticker_price", ratio=1),
        Layout(name="candlestick_chart", ratio=2),
    )
    return layout

def create_order_book_table(order_book: OrderBook) -> Table:
    """
    Creates a table for the order book.
    """
    table = Table(title=f"Order Book for {order_book.ticker}")
    table.add_column("Bids", justify="right", style="green")
    table.add_column("Asks", justify="left", style="red")

    for bid, ask in zip_longest(order_book.bids, order_book.asks, fillvalue=None):
        bid_str = f"{bid.price:.2f} ({bid.quantity})" if bid else ""
        ask_str = f"{ask.price:.2f} ({ask.quantity})" if ask else ""
        table.add_row(bid_str, ask_str)
    return table

def create_bids_asks_chart(order_book: OrderBook, width: int = 80, height: int = 10) -> Text:
    """
    Creates a horizontal bar chart for the bid and ask volumes.
    """
    bids = order_book.bids
    asks = order_book.asks

    if not bids and not asks:
        return Text("No data", justify="center")

    all_prices = [o.price for o in bids] + [o.price for o in asks]
    min_price = min(all_prices) if all_prices else 0
    max_price = max(all_prices) if all_prices else 1

    price_range = max_price - min_price
    if price_range == 0:
        price_range = 1

    bid_bins = [0] * width
    ask_bins = [0] * width

    for bid in bids:
        bin_index = int(((bid.price - min_price) / price_range) * (width - 1))
        bid_bins[bin_index] += bid.quantity

    for ask in asks:
        bin_index = int(((ask.price - min_price) / price_range) * (width - 1))
        ask_bins[bin_index] += ask.quantity
    
    max_vol = 0
    if bid_bins:
        max_vol = max(max_vol, max(bid_bins))
    if ask_bins:
        max_vol = max(max_vol, max(ask_bins))

    if max_vol == 0:
        max_vol = 1

    chart = Text()
    for y in range(height - 1, -1, -1):
        row = Text()
        for x in range(width):
            bid_vol = bid_bins[x]
            ask_vol = ask_bins[x]

            bid_height = int((bid_vol / max_vol) * height) if max_vol > 0 else 0
            ask_height = int((ask_vol / max_vol) * height) if max_vol > 0 else 0

            if y < bid_height:
                row.append("█", style="green")
            elif y < ask_height:
                row.append("█", style="red")
            else:
                row.append(" ")
        chart.append(row)
        chart.append("\n")

    return chart

def create_candlesticks(prices: deque, bucket_size: int = 5) -> list:
    candlesticks = []
    if len(prices) < bucket_size:
        return []

    for i in range(0, len(prices) - len(prices) % bucket_size, bucket_size):
        bucket = list(prices)[i:i+bucket_size]
        open_price = bucket[0]
        close_price = bucket[-1]
        high_price = max(bucket)
        low_price = min(bucket)
        candlesticks.append((open_price, high_price, low_price, close_price))
    return candlesticks

def create_candlestick_chart(candlesticks: list, width: int = 50, height: int = 10) -> Text:
    """
    Creates a simple candlestick chart.
    """
    if not candlesticks:
        return Text("No data", justify="center")

    all_prices = [p for cs in candlesticks for p in cs]
    max_price = max(all_prices)
    min_price = min(all_prices)
    price_range = max_price - min_price if max_price > min_price else 1

    chart = Text()
    for y in range(height - 1, -1, -1):
        row = Text()
        for i, (open_price, high_price, low_price, close_price) in enumerate(candlesticks):
            if i >= width:
                break

            color = "green" if close_price >= open_price else "red"
            
            y_price = min_price + (y / (height - 1)) * price_range

            char = " "
            if low_price <= y_price <= high_price:
                char = "│" # Wick
            if min(open_price, close_price) <= y_price <= max(open_price, close_price):
                char = "┃" # Body

            row.append(char, style=color)
        chart.append(row)
        chart.append("\n")

    return chart

def create_ticker_panel(ticker: str, last_price: float, trades: list) -> Panel:
    """
    Creates a panel for the ticker information.
    """
    price_text = Text(f"{last_price:.2f}", style="bold green" if trades else "bold red")
    return Panel(price_text, title=f"Ticker: {ticker}")


def main():
    """
    Runs the market simulation.
    """
    console = Console()
    layout = create_layout()

    sim_stock_ticker = "SIM"
    market_book = OrderBook(sim_stock_ticker)
    engine = MatchingEngine(market_book)
    
    agents = [Agent() for _ in range(100)]
    last_price = 100.0
    prices = deque(maxlen=50)

    with Live(layout, console=console, screen=True, redirect_stderr=False) as live:
        while True:
            # Choose a random agent to create an order
            agent = random.choice(agents)
            order, side = agent.create_random_order(sim_stock_ticker, last_price)

            # Process the order
            trades = engine.process_order(order, side)

            if trades:
                last_price = trades[-1].price
                prices.append(last_price)

            # Update the UI
            order_book_table = create_order_book_table(market_book)
            bids_asks_chart = create_bids_asks_chart(market_book, width=console.width, height=15)
            
            candlesticks = create_candlesticks(prices)
            candlestick_chart = create_candlestick_chart(candlesticks)

            ticker_panel = create_ticker_panel(sim_stock_ticker, last_price, trades)

            layout["header"].update(Panel(bids_asks_chart, title="Bids/Asks Chart"))
            layout["order_book"].update(order_book_table)
            layout["ticker_price"].update(ticker_panel)
            layout["candlestick_chart"].update(Panel(candlestick_chart, title="Candlestick Chart"))
            
            live.update(layout)
            time.sleep(0.1)

if __name__ == "__main__":
    main()