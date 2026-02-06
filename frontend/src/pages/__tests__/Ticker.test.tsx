import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { resetStore } from "../../test/mocks";

vi.mock("../../api/client", () => ({
  getTickerInfo: vi.fn(),
  getOrderbook: vi.fn(),
  getHistory: vi.fn(),
}));

vi.mock("../../api/ws", () => ({
  WSClient: class MockWSClient {
    connect = vi.fn();
    onMessage = vi.fn();
    onStatusChange = vi.fn();
    disconnect = vi.fn();
  },
}));

beforeEach(() => {
  resetStore();
});

describe("Ticker", () => {
  it("renders chart, order form, and order book sections", async () => {
    const { getTickerInfo, getOrderbook, getHistory } = await import("../../api/client");
    vi.mocked(getTickerInfo).mockResolvedValue({
      ticker: "FUN",
      current_price: 100,
      best_bid: 99,
      best_ask: 101,
      bid_depth: 100,
      ask_depth: 50,
    });
    vi.mocked(getOrderbook).mockResolvedValue({
      ticker: "FUN",
      bids: [{ price: 99, quantity: 10 }],
      asks: [{ price: 101, quantity: 5 }],
    });
    vi.mocked(getHistory).mockResolvedValue({
      ticker: "FUN",
      interval: "5m",
      candles: [],
    });

    const Ticker = (await import("../Ticker")).default;
    render(
      <MemoryRouter initialEntries={["/ticker/FUN"]}>
        <Routes>
          <Route path="/ticker/:symbol" element={<Ticker />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("FUN")).toBeInTheDocument();
      expect(screen.getByText("Price Chart")).toBeInTheDocument();
      expect(screen.getByText("Place Order")).toBeInTheDocument();
      expect(screen.getByText("Order Book")).toBeInTheDocument();
    });
  });
});
