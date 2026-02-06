import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { resetStore, setLoggedInUser } from "../../test/mocks";
import Navbar from "../Navbar";

beforeEach(() => {
  resetStore();
});

function renderNavbar() {
  return render(
    <MemoryRouter>
      <Navbar />
    </MemoryRouter>,
  );
}

describe("Navbar", () => {
  it("shows Login and Register when logged out", () => {
    renderNavbar();
    expect(screen.getByText("Login")).toBeInTheDocument();
    expect(screen.getByText("Register")).toBeInTheDocument();
  });

  it("shows Logout, Portfolio, and History when logged in", () => {
    setLoggedInUser();
    renderNavbar();
    expect(screen.getAllByText("Logout")).toHaveLength(1);
    expect(screen.getAllByText("Portfolio")).toHaveLength(1);
    expect(screen.getAllByText("History")).toHaveLength(1);
  });

  it("displays the username when logged in", () => {
    setLoggedInUser("alice");
    renderNavbar();
    expect(screen.getAllByText("alice").length).toBeGreaterThan(0);
  });
});
