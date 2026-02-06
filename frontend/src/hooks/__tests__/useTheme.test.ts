import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useTheme } from "../useTheme";

afterEach(() => {
  document.documentElement.classList.remove("dark");
  localStorage.removeItem("theme");
});

describe("useTheme", () => {
  it("defaults to light and toggles to dark", async () => {
    document.documentElement.classList.remove("dark");

    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("light");

    act(() => {
      result.current.toggleTheme();
    });

    // MutationObserver fires asynchronously — wait for it
    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
    });

    expect(result.current.theme).toBe("dark");
    expect(localStorage.getItem("theme")).toBe("dark");
  });
});
