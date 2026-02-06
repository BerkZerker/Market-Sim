import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";
import ErrorBoundary from "./components/ErrorBoundary";
import Navbar from "./components/Navbar";
import ToastContainer from "./components/Toast";
import Dashboard from "./pages/Dashboard";
import Leaderboard from "./pages/Leaderboard";
import Login from "./pages/Login";
import Portfolio from "./pages/Portfolio";
import Register from "./pages/Register";
import Ticker from "./pages/Ticker";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 py-6">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/ticker/:symbol" element={<Ticker />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/leaderboard" element={<Leaderboard />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
            </Routes>
          </ErrorBoundary>
        </main>
        <ToastContainer />
      </div>
    </BrowserRouter>
  </React.StrictMode>,
);
