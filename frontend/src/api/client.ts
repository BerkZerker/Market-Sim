const BASE = "/api";

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem("jwt_token");
  const apiKey = localStorage.getItem("api_key");

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  } else if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || res.statusText);
  }

  return res.json();
}

export async function register(username: string, password: string) {
  return request<{
    user_id: string;
    username: string;
    api_key: string;
    jwt_token: string;
    cash: number;
  }>("/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function login(username: string, password: string) {
  return request<{
    user_id: string;
    username: string;
    jwt_token: string;
  }>("/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function getTickers() {
  return request<{
    tickers: Record<
      string,
      {
        current_price: number | null;
        best_bid: number | null;
        best_ask: number | null;
      }
    >;
  }>("/market/tickers");
}

export async function getTickerInfo(ticker: string) {
  return request<{
    ticker: string;
    current_price: number | null;
    best_bid: number | null;
    best_ask: number | null;
    bid_depth: number;
    ask_depth: number;
  }>(`/market/${ticker}`);
}

export async function getOrderbook(ticker: string) {
  return request<{
    ticker: string;
    bids: { price: number; quantity: number }[];
    asks: { price: number; quantity: number }[];
  }>(`/market/${ticker}/orderbook`);
}

export async function placeOrder(
  ticker: string,
  side: string,
  price: number,
  quantity: number,
) {
  return request<{
    order_id: string;
    ticker: string;
    side: string;
    price: number;
    quantity: number;
    filled_quantity: number;
    status: string;
    trades: {
      trade_id: string;
      ticker: string;
      price: number;
      quantity: number;
      buyer_id: string;
      seller_id: string;
    }[];
  }>("/orders", {
    method: "POST",
    body: JSON.stringify({ ticker, side, price, quantity }),
  });
}

export async function getPortfolio() {
  return request<{
    user_id: string;
    username: string;
    cash: number;
    holdings: {
      ticker: string;
      quantity: number;
      current_price: number;
      value: number;
    }[];
    total_value: number;
  }>("/portfolio");
}

export async function getLeaderboard() {
  return request<{
    leaderboard: {
      user_id: string;
      username: string;
      cash: number;
      holdings: { ticker: string; quantity: number }[];
      total_value: number;
    }[];
  }>("/leaderboard");
}
