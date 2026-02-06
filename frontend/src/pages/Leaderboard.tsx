import { useEffect, useState } from "react";
import { getLeaderboard } from "../api/client";

interface Entry {
  user_id: string;
  username: string;
  cash: number;
  total_value: number;
}

export default function Leaderboard() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLeaderboard = () => {
    getLeaderboard()
      .then((data) => {
        setEntries(data.leaderboard);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchLeaderboard();
    const interval = setInterval(fetchLeaderboard, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Leaderboard</h1>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : entries.length === 0 ? (
        <p className="text-gray-500">No players yet. Be the first to register!</p>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left p-3 text-gray-400">Rank</th>
                <th className="text-left p-3 text-gray-400">Player</th>
                <th className="text-right p-3 text-gray-400">Cash</th>
                <th className="text-right p-3 text-gray-400">Total Value</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, i) => (
                <tr key={entry.user_id} className="border-b border-gray-800/50">
                  <td className="p-3 text-gray-400">#{i + 1}</td>
                  <td className="p-3 font-semibold text-white">
                    {entry.username}
                  </td>
                  <td className="p-3 text-right font-mono">
                    ${entry.cash.toFixed(2)}
                  </td>
                  <td className="p-3 text-right font-mono text-green-400">
                    ${entry.total_value.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
