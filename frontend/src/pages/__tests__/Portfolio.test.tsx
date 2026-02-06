import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { resetStore } from "../../test/mocks";

vi.mock("../../api/client", () => ({
  getPortfolio: vi.fn(),
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

beforeEach(() => {
  resetStore();
  mockNavigate.mockReset();
});

describe("Portfolio", () => {
  it("redirects to login when not authenticated", async () => {
    const Portfolio = (await import("../Portfolio")).default;
    render(
      <MemoryRouter>
        <Portfolio />
      </MemoryRouter>,
    );

    expect(mockNavigate).toHaveBeenCalledWith("/login");
  });
});
