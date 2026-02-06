import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getOrders, getTrades } from "../api/client";
import Spinner from "../components/Spinner";
import { useStore } from "../stores/useStore";

type Tab = "orders" | "trades";

interface Order {
  order_id: string;
  ticker: string;
  side: string;
  price: number;
  quantity: number;
  filled_quantity: number;
  status: string;
  created_at: string;
}

interface Trade {
  trade_id: string;
  ticker: string;
  price: number;
  quantity: number;
  side: string;
  counterparty_id: string;
  order_id: string;
  created_at: string;
}

const PAGE_SIZE = 20;

const statusColors: Record<string, string> = {
  open: "bg-blue-600/20 text-blue-400",
  partial: "bg-yellow-600/20 text-yellow-400",
  filled: "bg-green-600/20 text-green-400",
  cancelled: "bg-neutral-600/20 text-neutral-400",
};

export default function History() {
  const { username } = useStore((s) => s.user);
  const addNotification = useStore((s) => s.addNotification);
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("orders");
  const [orders, setOrders] = useState<Order[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [tickerFilter, setTickerFilter] = useState("");

  useEffect(() => {
    if (!username) {
      navigate("/login");
    }
  }, [username, navigate]);

  useEffect(() => {
    if (!username) return;
    setLoading(true);
    if (tab === "orders") {
      getOrders(PAGE_SIZE, page * PAGE_SIZE)
        .then(setOrders)
        .catch((err) => addNotification(err.message || "Failed to load orders", "error"))
        .finally(() => setLoading(false));
    } else {
      getTrades(tickerFilter || undefined, PAGE_SIZE, page * PAGE_SIZE)
        .then(setTrades)
        .catch((err) => addNotification(err.message || "Failed to load trades", "error"))
        .finally(() => setLoading(false));
    }
  }, [username, tab, page, tickerFilter, addNotification]);

  if (!username) return null;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">History</h1>

      {/* Tab toggle */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => { setTab("orders"); setPage(0); }}
          className={`flex-1 max-w-[120px] py-1.5 rounded text-sm font-semibold transition ${
            tab === "orders" ? "bg-blue-600 text-white" : "bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400"
          }`}
        >
          Orders
        </button>
        <button
          onClick={() => { setTab("trades"); setPage(0); }}
          className={`flex-1 max-w-[120px] py-1.5 rounded text-sm font-semibold transition ${
            tab === "trades" ? "bg-blue-600 text-white" : "bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400"
          }`}
        >
          Trades
        </button>
      </div>

      {/* Ticker filter for trades */}
      {tab === "trades" && (
        <input
          type="text"
          placeholder="Filter by ticker..."
          value={tickerFilter}
          onChange={(e) => { setTickerFilter(e.target.value.toUpperCase()); setPage(0); }}
          className="mb-4 bg-neutral-100 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded px-3 py-2 text-sm w-48"
        />
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      ) : tab === "orders" ? (
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-800">
                <th className="text-left p-3 text-neutral-500 dark:text-neutral-400">ID</th>
                <th className="text-left p-3 text-neutral-500 dark:text-neutral-400">Ticker</th>
                <th className="text-left p-3 text-neutral-500 dark:text-neutral-400">Side</th>
                <th className="text-right p-3 text-neutral-500 dark:text-neutral-400">Price</th>
                <th className="text-right p-3 text-neutral-500 dark:text-neutral-400">Qty</th>
                <th className="text-right p-3 text-neutral-500 dark:text-neutral-400">Filled</th>
                <th className="text-left p-3 text-neutral-500 dark:text-neutral-400">Status</th>
                <th className="text-right p-3 text-neutral-500 dark:text-neutral-400">Time</th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-3 text-neutral-400 dark:text-neutral-500 text-center">
                    No orders yet
                  </td>
                </tr>
              ) : (
                orders.map((o) => (
                  <tr key={o.order_id} className="border-b border-neutral-200/50 dark:border-neutral-800/50">
                    <td className="p-3 font-mono text-neutral-500 dark:text-neutral-400">{o.order_id.slice(0, 8)}</td>
                    <td className="p-3 font-semibold text-neutral-900 dark:text-white">{o.ticker}</td>
                    <td className={`p-3 font-semibold ${o.side === "buy" ? "text-green-400" : "text-red-400"}`}>
                      {o.side.toUpperCase()}
                    </td>
                    <td className="p-3 text-right font-mono">${o.price.toFixed(2)}</td>
                    <td className="p-3 text-right font-mono">{o.quantity}</td>
                    <td className="p-3 text-right font-mono">{o.filled_quantity}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColors[o.status] ?? "text-neutral-400"}`}>
                        {o.status}
                      </span>
                    </td>
                    <td className="p-3 text-right text-neutral-500 dark:text-neutral-400 text-xs">
                      {new Date(o.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-200 dark:border-neutral-800">
                <th className="text-left p-3 text-neutral-500 dark:text-neutral-400">ID</th>
                <th className="text-left p-3 text-neutral-500 dark:text-neutral-400">Ticker</th>
                <th className="text-left p-3 text-neutral-500 dark:text-neutral-400">Side</th>
                <th className="text-right p-3 text-neutral-500 dark:text-neutral-400">Price</th>
                <th className="text-right p-3 text-neutral-500 dark:text-neutral-400">Qty</th>
                <th className="text-right p-3 text-neutral-500 dark:text-neutral-400">Time</th>
              </tr>
            </thead>
            <tbody>
              {trades.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-3 text-neutral-400 dark:text-neutral-500 text-center">
                    No trades yet
                  </td>
                </tr>
              ) : (
                trades.map((t) => (
                  <tr key={t.trade_id} className="border-b border-neutral-200/50 dark:border-neutral-800/50">
                    <td className="p-3 font-mono text-neutral-500 dark:text-neutral-400">{t.trade_id.slice(0, 8)}</td>
                    <td className="p-3 font-semibold text-neutral-900 dark:text-white">{t.ticker}</td>
                    <td className={`p-3 font-semibold ${t.side === "buy" ? "text-green-400" : "text-red-400"}`}>
                      {t.side.toUpperCase()}
                    </td>
                    <td className="p-3 text-right font-mono">${t.price.toFixed(2)}</td>
                    <td className="p-3 text-right font-mono">{t.quantity}</td>
                    <td className="p-3 text-right text-neutral-500 dark:text-neutral-400 text-xs">
                      {new Date(t.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      <div className="flex justify-center gap-4 mt-4">
        <button
          onClick={() => setPage((p) => Math.max(0, p - 1))}
          disabled={page === 0}
          className="px-4 py-2 rounded text-sm bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          Previous
        </button>
        <span className="text-sm text-neutral-500 dark:text-neutral-400 self-center">Page {page + 1}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          disabled={tab === "orders" ? orders.length < PAGE_SIZE : trades.length < PAGE_SIZE}
          className="px-4 py-2 rounded text-sm bg-neutral-100 dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          Next
        </button>
      </div>
    </div>
  );
}
