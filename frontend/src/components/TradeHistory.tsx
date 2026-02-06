interface Trade {
  price: number;
  quantity: number;
  timestamp: number;
}

interface TradeHistoryProps {
  trades: Trade[];
}

export default function TradeHistory({ trades }: TradeHistoryProps) {
  return (
    <div className="space-y-0.5 max-h-64 overflow-y-auto">
      {trades.length === 0 && (
        <p className="text-neutral-400 dark:text-neutral-500 text-sm">No trades yet</p>
      )}
      {trades.map((trade, i) => (
        <div key={i} className="flex justify-between text-sm py-0.5 px-2">
          <span className="text-neutral-700 dark:text-neutral-300 font-mono">
            ${trade.price.toFixed(2)}
          </span>
          <span className="text-neutral-500 dark:text-neutral-400 font-mono">{trade.quantity}</span>
          <span className="text-neutral-400 dark:text-neutral-500 text-xs">
            {new Date(trade.timestamp * 1000).toLocaleTimeString()}
          </span>
        </div>
      ))}
    </div>
  );
}
