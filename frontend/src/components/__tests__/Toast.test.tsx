import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useStore } from "../../stores/useStore";
import { resetStore } from "../../test/mocks";
import ToastContainer from "../Toast";

beforeEach(() => {
  vi.useFakeTimers();
  resetStore();
});

describe("ToastContainer", () => {
  it("returns null when there are no notifications", () => {
    const { container } = render(<ToastContainer />);
    expect(container.innerHTML).toBe("");
  });

  it("renders notifications with dismiss button", () => {
    vi.useRealTimers();
    useStore.setState({
      notifications: [{ id: "1", message: "Something went wrong", type: "error" }],
    });

    render(<ToastContainer />);

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("\u00d7")).toBeInTheDocument(); // × dismiss button
  });
});
