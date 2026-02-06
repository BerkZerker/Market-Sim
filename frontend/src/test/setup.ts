import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

afterEach(() => {
  cleanup();
  localStorage.clear();
});

// Mock lightweight-charts (uses Canvas APIs unavailable in jsdom)
vi.mock("lightweight-charts", () => ({
  createChart: () => ({
    addSeries: () => ({
      setData: vi.fn(),
      update: vi.fn(),
    }),
    applyOptions: vi.fn(),
    timeScale: () => ({ fitContent: vi.fn() }),
    remove: vi.fn(),
  }),
  CandlestickSeries: {},
}));

// Mock ResizeObserver
class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
vi.stubGlobal("ResizeObserver", MockResizeObserver);
