# Batch 01 零遗留闭合策略

> **生效：** 2026-06-25 · 协调者用户指令  
> **规则：** 七路分支所有 **BLOCKING** 与 **NON-BLOCKING** OPEN 项必须修复或书面 re-defer（含 owner、phase、closure test）；**禁止**以「条件可验收」「主会话稍后」留 OPEN。

## 闭合定义

| 类型             | 闭合条件                                                             |
| ---------------- | -------------------------------------------------------------------- |
| BLOCKING         | 代码/测试/证据修复 + 复验通过                                        |
| NON-BLOCKING     | 同上，或 ADR/wont-fix + registry re-defer 行 + 负向测试              |
| PROBE_REDEFERRED | 授权/依赖缺失时须：taxonomy 状态 + closure test + 不得冒充 PASS live |
| loop/catalog     | `loop_maintain --fix` + **同分支 commit** 生成物                     |
| 未 commit        | **BLOCKING** — 闭合前必须 commit 交付物                              |

## 跨分支依赖

1. **DH2-BASE** → cherry-pick/rebase 至仍红 `test_dataHealthIntegration_v2Evidence_bundle` 的分支
2. **B01-WL** → merge/rebase 后 SP3 Boot 硬停解除
3. **Registry** → 主会话 Track A/B 合并时批处理 proposed delta

## 验收

每分支 Done 前：`uv run pytest -q` 全绿 + OPEN 清单 **0 行** + closure report 九项。
