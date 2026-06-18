import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App scaffold", () => {
  it("renders product name and five-layer summary", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Quant Monitor Desk" })).toBeTruthy();
    expect(screen.getByText(/Five layers:/)).toBeTruthy();
    expect(screen.getByText(/Regime/)).toBeTruthy();
  });
});
