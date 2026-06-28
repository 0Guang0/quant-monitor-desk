# Integration Audit — R3H-03（Plan 5d）

> doubt-driven-development · 2026-06-28

## CLAIM → DOUBT → RECONCILE

| CLAIM | DOUBT | RECONCILE |
| ----- | ----- | --------- |
| 十源可一卡闭合 | 工期/并行 registry | 垂直切片 + coordinator §9.8；replay-first |
| staged pilot 可删 | 3G 测试仍引用 | L2 迁出后 thin delegate；测迁移后删除 |
| tdx_pytdx 已够 | mootdx 重复 | 独立 port；共享 normalizer 片段 |
| Layer 可跳过 | 活卡 §6 要求 | §9.9 smoke only；非 R3H-05 |
| G2/G17 本卡不做 | DH WARNING 持续 | **OPEN** — 须用户确认 R3H-05 交接 vs 本卡最小 profile |

## 六类检查

| 类 | 状态 | 备注 |
| -- | ---- | ---- |
| scope | PASS | 十源对齐 manifest；未扩 R3H-04 |
| contract | PASS | spec→test 表完整 |
| test | PASS | §1 RED/GREEN 每步有命令 |
| doc-gap | PASS_WITH_GAP | G2/G17 交接未决 |
| adversarial | PASS | QMT/akshare/silent primary 负例已规划 |
| closure | PASS | 9.10 merge gate |

## doc-gap

- **G2/G17 交易日历**：frozen §8 写「最小 profile 或 R3H-05 交接」— **须 Grill-me 用户确认**（Q12）。
- **cninfo live PDF 范围**：**须 Grill-me 用户确认**（Q13）。
- **ADR 候选 mootdx/qmt_xqshare**：**须 Grill-me 用户确认**（Q8）。

## 结论

**PASS_WITH_GAPS** — 可冻结 Plan；Execute 前用户须闭合 Q8/Q12/Q13 或接受 Plan 默认。

**Phase 5d complete**
