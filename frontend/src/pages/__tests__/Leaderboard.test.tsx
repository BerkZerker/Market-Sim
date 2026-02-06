import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { resetStore } from "../../test/mocks";

vi.mock("../../api/client", () => ({
  getLeaderboard: vi.fn(),
}));

beforeEach(() => {
  resetStore();
});

describe("Leaderboard", () => {
  it("renders leaderboard table after loading", async () => {
    const { getLeaderboard } = await import("../../api/client");
    vi.mocked(getLeaderboard).mockResolvedValue({
      leaderboard: [
        { user_id: "u1", username: "alice", cash: 9000, holdings: [], total_value: 11000 },
        { user_id: "u2", username: "bob", cash: 8000, holdings: [], total_value: 10500 },
      ],
    });

    const Leaderboard = (await import("../Leaderboard")).default;
    render(<Leaderboard />);

    await waitFor(() => {
      expect(screen.getByText("alice")).toBeInTheDocument();
      expect(screen.getByText("bob")).toBeInTheDocument();
      expect(screen.getByText("$11000.00")).toBeInTheDocument();
    });
  });
});
