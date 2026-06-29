# R3-DCP-01 — baostock incremental watermark

> **轨道：** Wave 3a · debt-lite · `feature/wave3-r3-dcp-01-baostock`  
> **活卡 SSOT：** `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_01_BAOSTOCK_INCREMENTAL.md`  
> **Execute SSOT：** `DEBT.plan.md` + `research/reference-adoption-dcp01.md`

---

## 目标（人话）

让中国 A 股日频 bar（baostock）能走产品路径：先看隔离库里最后一天，只拉新来的数据，写进 clean 表，命令行能反复跑也不重复堆行。

---

## 价值

- Round 4 日常增量**第一个试点源**（与 fred 并列）
- 验证「读库水位 → incremental → clean write」在真实 port 上可复制
- 不依赖 `--live-wire` 运维脚本

---

## 约束摘要

| 项 | 要求 |
|----|------|
| 金路径 | `DataSourceService.fetch` + `DataSyncOrchestrator.run_incremental` |
| 数据根 | `QMD_DATA_ROOT` 隔离库；禁止 silent 写 canonical 主库 |
| Schema | R3H-06 `security_bar_1d` + upsert；无新 migration |
| 并行 | 轨 A 拥有 watermark + baostock；禁止改 fred |

---

## Acceptance criteria（活卡 §5）

- [ ] watermark 单测：空表 / 有数据 / 边界日
- [ ] incremental 集成测：replay 或 env-gated live（隔离库）
- [ ] 重复跑任务行数不增（写库幂等）
- [ ] CLI help + dry-run 可审计
- [ ] Plan 调研 `research/reference-adoption-dcp01.md` 含 L1/L2/L3 表
- [ ] Audit A1–A8 各维报告 + Repair ledger 关账
- [ ] `uv run pytest -q` exit 0

---

## Plan 交付物（本阶段）

| 产物 | 路径 | 状态 |
|------|------|------|
| 上下文复述 | `research/plan-boot.md` | ✅ |
| L1/L2/L3 调研 | `research/reference-adoption-dcp01.md` | ✅ |
| 架构方案 | `research/architecture-dcp01.md` | ✅ |
| 切片计划 | `DEBT.plan.md` | ✅ |
| 审计矩阵 | `AUDIT.plan.md` | ✅ |
| Grill-me | `research/grill-me-session.md` | ✅ 无未决 |
| Plan 对抗审计 | `research/plan-adversarial-audit.md` | ✅ |
| PRD（本文件） | `prd.md` | ✅ |

---

## 非目标

- 全 Tier A 源扩展（Wave 4 DCP-05）
- FullLoad / Backfill 产品化
- 改 prediction market / Kalshi / Polymarket
- web_search 真 API

---

## Done

活卡 AC 全勾 + P6 Repair 关账 + 主会话 merge → `R3H_PASS_EXECUTION_PLAN` Wave 3 DCP-01 **CLOSED**。
