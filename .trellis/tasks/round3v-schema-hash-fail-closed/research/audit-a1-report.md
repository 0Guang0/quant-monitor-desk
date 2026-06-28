# A1 Spec / Trace 审计报告 — B3V-DATA `round3v-schema-hash-fail-closed`

| 字段 | 值 |
|------|-----|
| 维度 | A1（Spec / Trace / trellis-check） |
| 分支 | `fix/round3v-schema-hash-fail-closed` |
| Worktree | `quant-monitor-desk-wt-b3v-data` |
| 审计员 | Audit-A1（只读） |
| 日期 | 2026-06-28 |
| **裁决** | **PASS** |

---

## 1. 裁决摘要

实现已入分支历史（`1bc0260d fix(data): schema_hash fail-closed for structured fetches (B3V-DATA)`，亦为 `master` 祖先）；`DATA-01..04` 与 `validation_gate` / `schema_hash` 行为对齐 `B02_02` 与 MASTER §2 AC-DATA-01..05（registry 除外）；A8 指定 pytest 子集 **106 passed**；`validate-execute-handoff` exit 0；Trace Authority 血缘完整；B02-DATA-05 explicit defer 至主会话。

相较 2026-06-25 初版 A1：**A1-B01（未 commit）与 A1-B02（spec 漂移）已闭合**——实现与 `.trellis/spec/backend/datasource-adapters.md:41` 已在 `1bc0260d` 同步。

**NON-BLOCKING（2 项，不阻 A1 PASS）：**

1. 分支相对 `master` 额外含 `tests/conftest.py` R3H/R3G 授权 bootstrap（+37 行），不在 B3V-DATA manifest / forbidden 之外，但属计划外邻接改动。
2. Tier B `ruff check` 在任务卡 §7 宽作用域 exit 1（51 项，多为既有测试 docstring E501）；**本任务生产文件** `skeleton_base.py` / `validation_gate.py` ruff **全绿**。

---

## 2. trellis-check 步骤证据（§3.1）

| 检查项 | 结果 | 证据 |
|--------|------|------|
| 1 变更范围 | PASS | `git log master..HEAD`：3 doc commits + 任务工件；实现于 `1bc0260d`（`git merge-base --is-ancestor 1bc0260d HEAD` exit 0）；`git diff master --stat` 主要为 `.trellis/tasks/round3v-schema-hash-fail-closed/` + `tests/conftest.py` |
| 2 任务工件 | PASS | `AUDIT.plan.md` §0.1；`B02_02` §4 forbidden / §6 测试；`MASTER.plan.md` §8–§9 |
| 3 包上下文 | PASS | 变更集中于 `datasources/adapters`、`db`、`specs/contracts`、§5.1 三测试文件 |
| 4 Spec Quality | PASS | `data_adapter_contract.md:46-66` 与 `.trellis/spec/backend/datasource-adapters.md:41` 一致（pointer + structured 必填） |
| 5 项目检查 | PASS | A8 子集 exit 0（106 passed，`--basetemp=.audit-sandbox/pytest-a1`）；生产文件 ruff exit 0 |
| 6 跨层链 | PASS | `SkeletonAdapterBase._fetch_impl` L182-202 → `fetch_log.schema_hash` → `DbValidationGate._schema_hash_blocks_write` L242-248 → `ValidationRejected` |
| 7 manifest 对账 | PASS | 实现文件 ⊆ `implement.jsonl` L19-32；无 registry/migration/RawStore/layer5 forbidden 路径 |

---

## 3. Trace Authority（AUDIT.plan §0.1）

| 条目 | 结果 | 证据 |
|------|------|------|
| 原始任务卡 | PASS | `B02_02_schema_hash_fail_closed.md` → MASTER §2 AC-DATA-01..05；§4 forbidden → MASTER §1.4/§1.5 |
| VR 索引 | PASS（defer） | `VR-DATA-001`；B02-DATA-05 → `original-plan-trace.md` 主会话 |
| Batch 边界 | PASS | `BATCH_3V_HARDENING_RULES.md` 与 MASTER §0 Must not 一致 |
| source-index | PASS | `research/source-index.md` §A–§C 完整 |
| original-plan-trace | PASS | B02-DATA-01..04 Execute；B02-DATA-05 explicit defer |
| integration-ledger | PASS | 与 MASTER §8 DATA-01..04 锚点一致 |
| omission-check | PASS | source-index §C 六类 [x] |

---

## 4. DATA-01..04 / validation_gate / schema_hash 对账

| 切片 | AC | 交付物 | 实现/测试证据 | 结果 |
|------|-----|--------|---------------|------|
| **DATA-01** | AC-DATA-01 | `data_adapter_contract.md` structured 段 | `data_adapter_contract.md:46-66`；`test_dataAdapterContract_documentsStructuredSchemaHashRequirement` | PASS |
| **DATA-02** | AC-DATA-02 | CSV/Parquet 有界 infer + fetch 守卫 | `_infer_csv_schema_hash`（64KiB+header）；`_infer_parquet_schema_hash`（DuckDB DESCRIBE）；`test_inferSchemaHash_csvHeader_*` / `parquetColumns_*` | PASS |
| **DATA-03** | AC-DATA-03,05 | `DbValidationGate` fail-closed | `_schema_hash_blocks_write` L242-248（structured+SUCCESS+row_count>0+NULL hash → block）；`test_missingSchemaHashOnStructuredFetch_rejects`（csv/parquet/json）；`test_schemaHashDriftWithoutApproval_rejects` 回归 | PASS |
| **DATA-04** | AC-DATA-04 | 损坏文件负向 | `_fetch_impl` L183-202 → `SCHEMA_DRIFT`；`test_skeletonFetch_corruptCsv_*` / `corruptParquet_*` | PASS |

### validation_gate 核心逻辑（抽检）

```242:248:backend/app/db/validation_gate.py
        if (
            structured
            and str(status) == "SUCCESS"
            and int(row_count or 0) > 0
            and current_hash is None
        ):
            return True
```

### adapter schema_hash 守卫（抽检）

```182:202:backend/app/datasources/adapters/skeleton_base.py
        schema_hash = _infer_schema_hash(payload)
        if (
            payload.file_type in _STRUCTURED_FILE_TYPES
            and row_count > 0
            and schema_hash is None
        ):
            return FetchResult(
                ...
                status="SCHEMA_DRIFT",
```

### TDD / 负向证据（B3V-AUD-05）

| 步骤 | RED | GREEN |
|------|-----|-------|
| DATA-01 | `execute-evidence/9.1-red.txt` | `9.1-green.txt` |
| DATA-02 | `9.2-red.txt` — infer assert None | `9.2-green.txt` |
| DATA-03 | `9.3-red.txt` — `DID NOT RAISE ValidationRejected` | `9.3-green.txt` |
| DATA-04 | `9.4-red.txt` | `9.4-green.txt` |

---

## 5. GitNexus

| 动作 | 结果 |
|------|------|
| `query("schema_hash fail-closed ValidationGate")` | 命中 `proc_73_assert_can_write` → `_schema_hash_blocks_write` |
| `context("_schema_hash_blocks_write")` | 上游 `_enforce_report`；epistemic exact |
| 索引新鲜度 | **WARN**：索引行号滞后（示 L165-205 / `_infer_schema_hash` JSON-only 旧版）；工作区已扩展 CSV/Parquet。合并前建议 `node .gitnexus/run.cjs analyze` |

---

## 6. Findings

### BLOCKING

无。

### NON-BLOCKING

| ID | 位置 | 发现 |
|----|------|------|
| A1-N01 | `tests/conftest.py` vs `master` | +37 行 R3H/R3G 授权 bootstrap，非 B3V-DATA manifest 切片 |
| A1-N02 | ruff 宽作用域 | 51 项（多数既有测试 E501）；生产改动文件全绿 |
| A1-N03 | GitNexus | 符号行号滞后 |
| A1-N04 | `validation_gate.py:264-265` | baseline 缺失时 fail-open（首写场景；MASTER §2.2 未强制 block） |
| A1-N05 | `skeleton_base.py:57-59` | Parquet infer 写 temp 文件；受 `max_payload_bytes` 约束 |
| A1-N06 | Windows basetemp | 复用 `.audit-sandbox/pytest` 可能 `FileExistsError`；清目录或换 `--basetemp` 后缀可复现 |

**显式声明：** 对抗搜索完成；无 forbidden 文件改动；无削弱 B3V-AUD-05 负向测试目的；无 production clean write 路径。

---

## 7. A1 Checklist

- [x] trellis-check 步骤 1–7 有证据（§2）
- [x] diff vs audit/check manifest（`implement.jsonl` / `check.jsonl`）
- [x] Trace Authority 已继承或 explicit defer（B02-DATA-05）
- [x] 无 Plan omission（source-index / round map）
- [x] GitNexus 已 query + context（索引陈旧已注明）
- [x] Spec 与实现同步
- [x] 分支可审计交付物（`1bc0260d` + handoff 证据 commits）

---

## 8. 验证命令记录

```text
# A8 子集（AUDIT.plan §1）
uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest-a1
→ exit 0（106 passed）

# 生产文件 ruff
uv run ruff check backend/app/datasources/adapters/skeleton_base.py backend/app/db/validation_gate.py
→ exit 0

# Execute handoff
uv run python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/round3v-schema-hash-fail-closed
→ exit 0

# 分支事实
git log master..HEAD --oneline
→ 93815e00 chore(batch3v-data): execute handoff evidence...
→ d6971ad3 docs(batch3v-data): Plan QC PASS...
→ 44821ea6 docs(batch3v-data): Plan freeze evidence...
git merge-base --is-ancestor 1bc0260d HEAD
→ exit 0
```

---

## 9. 后续（非 A1 范围）

- A2–A8 由主会话按 `AUDIT.plan.md` 派发；registry 闭合（B02-DATA-05）归主会话。
- 全量 Audit PASS 须 A1–A8 矩阵齐；本维 **PASS**。
