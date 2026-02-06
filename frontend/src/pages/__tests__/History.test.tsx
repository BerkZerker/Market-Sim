import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { resetStore, setLoggedInUser } from "../../test/mocks";

vi.mock("../../api/client", () => ({
  getOrders: vi.fn(),
  getTrades: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  resetStore();
  mockNavigate.mockReset();
});

describe("History", () => {
  it("renders orders tab with data", async () => {
    setLoggedInUser();
    const { getOrders } = await import("../../api/client");
    vi.mocked(getOrders).mockResolvedValue([
      {
        order_id: "order-abc-123",
        ticker: "FUN",
        side: "buy",
        price: 100,
        quantity: 10,
        filled_quantity: 5,
        status: "partial",
        created_at: "2024-01-01T00:00:00Z",
      },
    ]);

    const History = (await import("../History")).default;
    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("FUN")).toBeInTheDocument();
      expect(screen.getByText("partial")).toBeInTheDocument();
    });
  });
});
