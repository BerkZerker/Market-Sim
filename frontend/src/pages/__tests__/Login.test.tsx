import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { resetStore } from "../../test/mocks";

vi.mock("../../api/client", () => ({
  login: vi.fn(),
}));

beforeEach(() => {
  resetStore();
});

describe("Login", () => {
  it("renders the login form", async () => {
    const Login = (await import("../Login")).default;
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    expect(screen.getByPlaceholderText("Username")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Login" })).toBeInTheDocument();
  });

  it("shows error on login failure", async () => {
    const { login } = await import("../../api/client");
    vi.mocked(login).mockRejectedValue(new Error("Invalid credentials"));

    const Login = (await import("../Login")).default;
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByPlaceholderText("Username"), "bad");
    await userEvent.type(screen.getByPlaceholderText("Password"), "pass");
    await userEvent.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });
  });
});
