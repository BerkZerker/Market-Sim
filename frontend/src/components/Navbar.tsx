import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useTheme } from "../hooks/useTheme";
import { useStore } from "../stores/useStore";

export default function Navbar() {
  const { username } = useStore((s) => s.user);
  const wsConnected = useStore((s) => s.wsConnected);
  const logout = useStore((s) => s.logout);
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const handleLogout = () => {
    logout();
    setMenuOpen(false);
    navigate("/");
  };

  const isActive = (path: string) => location.pathname === path;

  const linkClass = (path: string) =>
    `text-sm transition ${
      isActive(path) ? "text-neutral-900 dark:text-white font-semibold" : "text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white"
    }`;

  return (
    <nav className="bg-neutral-50 dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-lg font-bold text-neutral-900 dark:text-white">
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
              <>
                <Link to="/portfolio" className={linkClass("/portfolio")}>
                  Portfolio
                </Link>
                <Link to="/history" className={linkClass("/history")}>
                  History
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Desktop auth + theme toggle */}
        <div className="hidden md:flex items-center gap-4">
          <button
            onClick={toggleTheme}
            className="text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition"
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
          {username ? (
            <>
              <span className="text-sm text-neutral-500 dark:text-neutral-400">{username}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition"
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
        <div className="flex md:hidden items-center gap-3">
          <button
            onClick={toggleTheme}
            className="text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition"
          >
            {theme === "dark" ? (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
          <button
            className="text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white"
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
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="md:hidden border-t border-neutral-200 dark:border-neutral-800 px-4 py-3 flex flex-col gap-3">
          <Link to="/" className={linkClass("/")} onClick={() => setMenuOpen(false)}>
            Dashboard
          </Link>
          <Link to="/leaderboard" className={linkClass("/leaderboard")} onClick={() => setMenuOpen(false)}>
            Leaderboard
          </Link>
          {username && (
            <>
              <Link to="/portfolio" className={linkClass("/portfolio")} onClick={() => setMenuOpen(false)}>
                Portfolio
              </Link>
              <Link to="/history" className={linkClass("/history")} onClick={() => setMenuOpen(false)}>
                History
              </Link>
            </>
          )}
          <hr className="border-neutral-200 dark:border-neutral-800" />
          {username ? (
            <>
              <span className="text-sm text-neutral-500 dark:text-neutral-400">{username}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-neutral-500 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-white transition text-left"
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
