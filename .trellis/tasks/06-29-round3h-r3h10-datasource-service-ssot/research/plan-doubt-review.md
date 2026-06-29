# Plan 加固 — doubt-driven-development

> **Skill:** `doubt-driven-development` · **单模型对抗审查** @ 2026-06-29  
> **说明：** 交互式 cross-model 未启用；用户可在 freeze 前要求 Gemini/Codex 二轮。

---

## Cycle 1 — fail-closed（S10-01）

### CLAIM

生产 Sync 调用方未传 `datasource_service=` 时必须失败，禁止框架自动构造默认 `DataSourceService`。

### ARTIFACT

`to-issues-slices.md` §3 + ADR-025 草案。

### CONTRACT

- 与 `guard_production_adapter_bypass` 对称（adapter 旁路已 fail-closed）
- 错误可测、可区分「缺 service」vs「adapter 旁路」
- 不引入隐式第二条 sync 入口（EasyXT 反例）

### 对抗发现

| #   | 发现                                                                                                                                                             | 分类                                                                                    |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| D1  | `IncrementalJobRunner.run` 已在 `adapter is None and fetch_callable is None` 时 `ValueError`（`runners.py:369`）— 行为可能**已是** fail-closed，但文案为 generic | **trade-off** — S10-01 应强化 orchestrator 层 + 契约化错误码/文案，而非重复 runner 逻辑 |
| D2  | pytest 路径可能仍传 `adapter=`；fail-closed 须继续尊重 `sync_adapter_bypass_allowed()`                                                                           | **actionable** — 测试勿破坏                                                             |
| D3  | CLI / 脚本若未传 service 会怎样？需矩阵逐行核对                                                                                                                  | **actionable** — BOOT 矩阵已列；S10-02 覆盖 CLI                                         |

### RECONCILE

裁决**成立**；Execute 重点是**显式契约 + 负向测 + 错误语义**，非从零新造 fail-closed。

---

## Cycle 2 — S10-05 双轨收敛

### CLAIM

`ops/*_fetch_ports` 与 `datasources/fetch_ports` 可收敛为同一 `FetchPort` 实现类而不破坏 rehearsal。

### ARTIFACT

`to-issues-slices.md` §7 · `bypass-baseline-matrix.md` 行 6–8。

### CONTRACT

- `test_staged_pilot.py` / `test_batch275_live_pilot_gate.py` 保持绿
- rehearsal 能力不删
- baostock/cninfo 等 READY 源行为不漂移

### 对抗发现

| #   | 发现                                                           | 分类                                                                                      |
| --- | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| D4  | 薄委托若 staging 与 production 注入路径不同，可能隐藏 env 差异 | **actionable** — 测须断言**同一类**                                                       |
| D5  | S10-05 与 S10-04（interface_probe）文件重叠风险                | **trade-off** — 分 PR；先 04 后 05                                                        |
| D6  | 「deprecated re-export」vs「inline 委托」— 未在 Plan 冻结选型  | **contract misread** — 补 ADR 一句：优先薄委托同一模块，deprecated 仅当 import 面必须保留 |

### RECONCILE

S10-05 仍为最高风险切片；Execute 前在活卡补「收敛策略：薄委托 > re-export」。

---

## Cycle 3 — Plan freeze 延后

### CLAIM

无 `frozen/*.md` 亦可按切片 Execute。

### CONTRACT

Trellis complex 任务最终须 `validate-plan-freeze` 才能 `finish-work` / Audit PASS。

### 对抗发现

| #   | 发现                                                      | 分类                                                                          |
| --- | --------------------------------------------------------- | ----------------------------------------------------------------------------- |
| D7  | `research/*` 决策可能未进 frozen → Execute agent 误读草稿 | **actionable** — `plan-consolidation.md` 标 must-read；freeze 前 ADR/活卡承接 |
| D8  | 用户逐步 Execute 与 5e 合并顺序冲突                       | **trade-off** — 已接受；CLOSE 前必须 freeze                                   |

### RECONCILE

**接受 trade-off**；S10-CLOSE 前跑 `validate-plan-freeze`。

---

## Stop condition

三轮后无新的 P0 级 Plan 缺陷；剩余为 Execute 期实现细节。

**Cross-model：** 未询问用户 — 若需二轮，请指明 Gemini/Codex。

---

## doubt-driven-development 验证清单

- [x] 非平凡决策已 CLAIM
- [x] ARTIFACT + CONTRACT 分离
- [x] 发现已分类（actionable / trade-off / noise）
- [x] Stop condition 满足
