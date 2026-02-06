import { create } from "zustand";

interface TickerPrice {
  current_price: number | null;
  best_bid: number | null;
  best_ask: number | null;
}

interface Holding {
  ticker: string;
  quantity: number;
  current_price: number;
  value: number;
}

interface PricePoint {
  time: string;
  price: number;
}

interface UserState {
  userId: string | null;
  username: string | null;
  jwtToken: string | null;
  apiKey: string | null;
  cash: number;
  holdings: Holding[];
  totalValue: number;
}

interface MarketState {
  prices: Record<string, TickerPrice>;
  priceHistory: Record<string, PricePoint[]>;
}

interface OrderBookLevel {
  price: number;
  quantity: number;
}

interface OrderBookState {
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
}

interface Notification {
  id: string;
  message: string;
  type: "error" | "success" | "info";
}

interface AppState {
  user: UserState;
  market: MarketState;
  orderbook: OrderBookState;
  notifications: Notification[];
  wsConnected: boolean;

  setUser: (user: Partial<UserState>) => void;
  logout: () => void;
  setPrices: (prices: Record<string, TickerPrice>) => void;
  addPricePoint: (ticker: string, price: number) => void;
  setOrderbook: (bids: OrderBookLevel[], asks: OrderBookLevel[]) => void;
  setPortfolio: (cash: number, holdings: Holding[], totalValue: number) => void;
  addNotification: (message: string, type: Notification["type"]) => void;
  removeNotification: (id: string) => void;
  setWsConnected: (connected: boolean) => void;
}

export const useStore = create<AppState>((set, get) => ({
  user: {
    userId: localStorage.getItem("user_id"),
    username: localStorage.getItem("username"),
    jwtToken: localStorage.getItem("jwt_token"),
    apiKey: localStorage.getItem("api_key"),
    cash: 0,
    holdings: [],
    totalValue: 0,
  },
  market: {
    prices: {},
    priceHistory: {},
  },
  orderbook: {
    bids: [],
    asks: [],
  },
  notifications: [],
  wsConnected: false,

  setUser: (userData) =>
    set((state) => {
      if (userData.jwtToken) localStorage.setItem("jwt_token", userData.jwtToken);
      if (userData.apiKey) localStorage.setItem("api_key", userData.apiKey);
      if (userData.userId) localStorage.setItem("user_id", userData.userId);
      if (userData.username) localStorage.setItem("username", userData.username);
      return { user: { ...state.user, ...userData } };
    }),

  logout: () =>
    set(() => {
      localStorage.removeItem("jwt_token");
      localStorage.removeItem("api_key");
      localStorage.removeItem("user_id");
      localStorage.removeItem("username");
      return {
        user: {
          userId: null,
          username: null,
          jwtToken: null,
          apiKey: null,
          cash: 0,
          holdings: [],
          totalValue: 0,
        },
      };
    }),

  setPrices: (prices) =>
    set((state) => ({
      market: { ...state.market, prices },
    })),

  addPricePoint: (ticker, price) =>
    set((state) => {
      const history = { ...state.market.priceHistory };
      const points = history[ticker] || [];
      const now = new Date().toLocaleTimeString();
      history[ticker] = [...points.slice(-99), { time: now, price }];
      return { market: { ...state.market, priceHistory: history } };
    }),

  setOrderbook: (bids, asks) =>
    set(() => ({
      orderbook: { bids, asks },
    })),

  setPortfolio: (cash, holdings, totalValue) =>
    set((state) => ({
      user: { ...state.user, cash, holdings, totalValue },
    })),

  addNotification: (message, type) => {
    const id = Date.now().toString();
    set((state) => ({
      notifications: [...state.notifications.slice(-4), { id, message, type }],
    }));
    setTimeout(() => get().removeNotification(id), 5000);
  },

  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  setWsConnected: (connected) => set({ wsConnected: connected }),
}));
