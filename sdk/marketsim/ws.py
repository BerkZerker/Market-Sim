"""Async WebSocket client for real-time Market-Sim data."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any

import websockets


class MarketSimWS:
    """Subscribe to real-time channels: prices, trades:{ticker}, orderbook:{ticker}."""

    def __init__(self, base_url: str):
        # Convert http(s) to ws(s)
        self._ws_base = (
            base_url.rstrip("/")
            .replace("http://", "ws://")
            .replace("https://", "wss://")
        )
        self._callbacks: dict[str, list[Callable[[dict], Any]]] = {}
        self._connections: dict[str, Any] = {}
        self._tasks: list[asyncio.Task] = []

    def subscribe(self, channel: str, callback: Callable[[dict], Any]) -> None:
        """Register a callback for a channel. Call before run()."""
        if channel not in self._callbacks:
            self._callbacks[channel] = []
        self._callbacks[channel].append(callback)

    async def _listen(self, channel: str) -> None:
        url = f"{self._ws_base}/ws/{channel}"
        while True:
            try:
                async with websockets.connect(url) as ws:
                    self._connections[channel] = ws
                    async for message in ws:
                        data = json.loads(message)
                        for cb in self._callbacks.get(channel, []):
                            cb(data)
            except (
                websockets.ConnectionClosed,
                ConnectionRefusedError,
                OSError,
            ):
                await asyncio.sleep(3)

    async def run(self) -> None:
        """Start listening on all subscribed channels. Blocks until cancelled."""
        for channel in self._callbacks:
            task = asyncio.create_task(self._listen(channel))
            self._tasks.append(task)
        if self._tasks:
            await asyncio.gather(*self._tasks)

    async def close(self) -> None:
        """Cancel all listener tasks."""
        for task in self._tasks:
            task.cancel()
        for ws in self._connections.values():
            await ws.close()
        self._tasks.clear()
        self._connections.clear()
