import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import Spinner from "../Spinner";

describe("Spinner", () => {
  it("renders an SVG element", () => {
    const { container } = render(<Spinner />);
    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
  });

  it("applies size classes", () => {
    const { container: lg } = render(<Spinner size="lg" />);
    expect(lg.querySelector("svg")).toHaveClass("h-12", "w-12");

    const { container: sm } = render(<Spinner size="sm" />);
    expect(sm.querySelector("svg")).toHaveClass("h-4", "w-4");
  });
});
