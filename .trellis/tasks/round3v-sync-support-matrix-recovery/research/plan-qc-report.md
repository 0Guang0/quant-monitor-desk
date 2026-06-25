# Plan QC Report — B3V-SYNC Sync Support Matrix & Crash-window Recovery

> **Agent:** Plan 质检 Agent-2 · **model:** `composer-2.5`  
> **Worktree:** `../quant-monitor-desk-wt-b3v-sync`  
> **输入:** `MASTER.plan.md` · `implement.jsonl` · `research/plan-quality-audit-3.10.md` · `plan.freeze.md`  
> **对照:** Playbook §3.5 · §3.8–§3.10 · `manifest_protocol.py` E11

---

## 1. 执行摘要

| 项 | 结果 |
|----|------|
| 初检发现项 | **0**（阻断） / **2**（信息性，已接受） |
| 已修复 | N/A（本轮回无需 Plan 回写） |
| 复检遗留 | **0** |
| `validate-plan-freeze` | **exit 0**（2026-06-25 本轮回跑） |
| `check_docs_specs_indexed.py` | **exit 0** |
| 可派发 Execute | **是**（`composer-2.5` only；待 `plan.freeze.md` §5 用户/协调者批准） |

**裁决：** **PASS_FOR_DISPATCH**

---

## 2. 机械门禁

| 门禁 | 命令 / 检查 | 结果 |
|------|-------------|------|
| Plan freeze | `python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/round3v-sync-support-matrix-recovery` | exit 0 |
| Docs index | `uv run python scripts/check_docs_specs_indexed.py` | exit 0 |
| implement 首行 | L1 = `MASTER.plan.md` | PASS |
| integration-ledger | L5 `research/integration-ledger.md` | PASS |
| audit 首行 | L1 = `AUDIT.plan.md` | PASS |
| manifest_protocol_version | `task.json` / `plan.freeze.md` → `"3"` | PASS |

---

## 3. Playbook §3.5 路径索引（零遗漏复核）

> 规则（§3.9）：§3.x 每行须在 `MASTER` / `implement.jsonl` / `DEBT.plan` 有对应行；**既有接线/测试** 可走 E11a pointer（`source-index.md` + `integration-ledger.md` + `context_pack.json`），不得误入 `implement.jsonl`。

| Playbook §3.5 路径 | MASTER | implement | pointer / 纠偏 | 遗漏风险 |
|--------------------|--------|-----------|----------------|----------|
| `specs/contracts/sync_job_contract.yaml` | §0 §3.5 [x] | L16 | — | 无 |
| `backend/app/sync/orchestrator.py` · `runners.py` | §0 §3.5 [x] | —（E11a） | `source-index.md` §B wiring；`sync-runtime-baseline.md` | 无 |
| `docs/modules/sync_jobs.md` | — | — | **不存在**；纠偏至契约 YAML + `docs/modules/data_sync_orchestrator.md`（`context_pack.json` L71） | 已纠偏 |
| `backend/app/db/write_manager.py` | §0 §3.5 [x] 只读 | —（只读接线） | `source-index.md` §B；`test_write_manager.py` L20 回归锚点 | 无 |
| `tests/test_sync_orchestrator.py` | §5.1 §9 [x] | —（E11） | `context_pack.json` tests L119；`source-index.md` §B deferred | 无 |
| `tests/test_sync_runners.py` | — | — | **不存在**；substitution → `test_sync_orchestrator.py`（MASTER §5.1） | 已纠偏 |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | §0 §3.1 [x] | L11 | VR-SYNC-001/002 路由 | 无 |

**MASTER §3.5 增补行（任务卡/ADR，Playbook 未单列）：**

| 路径 | MASTER | implement | 遗漏风险 |
|------|--------|-----------|----------|
| `B02_04_sync_job_support_and_recovery.md` | §0 [x] | L7 | 无 |
| `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md` | §0 [x] | L18 | 无 |
| `tests/test_r3x_residual_open_items_closure.py` | §5.1 §9.4 | L19 | 无 |
| `tests/test_write_manager.py` | §5.4 | L20 | 无 |
| `docs/modules/data_sync_orchestrator.md` | §0（若存在） | `context_pack.json` | 无 |

**§3.5 结论：** 8/8 有效路径已索引；2 条 Playbook 幽灵路径已文档化纠偏。**PASS**

---

## 4. B3V-OPS 只读依赖

| 检查点 | MASTER 锚点 | 结果 |
|--------|-------------|------|
| 前置声明 | §0 元信息「只读依赖 B3V-OPS `write_contract.yaml` / `WriteManager`」 | PASS |
| Must not own | §0 Batch 边界表：`write_contract.yaml` / WriteManager 写模式语义 | PASS |
| 停止条件 #2 | §1.5：修改 write 契约或 WriteManager 写模式 → 中止 | PASS |
| implement 索引 | `write_contract.yaml` L17（extract: read-only crash context） | PASS |
| integration-ledger | L12 `write_contract.yaml` strategy=`read-only` | PASS |
| 合并顺序 | MASTER 头部 + Playbook §7：B3V-OPS 之后 FF merge | PASS |
| Red flag | §7「与 OPS 并发改 write 契约」→ 只读 + 合并顺序 | PASS |

**结论：** OPS write 契约只读依赖已冻结，Execute 边界清晰。**PASS**

---

## 5. VR-SYNC-001 A/B 门控

| 维度 | 证据 | 结果 |
|------|------|------|
| 路径 A（分支内关闭） | §9.6：`test_syncJob_incremental_crashWindow_*` + `recoverStuckWriting` GREEN → 关闭 VR-SYNC-001 | PASS |
| 路径 B（re-defer） | §9.6：`research/sync-001-handoff.md`（owner Round 3F · R3F-BR-03 · entrypoints · closure tests） | PASS |
| 停止条件 #4 | §1.5：需同事务 COMPLETED 且触及 ADR/WriteManager → 路径 B handoff | PASS |
| 垂直切片 | `vertical-slices.md` SYNC-06 二选一表 | PASS |
| AC 闭合 | AC-SYNC-001 · AC-SYNC-CLOSE · AUDIT A5 | PASS |
| Red flag | §7「只关 matrix 不关 VR-SYNC-001」→ §9.6 门控 | PASS |
| integration-audit | §1 VR-SYNC-001 二选一 → §9.6 | PASS |

**结论：** VR-SYNC-001 关闭逻辑为显式二选一门控，不可静默跳过。**PASS**

---

## 6. E11 `implement.jsonl` 负向表

> `manifest_protocol.py` E11：`backend/app/sync/`、`tests/test_sync_` 不得列入 `implement.jsonl`（Execute 创建或 deferred 接线）。

| 检查 | 结果 |
|------|------|
| `grep implement.jsonl` 无 `backend/app/sync/` | PASS |
| `grep implement.jsonl` 无 `tests/test_sync_` | PASS |
| E11a pointer 文档 | `sync-runtime-baseline.md` L42；`source-index.md` §B inherited/deferred | PASS |
| MASTER §3.5 [x] 与 E11 共存 | 索引在 MASTER + pointer；非 implement 重复列出 | PASS |
| `validate-plan-freeze` E11 子检 | exit 0（无 E11 告警） | PASS |

**结论：** E11 合规；既有 sync 接线通过 E11a pointer 覆盖，不污染 manifest。**PASS**

---

## 7. Playbook §8.4 → MASTER §2/§4 AC 子集

| §8.4 维度 | MASTER AC | 验证链 | 状态 |
|-----------|-----------|--------|------|
| Plan freeze | AC-SYNC-PLAN | `validate-plan-freeze` | PASS |
| Support matrix | AC-SYNC-002 | §9.1–9.3 · S1–S2 | PASS |
| Crash-window | AC-SYNC-001 | §9.5–9.6 · S3–S4 或 handoff | PASS |
| Registry delta | AC-SYNC-REG | §9.4 proposed delta | PASS |
| 测试纪律 | AC-SYNC-TEST | §5 五字段 + 语义断言 | PASS |
| Playbook PASS | AC-SYNC-PLAYBOOK | §10 §6 Tier A | PASS |
| VR 闭合 | AC-SYNC-CLOSE | VR-SYNC-002 关闭；VR-SYNC-001 二选一 | PASS |

---

## 8. 信息性观察（非阻断）

| # | 观察 | 严重度 | 处置 |
|---|------|--------|------|
| I1 | Playbook §3.1 共用底座部分路径（如 `runtime_versions.md`、`resource_limits.yaml`、registry `RESOLVED`）仅在 MASTER §3.1 摘要行出现，未逐条入 `implement.jsonl` | 低 | **接受**：MASTER「无损摘要」+ freeze gate exit 0；不影响 SYNC 切片 Execute |
| I2 | `plan.freeze.md` §5 用户批准仍为 `[ ]` | 流程 | Execute 前须协调者勾选批准 |

---

## 9. 与 `plan-quality-audit-3.10.md` 交叉核对

- §3.10 表 **15 行**：遗漏风险列均为「无」或「已纠偏/门控」
- 本 QC 独立复检 §3.5、OPS 只读、VR-SYNC-001 A/B、E11：**一致，无新增阻断项**

---

## 10. 复检结论

| 专项 | 结果 |
|------|------|
| §3.5 路径索引 | **PASS**（含 2 条纠偏） |
| B3V-OPS 只读依赖 | **PASS** |
| VR-SYNC-001 A/B 门控 | **PASS** |
| E11 implement.jsonl | **PASS** |
| `validate-plan-freeze` | **exit 0** |
| 阻断遗留项 | **0** |

**Execute 派发：** 可派发 Agent-3（Execute）；模型 **`composer-2.5`**；禁 `composer-2.5-fast`。  
**禁止：** 本 QC 回合不执行 `task.py start`、不写业务代码、不跑 §9 RED/GREEN。
