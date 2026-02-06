import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import OrderBookView from "../OrderBookView";

describe("OrderBookView", () => {
  it("renders bid and ask levels", () => {
    const bids = [{ price: 99.0, quantity: 10 }];
    const asks = [{ price: 101.0, quantity: 5 }];

    render(<OrderBookView bids={bids} asks={asks} />);

    expect(screen.getByText("$99.00")).toBeInTheDocument();
    expect(screen.getByText("$101.00")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("shows spread when both sides have levels", () => {
    const bids = [{ price: 99.0, quantity: 10 }];
    const asks = [{ price: 101.0, quantity: 5 }];

    render(<OrderBookView bids={bids} asks={asks} />);

    expect(screen.getByText("$2.00")).toBeInTheDocument(); // spread
    expect(screen.getByText("$100.00")).toBeInTheDocument(); // mid
  });
});
