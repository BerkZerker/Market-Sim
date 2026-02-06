import { useStore } from "../stores/useStore";

/** Reset Zustand store to initial state between tests. */
export function resetStore() {
  useStore.setState({
    user: {
      userId: null,
      username: null,
      jwtToken: null,
      apiKey: null,
      cash: 0,
      holdings: [],
      totalValue: 0,
    },
    market: { prices: {}, priceHistory: {} },
    orderbook: { bids: [], asks: [] },
    notifications: [],
    wsConnected: false,
  });
}

/** Set store to a logged-in user state. */
export function setLoggedInUser(
  username = "testuser",
  jwtToken = "test-jwt-token",
) {
  useStore.setState({
    user: {
      userId: "user-123",
      username,
      jwtToken,
      apiKey: null,
      cash: 10000,
      holdings: [],
      totalValue: 10000,
    },
  });
}
