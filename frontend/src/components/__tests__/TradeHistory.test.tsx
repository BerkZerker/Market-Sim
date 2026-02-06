import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import TradeHistory from "../TradeHistory";

describe("TradeHistory", () => {
  it("shows empty state when no trades", () => {
    render(<TradeHistory trades={[]} />);
    expect(screen.getByText("No trades yet")).toBeInTheDocument();
  });

  it("renders trade rows", () => {
    const trades = [
      { price: 100.5, quantity: 10, timestamp: 1700000000 },
      { price: 99.0, quantity: 5, timestamp: 1700000060 },
    ];
    render(<TradeHistory trades={trades} />);

    expect(screen.getByText("$100.50")).toBeInTheDocument();
    expect(screen.getByText("$99.00")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });
});
