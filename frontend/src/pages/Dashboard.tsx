import { useEffect } from "react";
import { getTickers } from "../api/client";
import { WSClient } from "../api/ws";
import PriceCard from "../components/PriceCard";
import { useStore } from "../stores/useStore";

export default function Dashboard() {
  const prices = useStore((s) => s.market.prices);
  const setPrices = useStore((s) => s.setPrices);
  const addPricePoint = useStore((s) => s.addPricePoint);

  // Initial fetch
  useEffect(() => {
    getTickers().then((data) => setPrices(data.tickers));
  }, [setPrices]);

  // WebSocket for live prices
  useEffect(() => {
    const ws = new WSClient("prices");
    ws.connect();
    ws.onMessage((msg: unknown) => {
      const data = msg as { type: string; data: Record<string, { current_price: number | null; best_bid: number | null; best_ask: number | null }> };
      if (data.type === "prices") {
        setPrices(data.data);
        for (const [ticker, info] of Object.entries(data.data)) {
          if (info.current_price != null) {
            addPricePoint(ticker, info.current_price);
          }
        }
      }
    });
    return () => ws.disconnect();
  }, [setPrices, addPricePoint]);

  const tickers = Object.entries(prices);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Market Dashboard</h1>
      {tickers.length === 0 ? (
        <p className="text-gray-500">Loading tickers...</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {tickers.map(([ticker, info]) => (
            <PriceCard
              key={ticker}
              ticker={ticker}
              price={info.current_price}
              bestBid={info.best_bid}
              bestAsk={info.best_ask}
            />
          ))}
        </div>
      )}
    </div>
  );
}
