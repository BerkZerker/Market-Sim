import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { resetStore } from "../../test/mocks";

vi.mock("../../api/client", () => ({
  getTickers: vi.fn(),
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

describe("Dashboard", () => {
  it("shows spinner while loading", async () => {
    const { getTickers } = await import("../../api/client");
    vi.mocked(getTickers).mockReturnValue(new Promise(() => {})); // never resolves

    const Dashboard = (await import("../Dashboard")).default;
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    expect(document.querySelector("svg.animate-spin")).toBeInTheDocument();
  });

  it("renders price cards after loading", async () => {
    const { getTickers } = await import("../../api/client");
    vi.mocked(getTickers).mockResolvedValue({
      tickers: {
        FUN: { current_price: 100, best_bid: 99, best_ask: 101 },
        MEME: { current_price: 50, best_bid: 49, best_ask: 51 },
      },
    });

    const Dashboard = (await import("../Dashboard")).default;
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("FUN")).toBeInTheDocument();
      expect(screen.getByText("MEME")).toBeInTheDocument();
    });
  });
});
