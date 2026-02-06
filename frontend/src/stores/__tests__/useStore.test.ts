import { beforeEach, describe, expect, it, vi } from "vitest";
import { useStore } from "../useStore";
import { resetStore } from "../../test/mocks";

beforeEach(() => {
  resetStore();
});

describe("useStore", () => {
  it("sets user data and persists to localStorage", () => {
    useStore.getState().setUser({
      userId: "u1",
      username: "alice",
      jwtToken: "jwt-abc",
    });

    const { user } = useStore.getState();
    expect(user.userId).toBe("u1");
    expect(user.username).toBe("alice");
    expect(user.jwtToken).toBe("jwt-abc");
    expect(localStorage.getItem("user_id")).toBe("u1");
    expect(localStorage.getItem("jwt_token")).toBe("jwt-abc");
  });

  it("clears user state and localStorage on logout", () => {
    useStore.getState().setUser({ userId: "u1", jwtToken: "jwt" });
    useStore.getState().logout();

    const { user } = useStore.getState();
    expect(user.userId).toBeNull();
    expect(user.jwtToken).toBeNull();
    expect(localStorage.getItem("jwt_token")).toBeNull();
  });

  it("sets market prices", () => {
    const prices = {
      FUN: { current_price: 100, best_bid: 99, best_ask: 101 },
    };
    useStore.getState().setPrices(prices);

    expect(useStore.getState().market.prices).toEqual(prices);
  });

  it("adds price point and caps history at 100", () => {
    // Add 105 points
    for (let i = 0; i < 105; i++) {
      useStore.getState().addPricePoint("FUN", 100 + i);
    }
    const history = useStore.getState().market.priceHistory["FUN"];
    expect(history).toHaveLength(100);
    expect(history[99].price).toBe(204); // last one added: 100+104
  });

  it("sets orderbook", () => {
    const bids = [{ price: 99, quantity: 10 }];
    const asks = [{ price: 101, quantity: 5 }];
    useStore.getState().setOrderbook(bids, asks);

    expect(useStore.getState().orderbook.bids).toEqual(bids);
    expect(useStore.getState().orderbook.asks).toEqual(asks);
  });

  it("adds and removes notifications", () => {
    vi.useFakeTimers();

    useStore.getState().addNotification("Test error", "error");
    expect(useStore.getState().notifications).toHaveLength(1);
    expect(useStore.getState().notifications[0].message).toBe("Test error");

    const id = useStore.getState().notifications[0].id;
    useStore.getState().removeNotification(id);
    expect(useStore.getState().notifications).toHaveLength(0);

    vi.useRealTimers();
  });

  it("sets portfolio data", () => {
    const holdings = [
      { ticker: "FUN", quantity: 10, current_price: 100, value: 1000 },
    ];
    useStore.getState().setPortfolio(9000, holdings, 10000);

    const { user } = useStore.getState();
    expect(user.cash).toBe(9000);
    expect(user.holdings).toEqual(holdings);
    expect(user.totalValue).toBe(10000);
  });
});
