import { useState } from "react";
import { placeOrder } from "../api/client";
import { useStore } from "../stores/useStore";

interface OrderFormProps {
  ticker: string;
  currentPrice: number | null;
}

export default function OrderForm({ ticker, currentPrice }: OrderFormProps) {
  const { username } = useStore((s) => s.user);
  const [side, setSide] = useState<"buy" | "sell">("buy");
  const [price, setPrice] = useState(currentPrice?.toFixed(2) ?? "");
  const [quantity, setQuantity] = useState("10");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!username) {
    return (
      <div className="text-neutral-400 dark:text-neutral-500 text-sm">Log in to place orders</div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setStatus(null);

    try {
      const result = await placeOrder(
        ticker,
        side,
        parseFloat(price),
        parseInt(quantity),
      );
      setStatus(
        `Order ${result.status}: ${result.filled_quantity}/${result.quantity} filled`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Order failed");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setSide("buy")}
          className={`flex-1 py-1.5 rounded text-sm font-semibold transition ${
            side === "buy"
              ? "bg-green-600 text-white"
              : "bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400"
          }`}
        >
          Buy
        </button>
        <button
          type="button"
          onClick={() => setSide("sell")}
          className={`flex-1 py-1.5 rounded text-sm font-semibold transition ${
            side === "sell"
              ? "bg-red-600 text-white"
              : "bg-neutral-100 dark:bg-neutral-800 text-neutral-500 dark:text-neutral-400"
          }`}
        >
          Sell
        </button>
      </div>
      <input
        type="number"
        step="0.01"
        placeholder="Price"
        value={price}
        onChange={(e) => setPrice(e.target.value)}
        className="w-full bg-neutral-100 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded px-3 py-2 text-sm"
      />
      <input
        type="number"
        step="1"
        min="1"
        placeholder="Quantity"
        value={quantity}
        onChange={(e) => setQuantity(e.target.value)}
        className="w-full bg-neutral-100 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-700 rounded px-3 py-2 text-sm"
      />
      <button
        type="submit"
        className={`w-full py-2 rounded text-sm font-semibold transition ${
          side === "buy"
            ? "bg-green-600 hover:bg-green-500 text-white"
            : "bg-red-600 hover:bg-red-500 text-white"
        }`}
      >
        Place {side === "buy" ? "Buy" : "Sell"} Order
      </button>
      {status && <p className="text-green-400 text-sm">{status}</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}
    </form>
  );
}
