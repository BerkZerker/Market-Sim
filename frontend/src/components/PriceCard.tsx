import { Link } from "react-router-dom";

interface PriceCardProps {
  ticker: string;
  price: number | null;
  bestBid: number | null;
  bestAsk: number | null;
}

export default function PriceCard({
  ticker,
  price,
  bestBid,
  bestAsk,
}: PriceCardProps) {
  return (
    <Link
      to={`/ticker/${ticker}`}
      className="block bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-4 hover:border-neutral-400 dark:hover:border-neutral-600 transition"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-bold text-neutral-900 dark:text-white">{ticker}</h3>
        <span className="text-xl font-mono text-neutral-900 dark:text-white">
          ${price?.toFixed(2) ?? "---"}
        </span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-green-400">
          Bid: ${bestBid?.toFixed(2) ?? "---"}
        </span>
        <span className="text-red-400">
          Ask: ${bestAsk?.toFixed(2) ?? "---"}
        </span>
      </div>
    </Link>
  );
}
