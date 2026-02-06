import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useStore } from "../stores/useStore";

export default function Navbar() {
  const { username } = useStore((s) => s.user);
  const wsConnected = useStore((s) => s.wsConnected);
  const logout = useStore((s) => s.logout);
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    setMenuOpen(false);
    navigate("/");
  };

  const isActive = (path: string) => location.pathname === path;

  const linkClass = (path: string) =>
    `text-sm transition ${
      isActive(path) ? "text-white font-semibold" : "text-gray-400 hover:text-white"
    }`;

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-lg font-bold text-white">
            Market Sim
          </Link>
          <span
            className={`h-2 w-2 rounded-full ${
              wsConnected ? "bg-green-400" : "bg-red-400 animate-pulse"
            }`}
            title={wsConnected ? "Connected" : "Disconnected"}
          />
          <div className="hidden md:flex items-center gap-6 ml-3">
            <Link to="/" className={linkClass("/")}>
              Dashboard
            </Link>
            <Link to="/leaderboard" className={linkClass("/leaderboard")}>
              Leaderboard
            </Link>
            {username && (
              <Link to="/portfolio" className={linkClass("/portfolio")}>
                Portfolio
              </Link>
            )}
          </div>
        </div>

        {/* Desktop auth */}
        <div className="hidden md:flex items-center gap-4">
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
              <Link to="/login" className={linkClass("/login")}>
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

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-gray-400 hover:text-white"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="md:hidden border-t border-gray-800 px-4 py-3 flex flex-col gap-3">
          <Link to="/" className={linkClass("/")} onClick={() => setMenuOpen(false)}>
            Dashboard
          </Link>
          <Link to="/leaderboard" className={linkClass("/leaderboard")} onClick={() => setMenuOpen(false)}>
            Leaderboard
          </Link>
          {username && (
            <Link to="/portfolio" className={linkClass("/portfolio")} onClick={() => setMenuOpen(false)}>
              Portfolio
            </Link>
          )}
          <hr className="border-gray-800" />
          {username ? (
            <>
              <span className="text-sm text-gray-400">{username}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-gray-400 hover:text-white transition text-left"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className={linkClass("/login")} onClick={() => setMenuOpen(false)}>
                Login
              </Link>
              <Link to="/register" className={linkClass("/register")} onClick={() => setMenuOpen(false)}>
                Register
              </Link>
            </>
          )}
        </div>
      )}
    </nav>
  );
}
