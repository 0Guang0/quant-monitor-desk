# PRD — B01-023 full Layer5 evidence chain

## Problem

Layer2–4 已有 staged snapshot 与 023A evidence identity，但缺少可审计的 **full evidence chain**：无法把 bar/event/financial/valuation 证据与 Layer3/4 上游快照串成「为什么这么判断」的结构化链路。

## Users

- 下游 Batch 5+ 建模与 Round4 review/backtest
- 主会话 merge coordinator（Track B 验收）

## Success criteria

1. `instrument_registry` + evidence models 可 staged 校验
2. `evidence_chain_builder` 产出含 ≥1 层结构化 context + upstream snapshot ids
3. Agent 文本不能成为事实源（回归 023A + chain 测试）
4. `R3-PARTIAL-4` 有 ADR + pytest
5. 不声称 production-live；Track B 独立 merge

## Non-goals

- Live source / production DB write
- 全市场全历史 bar 回填
- 完整人工审核 UI
- Registry 三件套闭合（主会话）
