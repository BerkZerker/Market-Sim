import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { resetStore, setLoggedInUser } from "../../test/mocks";
import OrderForm from "../OrderForm";

vi.mock("../../api/client", () => ({
  placeOrder: vi.fn(),
}));

beforeEach(() => {
  resetStore();
});

describe("OrderForm", () => {
  it("shows login prompt when not authenticated", () => {
    render(<OrderForm ticker="FUN" currentPrice={100} />);
    expect(screen.getByText("Log in to place orders")).toBeInTheDocument();
  });

  it("renders form when authenticated", () => {
    setLoggedInUser();
    render(<OrderForm ticker="FUN" currentPrice={100} />);

    expect(screen.getByText("Buy")).toBeInTheDocument();
    expect(screen.getByText("Sell")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Price")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Quantity")).toBeInTheDocument();
  });

  it("submits order and shows status", async () => {
    setLoggedInUser();
    const { placeOrder } = await import("../../api/client");
    vi.mocked(placeOrder).mockResolvedValue({
      order_id: "o1",
      ticker: "FUN",
      side: "buy",
      price: 100,
      quantity: 10,
      filled_quantity: 5,
      status: "partial",
      trades: [],
    });

    render(<OrderForm ticker="FUN" currentPrice={100} />);

    await userEvent.click(screen.getByText("Place Buy Order"));

    await waitFor(() => {
      expect(screen.getByText("Order partial: 5/10 filled")).toBeInTheDocument();
    });
  });
});
