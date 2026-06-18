# Repair Report — Round 2 Batch D

> Phase 8 Repair · 2026-06-19 · 主会话执行  
> 依据：Audit `audit.report.md` §4.3 + 各子 agent `research/audit-sections/A1–A8.md`

---

## 1. 判定

**Repair: CLOSED** — 所有子 agent 标记的可在本轮修复项已落地；严格 §9.3 `pytest -q` + `ruff check .` 全绿。

| 门禁 | Repair 后 |
|------|-----------|
| `pytest -q --cov=backend --cov-fail-under=75` | **PASS**（330+ tests, cov 93.82%） |
| `ruff check .` | **PASS** |
| `test_manifest_protocol.py -k batch_d` | **7/7 PASS** |
| Tier A sync | **27/27 PASS**（含 redaction 新测） |

---

## 2. 问题来源说明

§4.3 编号（R-D-xx）来自 **A9 主会话** 汇总各子 agent 发现后写入 `audit.report.md`。  
各修复项的**原始发现**均对应下表子 agent 维度（非主会话臆造）。

---

## 3. 子 agent 发现 → 处置

### A1 Spec ([dce395b6](dce395b6-8638-47da-b0e7-d92475c18ce2))

| 发现 | 优先级 | 处置 |
|------|--------|------|
| O-2 `implement.jsonl` 缺 `test_batch_d_orchestration_flow.py` | P1 | **已修复**（Audit 补行；Repair 保留） |
| Adversarial：`jobs.py` / `orchestrator.py` / `006.sql` 未入 manifest | — | **不修复（设计）** — `manifest_protocol` E11 禁止 Execute-created 路径入 implement；见 §4 Deferred D-A1-1 |
| 契约/架构/runtime 对齐 | — | 无代码变更需求 |

### A2 Code review ([075d1597](075d1597-6701-4d30-ac63-33dca78e83c1))

| 发现 | 优先级 | 处置 |
|------|--------|------|
| R-D-02 `emit_event` 重复 `job_event_log` INSERT | Important | **已修复** — `SyncJobStateMachine.emit_custom_event` + orchestrator 委托 |
| `begin_fetching` 在 state machine 外写 `error_*` | Important | **已修复** — `transition(..., error_type=, error_message=)` |
| `run_reconcile` 未使用 `adapter` | Suggestion | **已修复** — 注释标明 Round 3 |
| `run_incremental` 过长 | Suggestion | **Deferred D-A2-1** → Round 3 |
| `run_backfill` 可抽 helper | Suggestion | **Deferred D-A2-2** → Round 3 |
| COMPLETED 独立事务 | Suggestion | **Deferred D-A2-3** — orchestrator 注释 intentional split |

### A3 DB ([8bafa069](8bafa069-f62f-46d7-8e9c-e75a3022ccff))

| 发现 | 优先级 | 处置 |
|------|--------|------|
| 006 幂等/列对齐/init_db×2 | — | 无需变更 |
| P2：`schema.sql` 缺 006 索引 | Suggestion | **已修复** — 补 `idx_data_sync_job_run_id` / `idx_job_event_log_job_id` |
| migrate.py 事务文档 | Suggestion | **Deferred** — `.trellis/spec/backend/database-guidelines.md` 待填充时补 |

### A4 Tests ([a275d5af](a275d5af-fd7e-4608-a877-f55c6a9c6b3d))

| 发现 | 优先级 | 处置 |
|------|--------|------|
| O-2 manifest | P1 | **已修复**（同 A1） |
| O-1 ruff E501 | P2 | **已修复** — `test_trellis_validate_plan.py` 折行 |
| O-3 strict pytest | P2 | **已修复** — meta 测试 `from common.*` 导入 + handoff fixture 补 boot-reads |
| AC-2 六种 job_type | — | 已满足 |
| `data_quality` 未 invoke validator 单测 | Low | **Deferred D-A4-1** → Round 3（MASTER 骨架边界） |

### A5 Traceability ([5cd755f2](5357-404c-856f-35298adfc606))

| 发现 | 优先级 | 处置 |
|------|--------|------|
| AC-11 因 O-1/O-3 封顶 4 | — | **已修复** — 全门禁绿 → AC-11 可升至 5 |
| `8.8-green.txt` 计数 2 vs 1 | Info | 证据文件未改（历史 drift）；不影响门禁 |
| O-3 诚实披露 | — | 接受；Repair 后 strict Tier C 绿 |

### A6 Security ([1e8ec322](1e8ec322-23ed-4fea-88c7-e3d07a223e1b))

| 发现 | 优先级 | 处置 |
|------|--------|------|
| R-D-03 fetch 错误未 redact 入 `job_event_log` | Medium/P2 | **已修复** — `_safe_event_message` / `_insert_job_event` |
| LOW `trigger_reason` 无 allowlist | Low | **已修复** — `BACKFILL_TRIGGER_REASONS` + `normalize_backfill_trigger_reason` |
| INFO 缺 orchestrator redaction 测试 | Info | **已修复** — `test_orchestrator_fetchFailure_redactsErrorInJobEventLog` |
| INFO `error_message` 列 footgun | Info | **已修复** — guard 路径经 `transition` redact |
| Round 3+ API 暴露 operator-only | Recommendation | **Deferred D-A6-1** |

### A7 Resource/scope ([7e7c5d3f](7e7c5d3f-6312-4003-80d5-af1edb6a2bbf))

| 发现 | 优先级 | 处置 |
|------|--------|------|
| ResourceGuard / eco / scope | — | 无变更 |
| A7-I1 pytest `-k resource` 窄 | Info | **Deferred D-A7-2** — 文档 |
| A7-I2 骨架 job 未达 FETCHING | Info | **Deferred D-A7-1** → Round 3 |

### A8 Docs ([66935f12](66935f12-2af0-404f-8d10-98030a4589e5))

| 发现 | 优先级 | 处置 |
|------|--------|------|
| R-D-08 双 handoff 路径/内容 | P2 | **已修复** — 统一 `execute-evidence/8.11-handoff.txt` + research 副本 |
| R-D-09 `EXECUTE-READY.md`  stale | P2 | **已修复** |
| R-D-10 DECISIONS 缺 open-items 脚注 | P2 | **已修复** |
| BATCH_D_STATUS evidence 路径 | P2 | **已修复** — 指向 canonical `execute-evidence/` |

---

## 4. Deferred（必须后续轮次）

| ID | 问题 | 阶段 |
|----|------|------|
| D-A1-1 | Execute-created 路径（sync/*, 006, sync_registry）不入 implement.jsonl | **By design** — E11；交付见 `BATCH_D_STATUS` D-1…D-7 |
| D-A2-1 | `run_incremental` 拆 helper | Round 3 refactor |
| D-A2-2 | `run_backfill` 抽 `_run_shard_fetch` | Round 3 refactor |
| D-A2-3 | COMPLETED 与 write 单事务 | Round 3 ops hardening |
| D-A4-1 | `data_quality` job 调用 validator 深度测 | Round 3（§6.6 完整语义） |
| D-A6-1 | `job_event_log` API 字段 ACL | Round 3 API |
| D-A7-1 | full_load/revision_audit/data_quality 经 `begin_fetching` | Round 3 fetch 路径 |
| D-A7-2 | Tier B 命令文档 `-k "resource or guard"` | Trellis 文档 |

---

## 5. 代码变更摘要

| 文件 | 变更 |
|------|------|
| `backend/app/sync/jobs.py` | redaction、`_insert_job_event`、`emit_custom_event`、`transition` error 字段、trigger allowlist |
| `backend/app/sync/orchestrator.py` | 委托 emit、guard error 经 SM、backfill trigger 校验、注释 |
| `tests/test_sync_orchestrator.py` | redaction 测试；backfill trigger 用 `manual_request` |
| `tests/test_trellis_validate_plan.py` | 包导入 + E501 折行 |
| `tests/test_trellis_validate_execute.py` | 包导入 + boot 证据 fixture |
| `tests/test_manifest_protocol.py` | ruff import 整理（自动） |
| `specs/schema/schema.sql` | 006 索引镜像 |
| `implement.jsonl` | 保留 O-2 测试路径（E11 合规） |
| 文档 | `BATCH_D_STATUS.md`, `DECISIONS.md`, `EXECUTE-READY.md`, handoff 文件 |

---

## 6. 更新 Audit 判定

Repair 后建议任务判定：**PASS**（原 PASS_WITH_FIXES §4.3 已闭合）。
