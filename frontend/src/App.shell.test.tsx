import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App shell states", () => {
  it("renders loading-free default view with layer summary", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Quant Monitor Desk" })).toBeTruthy();
    expect(screen.getByText(/Five layers:/)).toBeTruthy();
  });

  it("exposes scaffold subtitle copy", () => {
    render(<App />);
    expect(screen.getAllByText(/Local-first quantitative monitoring/).length).toBeGreaterThan(0);
  });
});
