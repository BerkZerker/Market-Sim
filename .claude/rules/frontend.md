---
globs:
  - "frontend/**"
---

# Frontend Rules

- Vite dev server proxies `/api` → `http://localhost:8000` and `/ws` → `ws://localhost:8000` (see `vite.config.ts`).
- State management: Zustand store in `stores/useStore.ts`. Auth state persists to localStorage.
- API client: `api/client.ts` — all fetch calls go through here. Uses JWT from store.
- WebSocket client: `api/ws.ts` — channel-based. Auto-reconnects after 3s on disconnect.
- Pages use WebSocket subscriptions for real-time updates (prices, trades, order book).
- Tailwind for styling — no CSS modules or styled-components.
- React Router v6 with routes defined in `main.tsx`.
- Build: `npm run dev` (dev server) or `npm run build` (production).
