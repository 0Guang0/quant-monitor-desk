# Plan 对抗性审计 — R3-DCP-02 fred macro incremental

> **审计 agent：** Plan-Adversarial（Wave 3 轨 B）  
> **日期：** 2026-06-30  
> **模型：** composer-2.5  
> **任务目录：** `.trellis/tasks/06-30-wave3-r3-dcp-02-fred`  
> **权威：** `02-plan-audit-agent.md` · `agents/audit-adversarial-authority.md` · `00-MAIN-SESSION-COORDINATOR.md` §4 · `BRANCH-DCP-02.md`

---

## 1. 审计结论

| 指标         | 数量  |
| ------------ | ----- |
| **发现问题** | 7     |
| **已修复**   | 7     |
| **遗留**     | **0** |

**裁决：** Plan 产物可进入 P4 Execute（对抗审计 PASS）。

---

## 2. 清单复验（A–C）

### A. debt-lite 完整性

| 检查项                                                          | 结果 | 证据                                       |
| --------------------------------------------------------------- | ---- | ------------------------------------------ |
| `research/reference-adoption-dcp02.md` L1/L2/L3 非空 + 证据路径 | PASS | §2 总表 15 行；§3–§4 深读锚点              |
| `research/plan-boot.md` 六项上下文                              | PASS | §1 做什么/价值/约束/设计/成功标准/完成条件 |
| `DEBT.plan.md` 列完整                                           | PASS | 5 切片 × AC/allowed/forbidden/验证/证据    |
| `AUDIT.plan.md` A1–A8                                           | PASS | §1 维度表；A6 SKIP §2.2                    |
| 调研先于 Plan                                                   | PASS | reference-adoption 日期与 DEBT 引用链一致  |

### B. 范围与冲突

| 检查项                 | 结果           | 备注                                                        |
| ---------------------- | -------------- | ----------------------------------------------------------- |
| 仅碰 fred 源           | PASS           | forbidden 含 baostock_port/adapters/tests                   |
| watermark 共享归属     | PASS（修复后） | 轨 A 写 `sync/watermark*`；本轨只读宏观 API 或 `ops/fred_*` |
| 无 silent canonical 写 | PASS           | production boundary + AUDIT §5                              |
| Execute 切片可单步 TDD | PASS           | S02-01..05 各绑单一 pytest 模块                             |

### C. 重点关切（用户指定）

| 关切                                           | 结果                                                               |
| ---------------------------------------------- | ------------------------------------------------------------------ |
| fred per-series watermark vs 轨 A `trade_date` | PASS — `indicator_id` + `DATE(publish_timestamp)`；禁止 bar reader |
| 共享 sync/watermark 所有权                     | PASS — orchestrator/runners/watermark 写权限归轨 A                 |
| 禁止 baostock 触及                             | PASS — DEBT/AUDIT forbidden 显式列出                               |

---

## 3. Finding Ledger（问题 → 修复 → 复验）

| #   | 原文定位                                             | 标签                  | Disposition | 修复                                                                                              | 复验                                                                |
| --- | ---------------------------------------------------- | --------------------- | ----------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| F1  | `DEBT.plan.md` allowed `backend/app/sync/**`         | BLOCKING · 范围泄漏   | **已修复**  | 收窄为只读 import；forbidden 增 `orchestrator.py` · `runners.py` · registry · `test_catalog.yaml` | 对照协调手册 §4 + DCP-01 轨锁                                       |
| F2  | `DEBT.plan.md` S02-03 forbidden 仅 `orchestrator.py` | BLOCKING · 共享锁     | **已修复**  | 增 `runners.py` · `baostock_port`；AC 注明调用方传 macro PipelineConfig                           | 切片表行 S02-03                                                     |
| F3  | `DEBT.plan.md` 协调依赖「薄包装 L1」未禁 bar reader  | HIGH · 语义混淆       | **已修复**  | 明确禁止 `read_*trade_date*`；仅宏观 API                                                          | §协调依赖段                                                         |
| F4  | 多文件 CLI `qmd data sync --source fred`             | BLOCKING · 与代码不符 | **已修复**  | 统一为 `--domain macro_series --source-id fred`（`cli/main.py` L23-35 现状）                      | `DEBT` S02-05 · `architecture` §6 · `prd` · `AUDIT` A7 · `grill-me` |
| F5  | `architecture-dcp02.md` §2.1 未禁 bar watermark API  | MEDIUM                | **已修复**  | 增宏观专用 API + 禁止 trade_date 函数                                                             | §2.1 · §3 组件表                                                    |
| F6  | `architecture-dcp02.md` orchestrator「尽量不改」     | MEDIUM · 措辞弱       | **已修复**  | 改为「禁止本轨修改」                                                                              | §3 组件表                                                           |
| F7  | `plan-boot.md` 缺 debt-lite 自检清单                 | NON-BLOCKING · 闸门   | **已修复**  | 增 §6 九项全勾                                                                                    | `plan-boot.md` §6                                                   |

---

## 4. 未改动的合理设计（审计确认）

1. **活卡** `R3_DCP_02_FRED_INCREMENTAL.md` §4 仍写「`--source fred`」为概念 shorthand；Execute 以 CLI 实旗标 `--domain` + `--source-id` 为准（与 DCP-01 `--domain` 先例一致）。
2. **debt-lite** 不产出 `EXECUTION_INDEX.md` / `plan.freeze.md` — 符合 Phase 8D。
3. **A6 SKIP** — tracer bullet、≤10 series、硬 cap；理由充分。
4. **S02-01** 默认 `ops/fred_incremental_watermark.py` 绿场实现 — 不阻塞快轨等轨 A。

---

## 5. Execute 入口提醒（非 finding）

- RED 前必读：`reference-adoption-dcp02.md` §5 门禁表。
- `run_incremental` 默认 `primary_keys=("instrument_id","trade_date")` — e2e 必须显式传 macro 参数（`architecture-dcp02.md` §4）。
- 轨 A merge 后 rebase：检查 `sync/watermark.py` 是否暴露宏观 API；无则继续 ops 局部实现。

---

## 6. 复验签名

```text
Plan-Audit Agent · R3-DCP-02 · 2026-06-30
发现问题 7 / 已修复 7 / 遗留 0
下一步：P4 Execute（03-execute-agent.md）· 禁止 task.py start 前跳过本审计
```
