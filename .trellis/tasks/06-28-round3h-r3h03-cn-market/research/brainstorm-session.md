# Brainstorm — R3H-03（Plan 2a）

> trellis-brainstorm · 2026-06-28

## 方案对比

| 选项 | 描述 | 结论 |
| ---- | ---- | ---- |
| A. 单文件 `cn_adapter.py` 十源 | 一个 catch-all | **否决** — 隐藏 auth/cap/evidence |
| B. 每源独立 port + `cn_market` normalizer | 对齐 R3H-01/02 模式 | **采纳** |
| C. 仅 registry 笔记 closure | 微切片 | **否决** — BATCH_3H_HARDENING_RULES §3 |
| D. 保留 ops staged pilot 为长期路径 | 不迁 L2 | **否决** — G11 产品化要求 |
| E. QMT 默认 READY 加速 demo | 跳过授权 | **否决** — D11 + 活卡 §6 |

## 风险表

| 风险 | 缓解 |
| ---- | ---- |
| registry 与 R3H-04 并行冲突 | §9.8 coordinator manifest；仅改十源行 |
| TDX 双源 tdx_pytdx/mootdx 重复 | 共享 normalizer 片段；独立 source_id；无 silent fallback |
| 工期十源膨胀 | replay-first；live 仅用户显式授权子集 |
| G2/G17 交易日历 | 最小 smoke 或登记 R3H-05 交接（**须 Grill-me Q12**） |

**Phase 2a complete**
