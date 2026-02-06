import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register } from "../api/client";
import { useStore } from "../stores/useStore";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const setUser = useStore((s) => s.setUser);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      const data = await register(username, password);
      setUser({
        userId: data.user_id,
        username: data.username,
        jwtToken: data.jwt_token,
        apiKey: data.api_key,
        cash: data.cash,
      });
      setApiKey(data.api_key);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  };

  const copyApiKey = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (apiKey) {
    return (
      <div className="max-w-md mx-auto">
        <h1 className="text-2xl font-bold mb-6">Registration Successful</h1>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 space-y-4">
          <p className="text-sm text-gray-400">
            Save your API key. You'll need it to connect AI agents.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 bg-gray-800 px-3 py-2 rounded text-sm font-mono text-green-400 break-all">
              {apiKey}
            </code>
            <button
              onClick={copyApiKey}
              className="bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded text-sm transition"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
          <button
            onClick={() => navigate("/")}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2 rounded font-semibold transition"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-6">Register</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
          required
          minLength={2}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2"
          required
          minLength={4}
        />
        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2 rounded font-semibold transition"
        >
          Register
        </button>
        {error && <p className="text-red-400 text-sm">{error}</p>}
      </form>
    </div>
  );
}
