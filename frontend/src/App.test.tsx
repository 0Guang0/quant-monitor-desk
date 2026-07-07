import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App scaffold", () => {
  it("renders product name and five-layer summary", () => {
    /* 覆盖范围：默认 dashboard shell 首屏
     * 测试对象：App
     * 目的/目标：占位 UI 至少暴露产品名和五层摘要，避免空白 shell
     * 验证点：heading=Quant Monitor Desk；正文含 Five layers 与 Regime
     * 失败含义：前端入口渲染为空或丢失核心产品上下文
     */
    render(<App />);
    expect(
      screen.getByRole("heading", { name: "Quant Monitor Desk" })
    ).toBeTruthy();
    expect(screen.getByText(/Five layers:/)).toBeTruthy();
    expect(screen.getByText(/Regime/)).toBeTruthy();
  });
});
