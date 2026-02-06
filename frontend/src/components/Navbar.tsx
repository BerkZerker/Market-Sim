import { Link, useNavigate } from "react-router-dom";
import { useStore } from "../stores/useStore";

export default function Navbar() {
  const { username } = useStore((s) => s.user);
  const logout = useStore((s) => s.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-lg font-bold text-white">
            Market Sim
          </Link>
          <Link
            to="/"
            className="text-sm text-gray-400 hover:text-white transition"
          >
            Dashboard
          </Link>
          <Link
            to="/leaderboard"
            className="text-sm text-gray-400 hover:text-white transition"
          >
            Leaderboard
          </Link>
          {username && (
            <Link
              to="/portfolio"
              className="text-sm text-gray-400 hover:text-white transition"
            >
              Portfolio
            </Link>
          )}
        </div>
        <div className="flex items-center gap-4">
          {username ? (
            <>
              <span className="text-sm text-gray-400">{username}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-400 hover:text-white transition"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm text-gray-400 hover:text-white transition"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-500 transition"
              >
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
