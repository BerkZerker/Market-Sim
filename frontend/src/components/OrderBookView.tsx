interface Level {
  price: number;
  quantity: number;
}

interface OrderBookViewProps {
  bids: Level[];
  asks: Level[];
}

export default function OrderBookView({ bids, asks }: OrderBookViewProps) {
  const maxQty = Math.max(
    ...bids.map((b) => b.quantity),
    ...asks.map((a) => a.quantity),
    1,
  );

  const bestBid = bids.length > 0 ? bids[0].price : null;
  const bestAsk = asks.length > 0 ? asks[0].price : null;

  return (
    <div>
      <div className="grid grid-cols-2 gap-4">
        {/* Bids */}
        <div>
          <h4 className="text-sm font-semibold text-green-400 mb-2">Bids</h4>
          <div className="space-y-0.5">
            {bids.slice(0, 15).map((level, i) => (
              <div key={i} className="relative flex justify-between text-sm py-0.5 px-2">
                <div
                  className="absolute inset-0 bg-green-900/30"
                  style={{ width: `${(level.quantity / maxQty) * 100}%` }}
                />
                <span className="relative text-green-400 font-mono">
                  ${level.price.toFixed(2)}
                </span>
                <span className="relative text-neutral-700 dark:text-neutral-300 font-mono">
                  {level.quantity}
                </span>
              </div>
            ))}
            {bids.length === 0 && (
              <p className="text-neutral-400 dark:text-neutral-500 text-sm">No bids</p>
            )}
          </div>
        </div>

        {/* Asks */}
        <div>
          <h4 className="text-sm font-semibold text-red-400 mb-2">Asks</h4>
          <div className="space-y-0.5">
            {asks.slice(0, 15).map((level, i) => (
              <div key={i} className="relative flex justify-between text-sm py-0.5 px-2">
                <div
                  className="absolute inset-0 bg-red-900/30 right-0 left-auto"
                  style={{ width: `${(level.quantity / maxQty) * 100}%` }}
                />
                <span className="relative text-red-400 font-mono">
                  ${level.price.toFixed(2)}
                </span>
                <span className="relative text-neutral-700 dark:text-neutral-300 font-mono">
                  {level.quantity}
                </span>
              </div>
            ))}
            {asks.length === 0 && (
              <p className="text-neutral-400 dark:text-neutral-500 text-sm">No asks</p>
            )}
          </div>
        </div>
      </div>

      {/* Spread info bar */}
      {bestBid !== null && bestAsk !== null && (
        <div className="mt-3 flex items-center justify-center gap-6 text-xs font-mono py-2 border-t border-neutral-200 dark:border-neutral-800">
          <span className="text-neutral-500 dark:text-neutral-400">
            Spread <span className="text-yellow-500 dark:text-yellow-400">${(bestAsk - bestBid).toFixed(2)}</span>
          </span>
          <span className="text-neutral-500 dark:text-neutral-400">
            Spread % <span className="text-yellow-500 dark:text-yellow-400">{(((bestAsk - bestBid) / ((bestBid + bestAsk) / 2)) * 100).toFixed(2)}%</span>
          </span>
          <span className="text-neutral-500 dark:text-neutral-400">
            Mid <span className="text-neutral-900 dark:text-white">${((bestBid + bestAsk) / 2).toFixed(2)}</span>
          </span>
        </div>
      )}
    </div>
  );
}
