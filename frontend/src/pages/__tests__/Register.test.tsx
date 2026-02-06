import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { resetStore } from "../../test/mocks";

vi.mock("../../api/client", () => ({
  register: vi.fn(),
}));

beforeEach(() => {
  resetStore();
});

describe("Register", () => {
  it("renders the registration form", async () => {
    const Register = (await import("../Register")).default;
    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    );

    expect(screen.getByPlaceholderText("Username")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Register" })).toBeInTheDocument();
  });

  it("shows API key on successful registration", async () => {
    const { register } = await import("../../api/client");
    vi.mocked(register).mockResolvedValue({
      user_id: "u1",
      username: "alice",
      api_key: "secret-api-key-123",
      jwt_token: "jwt",
      cash: 10000,
    });

    const Register = (await import("../Register")).default;
    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByPlaceholderText("Username"), "alice");
    await userEvent.type(screen.getByPlaceholderText("Password"), "password");
    await userEvent.click(screen.getByRole("button", { name: "Register" }));

    await waitFor(() => {
      expect(screen.getByText("Registration Successful")).toBeInTheDocument();
      expect(screen.getByText("secret-api-key-123")).toBeInTheDocument();
    });
  });
});
