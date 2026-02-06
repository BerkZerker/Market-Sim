#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "Shutting down..."
    [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null
    [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null
    wait 2>/dev/null
    echo "Done."
}
trap cleanup EXIT INT TERM

# --- Check prerequisites ---
if ! command -v uv &>/dev/null; then
    echo "Error: uv is not installed. Install it from https://github.com/astral-sh/uv"
    exit 1
fi

if ! command -v node &>/dev/null; then
    echo "Error: Node.js is not installed. Install Node.js 18+."
    exit 1
fi

# --- Install dependencies ---
echo "==> Installing backend dependencies..."
uv sync --project "$PROJECT_DIR"

echo "==> Installing frontend dependencies..."
npm install --prefix "$PROJECT_DIR/frontend"

# --- Start backend ---
echo "==> Starting backend on http://localhost:8000 ..."
uv run --project "$PROJECT_DIR" python "$PROJECT_DIR/backend/main.py" &
BACKEND_PID=$!

# Wait for backend to be ready
echo -n "    Waiting for backend"
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/api/health &>/dev/null; then
        echo " ready!"
        break
    fi
    echo -n "."
    sleep 1
    if [[ $i -eq 30 ]]; then
        echo " timed out!"
        echo "Error: Backend failed to start within 30 seconds."
        exit 1
    fi
done

# --- Start frontend ---
echo "==> Starting frontend on http://localhost:5173 ..."
npm run dev --prefix "$PROJECT_DIR/frontend" &
FRONTEND_PID=$!

# Wait for frontend to be ready, then open browser
echo -n "    Waiting for frontend"
for i in $(seq 1 30); do
    if curl -sf http://localhost:5173 &>/dev/null; then
        echo " ready!"
        if command -v xdg-open &>/dev/null; then
            xdg-open http://localhost:5173
        elif command -v open &>/dev/null; then
            open http://localhost:5173
        fi
        break
    fi
    echo -n "."
    sleep 1
    if [[ $i -eq 30 ]]; then
        echo " timed out!"
    fi
done

echo ""
echo "========================================"
echo "  Market-Sim is running!"
echo "  Backend:   http://localhost:8000"
echo "  Frontend:  http://localhost:5173"
echo "  API docs:  http://localhost:8000/docs"
echo "  Press Ctrl+C to stop."
echo "========================================"

wait
