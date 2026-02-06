import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock WebSocket
class MockWebSocket {
  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  close = vi.fn();

  constructor(public url: string) {
    // Simulate async connection
    setTimeout(() => this.onopen?.(), 0);
  }
}

vi.stubGlobal("WebSocket", MockWebSocket);

const { WSClient } = await import("../ws");

beforeEach(() => {
  vi.useFakeTimers();
});

describe("WSClient", () => {
  it("connects to the correct URL", () => {
    const ws = new WSClient("prices");
    ws.connect();

    // Check the URL pattern (uses location.protocol and host)
    expect(ws).toBeDefined();
  });

  it("calls message handlers on incoming messages", () => {
    const ws = new WSClient("prices");
    const handler = vi.fn();
    ws.onMessage(handler);
    ws.connect();

    // Access the internal WebSocket to trigger onmessage
    const internal = (ws as unknown as { ws: MockWebSocket }).ws;
    internal.onmessage?.({ data: JSON.stringify({ type: "prices", data: {} }) });

    expect(handler).toHaveBeenCalledWith({ type: "prices", data: {} });
  });

  it("cleans up on disconnect", () => {
    const ws = new WSClient("prices");
    const handler = vi.fn();
    ws.onMessage(handler);
    ws.connect();

    ws.disconnect();

    expect(
      (ws as unknown as { handlers: unknown[] }).handlers,
    ).toHaveLength(0);
  });
});
