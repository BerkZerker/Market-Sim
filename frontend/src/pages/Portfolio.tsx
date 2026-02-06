import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getPortfolio } from "../api/client";
import Spinner from "../components/Spinner";
import { useStore } from "../stores/useStore";

export default function Portfolio() {
  const { username, cash, holdings, totalValue } = useStore((s) => s.user);
  const setPortfolio = useStore((s) => s.setPortfolio);
  const addNotification = useStore((s) => s.addNotification);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!username) {
      navigate("/login");
      return;
    }
    getPortfolio()
      .then((data) => {
        setPortfolio(data.cash, data.holdings, data.total_value);
        setLoading(false);
      })
      .catch((err) => {
        addNotification(err.message || "Failed to load portfolio", "error");
        setLoading(false);
      });
  }, [username, navigate, setPortfolio, addNotification]);

  if (!username) return null;
  if (loading)
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Portfolio</h1>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-4">
          <p className="text-sm text-neutral-500 dark:text-neutral-400">Cash</p>
          <p className="text-xl font-mono text-neutral-900 dark:text-white">${cash.toFixed(2)}</p>
        </div>
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-4">
          <p className="text-sm text-neutral-500 dark:text-neutral-400">Holdings Value</p>
          <p className="text-xl font-mono text-neutral-900 dark:text-white">
            ${(totalValue - cash).toFixed(2)}
          </p>
        </div>
        <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-4">
          <p className="text-sm text-neutral-500 dark:text-neutral-400">Total Value</p>
          <p className="text-xl font-mono text-green-400">
            ${totalValue.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-200 dark:border-neutral-800">
              <th className="text-left p-3 text-neutral-500 dark:text-neutral-400">Ticker</th>
              <th className="text-right p-3 text-neutral-500 dark:text-neutral-400">Quantity</th>
              <th className="text-right p-3 text-neutral-500 dark:text-neutral-400">Price</th>
              <th className="text-right p-3 text-neutral-500 dark:text-neutral-400">Value</th>
            </tr>
          </thead>
          <tbody>
            {holdings.length === 0 ? (
              <tr>
                <td colSpan={4} className="p-3 text-neutral-400 dark:text-neutral-500 text-center">
                  No holdings yet
                </td>
              </tr>
            ) : (
              holdings.map((h) => (
                <tr key={h.ticker} className="border-b border-neutral-200/50 dark:border-neutral-800/50">
                  <td className="p-3 font-semibold text-neutral-900 dark:text-white">{h.ticker}</td>
                  <td className="p-3 text-right font-mono">{h.quantity}</td>
                  <td className="p-3 text-right font-mono">
                    ${h.current_price.toFixed(2)}
                  </td>
                  <td className="p-3 text-right font-mono text-green-400">
                    ${h.value.toFixed(2)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
