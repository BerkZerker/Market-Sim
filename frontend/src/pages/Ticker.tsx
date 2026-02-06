import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getOrderbook, getTickerInfo } from "../api/client";
import { WSClient } from "../api/ws";
import OrderBookView from "../components/OrderBookView";
import OrderForm from "../components/OrderForm";
import PriceChart from "../components/PriceChart";
import TradeHistory from "../components/TradeHistory";
import { useStore } from "../stores/useStore";

interface Trade {
  price: number;
  quantity: number;
  timestamp: number;
}

export default function Ticker() {
  const { symbol } = useParams<{ symbol: string }>();
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const orderbook = useStore((s) => s.orderbook);
  const setOrderbook = useStore((s) => s.setOrderbook);

  // Fetch initial data
  useEffect(() => {
    if (!symbol) return;
    getTickerInfo(symbol).then((data) => setCurrentPrice(data.current_price));
    getOrderbook(symbol).then((data) => setOrderbook(data.bids, data.asks));
  }, [symbol, setOrderbook]);

  // WebSocket for trades
  useEffect(() => {
    if (!symbol) return;
    const tradeWs = new WSClient(`trades:${symbol}`);
    tradeWs.connect();
    tradeWs.onMessage((msg: unknown) => {
      const data = msg as { type: string; price: number; quantity: number; timestamp: number };
      if (data.type === "trade") {
        setCurrentPrice(data.price);
        setTrades((prev) => [data, ...prev].slice(0, 50));
      }
    });
    return () => tradeWs.disconnect();
  }, [symbol]);

  // WebSocket for orderbook
  useEffect(() => {
    if (!symbol) return;
    const obWs = new WSClient(`orderbook:${symbol}`);
    obWs.connect();
    obWs.onMessage((msg: unknown) => {
      const data = msg as { type: string; bids: { price: number; quantity: number }[]; asks: { price: number; quantity: number }[] };
      if (data.type === "orderbook") {
        setOrderbook(data.bids, data.asks);
      }
    });
    return () => obWs.disconnect();
  }, [symbol, setOrderbook]);

  if (!symbol) return <p>No ticker selected</p>;

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold">{symbol}</h1>
        <span className="text-2xl font-mono text-neutral-900 dark:text-white">
          ${currentPrice?.toFixed(2) ?? "---"}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="lg:col-span-2 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 mb-3">
            Price Chart
          </h3>
          <PriceChart ticker={symbol} latestPrice={currentPrice ?? undefined} />
        </div>

        {/* Order form */}
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 mb-3">
            Place Order
          </h3>
          <OrderForm ticker={symbol} currentPrice={currentPrice} />
        </div>

        {/* Order book */}
        <div className="lg:col-span-2 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 mb-3">
            Order Book
          </h3>
          <OrderBookView bids={orderbook.bids} asks={orderbook.asks} />
        </div>

        {/* Recent trades */}
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 mb-3">
            Recent Trades
          </h3>
          <TradeHistory trades={trades} />
        </div>
      </div>
    </div>
  );
}
