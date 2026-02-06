import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Import after stubbing fetch
const { register, getTickers, login } = await import("../client");

beforeEach(() => {
  localStorage.clear();
  mockFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("API client", () => {
  it("sends Authorization header when JWT is set", async () => {
    localStorage.setItem("jwt_token", "my-jwt");
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ tickers: {} }),
    });

    await getTickers();

    const [, options] = mockFetch.mock.calls[0];
    expect(options.headers["Authorization"]).toBe("Bearer my-jwt");
  });

  it("sends X-API-Key header when only API key is set", async () => {
    localStorage.setItem("api_key", "my-key");
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ tickers: {} }),
    });

    await getTickers();

    const [, options] = mockFetch.mock.calls[0];
    expect(options.headers["X-API-Key"]).toBe("my-key");
    expect(options.headers["Authorization"]).toBeUndefined();
  });

  it("throws on error response with detail", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      statusText: "Bad Request",
      json: () => Promise.resolve({ detail: "Username taken" }),
    });

    await expect(register("alice", "pass")).rejects.toThrow("Username taken");
  });

  it("registers a user with POST", async () => {
    const data = {
      user_id: "u1",
      username: "alice",
      api_key: "key",
      jwt_token: "jwt",
      cash: 10000,
    };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(data),
    });

    const result = await register("alice", "pass");

    expect(result).toEqual(data);
    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/register");
    expect(options.method).toBe("POST");
  });

  it("logs in a user with POST", async () => {
    const data = { user_id: "u1", username: "alice", jwt_token: "jwt" };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(data),
    });

    const result = await login("alice", "pass");

    expect(result).toEqual(data);
    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe("/api/login");
  });
});
