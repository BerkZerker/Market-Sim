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
        Layout(name="header"),
        Layout(ratio=1, name="main"),
    )
    layout["main"].split_row(
        Layout(name="order_book", ratio=1),
        Layout(name="charts", ratio=2),
    )
    layout["charts"].split_column(
        Layout(name="ticker_price", ratio=1),
        Layout(name="bids_asks_chart", ratio=2),
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

def create_bids_asks_chart(order_book: OrderBook) -> Text:
    """
    Creates a U-shaped chart for the bid and ask prices.
    """
    bids = sorted(order_book.bids, key=lambda x: x.price, reverse=True)
    asks = sorted(order_book.asks, key=lambda x: x.price)

    if not bids and not asks:
        return Text("No data", justify="center")

    max_vol = 0
    if bids:
        max_vol = max(max_vol, max(bid.quantity for bid in bids))
    if asks:
        max_vol = max(max_vol, max(ask.quantity for ask in asks))

    chart = Text()
    for i in range(10, -1, -1):
        row = Text()
        # Bids
        bid_vol_str = ""
        if bids and i < len(bids):
            bid = bids[i]
            bar_len = int((bid.quantity / max_vol) * 20) if max_vol > 0 else 0
            bid_vol_str = "█" * bar_len
            row.append(f"{bid_vol_str:>20} ", style="green")
            row.append(f"{bid.price:.2f} |", style="white")
        else:
            row.append(" " * 21 + "|", style="white")

        # Asks
        if asks and i < len(asks):
            ask = asks[i]
            bar_len = int((ask.quantity / max_vol) * 20) if max_vol > 0 else 0
            ask_vol_str = "█" * bar_len
            row.append(f" {ask.price:.2f} ", style="white")
            row.append(f"{ask_vol_str:<20}", style="red")
        else:
            row.append(" " * 22, style="white")
        
        chart.append(row)
        chart.append("\n")

    return chart

def create_candlestick_chart(prices: deque) -> Text:
    """
    Creates a simple candlestick chart.
    """
    if len(prices) < 2:
        return Text("No data", justify="center")

    max_price = max(prices)
    min_price = min(prices)
    price_range = max_price - min_price if max_price > min_price else 1

    chart = Text()
    for i in range(0, len(prices) -1, 2):
        open_price = prices[i]
        close_price = prices[i+1]

        if close_price >= open_price:
            color = "green"
            body = "┃"
        else:
            color = "red"
            body = "┃"
        
        high = max(open_price, close_price)
        low = min(open_price, close_price)

        high_wick = "|" if high < max_price else " "
        low_wick = "|" if low > min_price else " "

        bar = Text()
        bar.append(high_wick + "\n", style=color)
        bar.append(body + "\n", style=color)
        bar.append(low_wick, style=color)
        chart.append(bar)
        chart.append(" ")

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
            bids_asks_chart = create_bids_asks_chart(market_book)
            candlestick_chart = create_candlestick_chart(prices)
            ticker_panel = create_ticker_panel(sim_stock_ticker, last_price, trades)

            layout["header"].update(Panel(f"Market Simulation - Ticker: {sim_stock_ticker}", style="bold blue"))
            layout["order_book"].update(order_book_table)
            layout["ticker_price"].update(ticker_panel)
            layout["bids_asks_chart"].update(Panel(bids_asks_chart, title="Bids/Asks Chart"))
            layout["candlestick_chart"].update(Panel(candlestick_chart, title="Candlestick Chart"))
            
            live.update(layout)
            time.sleep(0.1)

if __name__ == "__main__":
    main()