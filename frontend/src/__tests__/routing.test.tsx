import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { resetStore } from "../test/mocks";

vi.mock("../api/client", () => ({
  getTickers: vi.fn().mockResolvedValue({ tickers: {} }),
  getLeaderboard: vi.fn().mockResolvedValue({ leaderboard: [] }),
}));

vi.mock("../api/ws", () => ({
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

describe("Routing", () => {
  it("renders Dashboard at /", async () => {
    const Dashboard = (await import("../pages/Dashboard")).default;
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Market Dashboard")).toBeInTheDocument();
    });
  });

  it("renders Login at /login", async () => {
    const Login = (await import("../pages/Login")).default;
    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<Login />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: "Login" })).toBeInTheDocument();
  });
});
