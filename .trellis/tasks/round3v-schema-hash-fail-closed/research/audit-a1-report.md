# A1 Spec / Trace 审计报告 — B3V-DATA `round3v-schema-hash-fail-closed`

| 字段 | 值 |
|------|-----|
| 维度 | A1（Spec / Trace / trellis-check） |
| 分支 | `fix/round3v-schema-hash-fail-closed` |
| Worktree | `quant-monitor-desk-wt-b3v-data` |
| 审计员 | trellis-check（只读 · 仅 A1） |
| 日期 | 2026-06-25 |
| **裁决** | **BLOCKING** |

---

## 1. 裁决摘要

工作区 diff 在行为层面与 `B02_02` §2–§6、`MASTER.plan.md` §2 AC-DATA-01..04 基本对齐；A8 指定 pytest 子集全绿；Trace Authority 血缘完整；B02-DATA-05 / `VR-DATA-001` registry 闭合已 explicit defer 至主会话。

**BLOCKING（2 项，须 Execute/主会话闭合后方可签收）：**

1. **交付物未入分支** — 6 个生产/契约/测试文件均为 unstaged 修改；`git log master..HEAD` 为空；`.trellis/tasks/round3v-schema-hash-fail-closed/` 整棵未跟踪。`MASTER.plan.md` §10 勾选「`validate-execute-handoff` 0」，与 git 可审计事实矛盾。
2. **Spec 与契约漂移** — `specs/contracts/data_adapter_contract.md` 已冻结结构化 `schema_hash` fail-closed 规则，但 `.trellis/spec/backend/datasource-adapters.md` §3 Contracts 表 L41 仍写「`FetchPayload.schema_hash` Optional; JSON dict keys fingerprint when omitted」。`implement.jsonl` L32 点名该 spec 用于「§9.1 contract align」，却未同步更新。

---

## 2. trellis-check 步骤证据（§3.1）

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 1 变更范围 | WARN | `git status`：6 modified（`skeleton_base.py`, `validation_gate.py`, `data_adapter_contract.md`, 3 test 文件）+ untracked task tree；`git diff master --stat` 336 insertions（仅工作区，无 commit） |
| 2 任务工件 | PASS | `prd.md` 薄索引；`AUDIT.plan.md` §0.1 Trace Authority 已读；`B02_02` §4 forbidden / §6 测试已对照 |
| 3 包上下文 | SKIP | 只读 A1；变更集中于 `datasources/adapters` + `db` + `specs/contracts` |
| 4 Spec Quality | **FAIL** | `.trellis/spec/backend/datasource-adapters.md:41` 与 `data_adapter_contract.md:43-63` 语义冲突 |
| 5 项目检查 | PARTIAL | A8 子集 exit 0（103 passed）；`uv run ruff check backend/app/datasources backend/app/db tests/...` exit 1（9 项，多数为既有文件 E501/I001，见 §6） |
| 6 跨层链 | PASS | `SkeletonAdapterBase._fetch_impl` → `fetch_log.schema_hash` → `DbValidationGate._schema_hash_blocks_write` → `ValidationRejected`（`skeleton_base.py:182-202`, `validation_gate.py:242-248`） |
| 7 manifest 对账 | PASS | diff 6 文件 ⊆ `implement.jsonl` 点名；无 registry/migration/RawStore/layer5 等 forbidden 路径 |

---

## 3. Trace Authority（AUDIT.plan §0.1）

| 条目 | 结果 | 证据 |
|------|------|------|
| 原始任务卡 | PASS | `B02_02_schema_hash_fail_closed.md` → MASTER §2 AC-DATA-01..05；§4 forbidden → MASTER §1.4/§1.5 |
| VR 索引 | PASS（defer） | `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` 路由 `VR-DATA-001`；B02-DATA-05 → `original-plan-trace.md` 主会话 |
| Batch 边界 | PASS | `BATCH_3V_HARDENING_RULES.md` §3–§4 与 MASTER §0 Must not 一致（无 live fetch / 无 production clean write） |
| source-index | PASS | `research/source-index.md` §A–§C 索引完整 |
| original-plan-trace | PASS | B02-DATA-01..04 Execute；B02-DATA-05 explicit defer |
| integration-ledger | PASS | 与 MASTER §8 DATA-01..04 锚点一致 |
| omission-check | PASS | source-index §C 六类覆盖全 [x]；无未登记越界 |

---

## 4. AC / 契约对账（MASTER §2）

| AC | 任务卡要求 | 实现/测试证据 | 结果 |
|----|-----------|---------------|------|
| AC-DATA-01 | 契约写明结构化 schema_hash | `data_adapter_contract.md:43-63` + `test_dataAdapterContract_documentsStructuredSchemaHashRequirement` | PASS |
| AC-DATA-02 | CSV/Parquet 有界推导 | `_infer_csv_schema_hash`（64KiB 前缀 + header）/ `_infer_parquet_schema_hash`（DuckDB DESCRIBE 列名）+ infer 测试 | PASS |
| AC-DATA-03 | Gate 缺 hash fail-closed | `_schema_hash_blocks_write` L242-248 + `test_missingSchemaHashOnStructuredFetch_rejects` | PASS |
| AC-DATA-04 | 损坏文件不可 SUCCESS 写路径 | `_fetch_impl` SCHEMA_DRIFT 守卫 L182-202 + corrupt CSV/Parquet 测试 | PASS |
| AC-DATA-05 | 漂移仍拒绝 | `test_schemaHashDriftWithoutApproval_rejects` 回归未删 | PASS |
| B02-DATA-05 / VR 闭合 | registry 主会话 | MASTER §1.4 + `original-plan-trace.md` explicit defer | PASS（defer，非本切片 Done） |

### TDD / 负向证据（B3V-AUD-05）

| 步骤 | RED 证据 | GREEN 证据 |
|------|----------|------------|
| DATA-01 | `execute-evidence/9.1-red.txt` | `9.1-green.txt` |
| DATA-02 | `execute-evidence/9.2-red.txt` — infer assert None | `9.2-green.txt` |
| DATA-03 | `execute-evidence/9.3-red.txt` — `DID NOT RAISE ValidationRejected` | `9.3-green.txt` |
| DATA-04 | `9.4-red.txt` / `9.4-green.txt` | corrupt 负向保留 |

---

## 5. GitNexus

| 动作 | 结果 |
|------|------|
| `query("schema_hash fail-closed ValidationGate")` | 命中 `assert_can_write` → `_enforce_report` → `_schema_hash_blocks_write` 流程（proc_73） |
| `context("_schema_hash_blocks_write")` | 上游 `_enforce_report`；epistemic exact |
| 索引新鲜度 | **WARN**：索引示 `_infer_schema_hash` L25-37（JSON-only 旧版）；工作区已扩展至 L85-100（CSV/Parquet）；`_schema_hash_blocks_write` 行号亦滞后。合并前建议 `node .gitnexus/run.cjs analyze` |

---

## 6. Findings

### BLOCKING

| ID | 位置 | 发现 | 建议 |
|----|------|------|------|
| A1-B01 | `git status` / MASTER §10 | 实现与任务工件均未 commit；`HEAD` 与 `master` 同提交 `d62e8dc4` | Execute 侧 commit 允许文件 + 任务目录；重跑 `validate-execute-handoff` |
| A1-B02 | `.trellis/spec/backend/datasource-adapters.md:41-42` | Spec 仍称 schema_hash「Optional / JSON only」，与契约及 `_fetch_impl` 结构化守卫矛盾 | 更新 §3：结构化 SUCCESS+row_count>0 必填；CSV/Parquet 有界推导；或 pointer 至 `data_adapter_contract.md` VR-DATA-001 段 |

### NON-BLOCKING

| ID | 位置 | 发现 |
|----|------|------|
| A1-N01 | 全量 pytest | 本任务未跑全量；A8 子集 103 passed。全量失败若存在，疑为 worktree 基线/环境，非本 diff 回归 |
| A1-N02 | ruff 作用域 | 9 项中 8 项位于未改文件（`route_planner.py`, `service.py`, `con_helpers.py`, 既有 contract 测试 docstring）；`test_db_validation_gate.py:333` E501 位于既有 drift 测试（行号因插入新用例位移），非本任务新增逻辑 |
| A1-N03 | GitNexus | 符号行号滞后（见 §5） |
| A1-N04 | `docs/modules/data_validation_and_conflict.md` | 未镜像契约「结构化缺 hash fail-closed」— 可选文档补强 |
| A1-N05 | DuckDB 依赖 | `skeleton_base.py` 新增 `import duckdb`；`pyproject.toml` 已有 `duckdb>=1.1.0`，非新重依赖，符合 B02_02 §4「无审批不重依赖」 |

---

## 7. 计划外发现（对抗性搜索）

> 已对照 `agents/audit-adversarial-authority.md` A1：设计边界 + 契约 scope vs diff + Red Flags + 计划外 defer。

| ID | 严重度 | 发现 | 说明 |
|----|--------|------|------|
| ADV-01 | NON-BLOCKING | Gate 在 **current hash 有值、baseline 缺失** 时 fail-open（`validation_gate.py:264-265`） | MASTER §2.2 设计为「baseline 存在且不同 → block」；首写场景可能故意放行 |
| ADV-02 | NON-BLOCKING | Parquet infer 将整段 payload 写入 temp 文件（`skeleton_base.py:57-59`） | 受 `max_payload_bytes`（10MB）约束；不扫行数据 |
| ADV-03 | NON-BLOCKING | `_fetch_log_is_structured` 无路径后缀时回查 `file_registry` 最近 structured 行（L195-206） | 主路径测试用 `.csv` 后缀覆盖；历史行误判风险低但存在 |
| ADV-04 | INFO | 全部 vendor adapter 继承 `SkeletonAdapterBase` | 无计划外旁路 adapter |
| ADV-05 | INFO | diff 无 registry / migration / production clean write | 符合 AUDIT.plan A3/A7 前置 |

**显式声明：** 已对抗搜索；未发现计划外 forbidden 文件改动；未发现削弱 B3V-AUD-05 负向测试目的。

---

## 8. A1 Checklist

- [x] trellis-check 步骤 1–7 有证据（§2）
- [x] diff vs audit/check manifest（`implement.jsonl` / `check.jsonl`）
- [x] Trace Authority 已继承或 explicit defer（B02-DATA-05）
- [x] 无 Plan omission（source-index / round map）
- [x] GitNexus 已 query + context（索引陈旧已注明）
- [ ] **Spec 与实现同步** — BLOCKING（A1-B02）
- [ ] **分支可审计交付物** — BLOCKING（A1-B01）

---

## 9. 验证命令记录

```text
# A8 子集（AUDIT.plan §1）
uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest
→ exit 0（103 passed）

# Tier B ruff（任务卡 §7 作用域）
uv run ruff check backend/app/datasources backend/app/db tests/test_db_validation_gate.py tests/test_adapter_skeletons.py tests/test_data_adapter_contract.py
→ exit 1（9 issues，见 §6 A1-N02）

# 分支事实
git log master..HEAD --oneline
→ （空）
git diff master --stat
→ 6 files, 336 insertions（工作区 only）
```

---

## 10. 后续（非 A1 范围）

- A2–A8 由主会话按 `AUDIT.plan.md` 派发；本报告不串演。
- A1-B01/B02 闭合前不建议 `finish-work` 或宣称 Batch 3V-DATA Audit PASS。
