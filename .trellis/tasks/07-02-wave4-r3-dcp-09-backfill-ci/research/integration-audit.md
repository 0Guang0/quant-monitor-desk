# Integration Audit — R3-DCP-09（Plan 5d · Repair reconcile）

## CLAIM → DOUBT → RECONCILE

| CLAIM                     | DOUBT                    | RECONCILE                              |
| ------------------------- | ------------------------ | -------------------------------------- |
| 需新 FullLoad 路径        | Batch 6 显式 non-goal    | 仅 backfill cap；不碰 FullLoadJob      |
| nightly 跑全量 pytest     | ~200s+ flake             | isolated `--quick` + network 子集      |
| CLI 支持全 Tier A backfill| 矩阵过大                 | pilot 单域；registry 扩展留 Batch 6    |
| 参考树缺失可跳过 L 梯     | guardrails 禁止          | 登记路径；Execute 实读或 block         |

## 六类检查（Execute 后）

| 类   | 状态 | 备注 |
| ---- | ---- | ---- |
| 契约 | PASS | `bounded_backfill_cap.yaml` + runtime SSOT @ `jobs.py` |
| 测试 | PASS | CLI/e2e/nightly manifest + registry 测 |
| 安全 | PASS | fail-closed · 隔离库 · no bypass |
| 架构 | PASS | 金路径不变 |
| 文档 | PASS | `nightly_ci.md` + ADR-030 |
| 运维 | PASS | workflow + ops 双轨 |

## adversarial

| 检查项                    | 结果 |
| ------------------------- | ---- |
| plan-doubt-review D1–D5   | PASS |
| 仓内代码未误入 L 梯       | PASS |
| 台账四 ID 切片绑定        | PASS |

## doc-gap

**CLOSED @ Execute S00–S06** — 原 GAP 行（`qmd data backfill` / nightly workflow / 台账）已由实现与测试闭合。

**Phase 5d + Repair · PASS**
