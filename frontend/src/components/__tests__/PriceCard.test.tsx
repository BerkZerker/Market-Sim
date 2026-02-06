import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import PriceCard from "../PriceCard";

function renderCard(props = {}) {
  const defaults = {
    ticker: "FUN",
    price: 100.5,
    bestBid: 99.0,
    bestAsk: 101.0,
  };
  return render(
    <MemoryRouter>
      <PriceCard {...defaults} {...props} />
    </MemoryRouter>,
  );
}

describe("PriceCard", () => {
  it("renders ticker name and price", () => {
    renderCard();
    expect(screen.getByText("FUN")).toBeInTheDocument();
    expect(screen.getByText("$100.50")).toBeInTheDocument();
  });

  it("links to the ticker detail page", () => {
    renderCard();
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/ticker/FUN");
  });
});
