# Plan 对抗性审计 — R3-DCP-01 baostock

> **审计 Agent：** Plan-Audit（`02-plan-audit-agent.md`）  
> **日期：** 2026-06-30 · **模型：** composer-2.5  
> **范围：** `DEBT.plan.md` · `AUDIT.plan.md` · `prd.md` · `research/*` · `check.jsonl` · `implement.jsonl`  
> **对照：** 活卡 · `R3_DCP_TO_ISSUES_INDEX.md` §1 · `BRANCH-DCP-01.md` · `00-MAIN-SESSION-COORDINATOR.md` §4 · 源码抽样复验

---

## 裁决

| 项                         | 结果                                  |
| -------------------------- | ------------------------------------- |
| debt-lite 完整性（清单 A） | **PASS**（修复后）                    |
| 范围与冲突（清单 B）       | **PASS**（修复后）                    |
| 遗留 open items            | **0**                                 |
| `validate-plan-freeze`     | **N/A**（debt-lite · 未升格 complex） |

**结论：** Plan 闸门可放行 Execute（由主会话派发 `03-execute-agent.md`；本轨 **不** `task.py start`）。

---

## 审计清单复验

### A. debt-lite 完整性

| 检查项                                                 | 结果 | 证据                                                           |
| ------------------------------------------------------ | ---- | -------------------------------------------------------------- |
| `reference-adoption-dcp01.md` L1/L2/L3 非空 + 证据路径 | ✅   | 9×L1 · 5×L2 · 4×L3；行内路径已对照源码                         |
| `plan-boot.md` 六项上下文                              | ✅   | §「六项上下文复述」1–6 齐全                                    |
| `DEBT.plan.md` allowed/forbidden/AC/验证/证据          | ✅   | 边界 + S01–S06 表六列完整                                      |
| `AUDIT.plan.md` A1–A8                                  | ✅   | 表 + A6 SKIP 理由 + 各维验证点                                 |
| 调研先于 Plan                                          | ✅   | `plan-boot` 必读清单 · adoption 引用 orchestrator/runners 实码 |

### B. 范围与冲突

| 检查项                 | 结果 | 证据                                                                        |
| ---------------------- | ---- | --------------------------------------------------------------------------- |
| 仅碰 baostock 源       | ✅   | forbidden：`fred_port` / `fred_*` / `test_*fred*`                           |
| watermark 归属轨 A     | ✅   | 与 `00-MAIN-SESSION-COORDINATOR.md` §4 一致；`architecture-dcp01` §共享协调 |
| 无 silent canonical 写 | ✅   | `DEBT` production boundary + `AUDIT` A4                                     |
| Execute 切片可单步 TDD | ✅   | S01→S06 每片独立 pytest + evidence 路径                                     |
| `runners.py` 共享锁    | ✅   | allowed 最小注入；`orchestrator.py` 列入 forbidden                          |

### C. 源码抽样（Plan 声称 vs 实码）

| 声称                                                | 复验                                                        | 结论                     |
| --------------------------------------------------- | ----------------------------------------------------------- | ------------------------ |
| `IncrementalJobRunner` 未注入 `start_time/end_time` | `runners.py:419-425` `FetchRequest` 无日期字段              | ✅ 缺口属实              |
| `baostock_port` replay 未窗过滤                     | `baostock_port.py:65-68` 全量返回 fixture                   | ✅ L2 待建               |
| `sync_plan` 仅 dry-run                              | `data_commands.py:68-77` 非 dry-run 抛 `USER_AUTH_REQUIRED` | ✅ S05 真跑路径为预期 L2 |
| 幂等先例                                            | `test_batch_d_orchestration_flow.py:174-220`                | ✅                       |
| clean 目标 `security_bar_1d`                        | `clean_write_targets.py:27-32`                              | ✅                       |

---

## Findings → Fixes → Reverify

| #   | 严重度 | Finding（原文定位）                                                                                                                          | Fix                                                                                         | Reverify                          |
| --- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------- |
| F1  | medium | `DEBT.plan.md` forbidden 未列 `orchestrator.py`；与主会话 §4 共享锁不一致，Execute 可能误改                                                  | 新增 `backend/app/sync/orchestrator.py` 至 forbidden；S03 forbidden 同步                    | ✅ 读 `DEBT.plan.md` forbidden 块 |
| F2  | medium | S02 验证跑 `test_sync_runners.py` 但未列入 allowed；S02 Source ID「INDEX P3–P4」误导                                                         | S02 allowed 加 `tests/test_sync_runners.py`；Source ID 改为「R3-DCP-01 §4 · INDEX P4 前置」 | ✅ 读 S02 表行                    |
| F3  | low    | S03 引用 `tests/service_path_support.py` 但顶层 allowed 无 helper 路径                                                                       | 顶层 allowed 增加 `tests/service_path_support.py`；S03 表与之一致                           | ✅ 读 allowed + S03               |
| F4  | low    | S06 仅列 `source_capabilities.yaml`，漏 `source_registry.yaml`（BRANCH 共享文件）                                                            | S06 Files 列补 `source_registry.yaml`                                                       | ✅ 读 S06 行                      |
| F5  | low    | `reference-adoption-dcp01.md` watermark API 名 `read_trade_date_watermark` 与 `architecture-dcp01.md` `read_bar_trade_date_watermark` 不一致 | L2 行改为 `read_bar_trade_date_watermark` + 完整参数                                        | ✅ 读 L2 watermark 行             |
| F6  | low    | `test_vendor_fetch_e2e.py` 证据行号 `110-204` 偏差（测试起始于 90）                                                                          | 改为 `90-175`                                                                               | ✅ grep + Read                    |
| F7  | low    | `baostock_port` L2 行暗示已过滤，实码未过滤                                                                                                  | 文案改为「现返回全 fixture；Execute 须补」                                                  | ✅ Read `baostock_port.py:65-97`  |
| F8  | low    | `AUDIT.plan.md`「各维重点验证点」缺 A2/A6/A7/A8                                                                                              | 补四节 checklist；A6 标注 SKIP + 计划外扫描                                                 | ✅ 读 `AUDIT.plan.md`             |
| F9  | low    | `BRANCH-DCP-01.md` 任务路径 `wave3-r3-dcp-01-baostock` 与实际目录 `06-30-wave3-r3-dcp-01-baostock` 不符；缺 `runners.py` / `orchestrator` 锁 | 更正路径；allowed 加 `runners.py`；forbidden 加 `orchestrator.py`                           | ✅ 读 `BRANCH-DCP-01.md`          |
| F10 | low    | `check.jsonl` / `implement.jsonl` 仍含 `_example` 占位，无 debt-lite 路由                                                                    | 删除占位；填入 Plan/活卡/research 必读行                                                    | ✅ 读两 jsonl                     |
| F11 | info   | `prd.md` 未登记 Plan-Audit 产物                                                                                                              | 增加 `plan-adversarial-audit.md` 行                                                         | ✅ 读 `prd.md` Plan 交付物表      |

---

## 统计

| 指标     | 数量   |
| -------- | ------ |
| 发现问题 | **11** |
| 已修复   | **11** |
| 遗留     | **0**  |

---

## 主会话自检清单（debt-lite · `02-plan-audit-agent.md`）

```text
[x] research/reference-adoption-dcp01.md — L1/L2/L3 表非空，有证据路径
[x] research/plan-boot.md — 六项上下文齐全
[x] DEBT.plan.md — allowed/forbidden/AC/验证/证据列完整
[x] AUDIT.plan.md — A1–A8 明确（A6 SKIP 有理由）
[x] 调研在 Plan 之前 — 引用链合理
[x] 范围仅 baostock — forbidden 覆盖 fred + orchestrator 共享锁
[x] watermark 轨 A 拥有 — 与 coordinator §4 一致
[x] 禁止 silent canonical 写 — DEBT + AUDIT A4
[x] Execute 切片可单步 TDD — S01–S06
[x] plan-adversarial-audit.md 落盘
[x] 遗留 0
```

---

## 放行备注（Execute Boot）

1. **必读顺序：** `plan-boot.md` → `reference-adoption-dcp01.md` → `architecture-dcp01.md` → `DEBT.plan.md` → 活卡。
2. **共享文件：** 改 `runners.py` 前通知主会话；**不得**改 `orchestrator.py`。
3. **参考项目树：** worktree 无 `参考项目/`；Execute 在用户环境按需 Read（adoption §F 已登记）。
4. **CLI 现状：** `sync_plan` 默认 dry-run；S05 须实现非 dry-run 金路径（替换 `USER_AUTH_REQUIRED` 硬挡或新增子路径）。
