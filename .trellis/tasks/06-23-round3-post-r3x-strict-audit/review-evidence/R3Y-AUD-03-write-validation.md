# R3Y-AUD-03 — Write / Validation / Conflict 反证

**Result:** WARN

## 目标与反证假设

验证 PROMPT_13 / R3X db-write-validation 修复是否进入 **runtime path**：

1. **clean write**（`file_registry` 以外 clean 表、sync orchestrator、Layer1 Phase 4 commit）是否必经 `WriteManager` + `DbValidationGate`？
2. **severe conflict**（`source_conflict.severity=severe` 且 `reconcile_status IN (OPEN, UNRESOLVED)`）是否在 gate 层阻断 clean write？
3. **staged evidence** 是否仍存在可绕过 `WriteManager` / `validation_report` 的旁路？
4. **reconcile** 路径是否在不经过完整 validation gate 的情况下写入 clean 表？

反证假设：若存在未文档化的 `INSERT INTO` clean 表、或 `StubValidationGate` 进入生产、或 reconcile 裸 `adapter.fetch` 后直写 clean，则 BLOCK。

## 读取文件（含 call path 追溯）

| 层级 | 文件 | 作用 |
|------|------|------|
| Gate | `backend/app/db/validation_gate.py` | `DbValidationGate` / `StubValidationGate` |
| Write | `backend/app/db/write_manager.py` | 唯一标准写入口；L309 `gate.assert_can_write` |
| Pipeline | `backend/app/sync/pipeline.py` | `SyncWritePipeline` → `WriteManager` + `DbValidationGate` |
| Sync | `backend/app/sync/runners.py` | `_finalize_staged` → `_write_clean`；`ReconcileJobRunner.run` |
| Storage | `backend/app/storage/file_registry.py` | `FileRegistry.register_on_connection` → `write_manager.write` |
| Storage bypass | `backend/app/storage/staged_evidence.py` | `register_staged_file_registry_rows` 裸 `INSERT` |
| Layer1 | `backend/app/layer1_axes/ingestion.py` | Phase 3 `_register_clean_file_registry_rows`；Phase 4 `ingestion_commit.py` |
| Staged pilot | `backend/app/ops/staged_pilot.py` | `_StagedPilotValidationGate`、`_StagedPilotFileRegistry` |
| 契约 | `docs/modules/write_manager.md` §4 | clean 写入须经 WriteManager |
| Blocker 卡 | `docs/.../R3X_db_write_validation_blockers.md` | ADV-A1-004 等闭合声明 |
| Merge evidence | `.trellis/tasks/fix-round3-db-write-validation-blockers/execute-evidence/merge_gate_report.md` | |
| Tests | `tests/test_db_validation_gate.py` `test_write_manager.py` `test_raw_store.py` `test_sync_orchestrator.py` `test_layer1_observation_ingestion.py` | |

**Call graph 摘要（clean write 主路径）：**

```text
IncrementalJobRunner / BackfillShardRunner
  → _finalize_staged (runners.py:232)
    → SyncValidationPipeline.validate_staging (quality + optional conflict)
    → if SEVERE_CONFLICT → WAITING_RECONCILE (no _write_clean)
    → SyncWritePipeline.write_clean (pipeline.py:75)
      → WriteManager.write → DbValidationGate.assert_can_write → MERGE/INSERT clean

Layer1 commit_clean_observation_and_snapshots (ingestion_commit.py)
  → DataQualityValidator + SourceConflictValidator (pre-write)
  → Layer1*Writer (each holds WriteManager + DbValidationGate)
  → DbValidationGate also blocks open severe conflicts at write time
```

## 核查方法（code trace + pytest 命令与结果）

### 静态 trace

```bash
# 全 backend 唯一绕过 WriteManager 写 file_registry 的路径
rg -n "INSERT INTO file_registry" backend/
# → 仅 staged_evidence.py:71

# production 代码对 register_staged_file_registry_rows 的 import
rg -n "register_staged_file_registry_rows" backend/
# → 仅 staged_evidence.py 定义；无其他 backend 调用方

# WriteManager 构造时 gate 必填
rg -n "WriteManager\(" backend/ 
# → 均注入 DbValidationGate 或 _StagedPilotValidationGate（staged_pilot）；测试用 Stub 仅在 tests/

# reconcile 裸 fetch
rg -n "adapter\.fetch" backend/app/sync/runners.py
# → L63 _fetch_with_guard（incremental/backfill 经 guard）；L868 ReconcileJobRunner 直接调用
```

### DOUBT 三类威胁（A3 基线）

| 类别 | 范围 | 结论 |
|------|------|------|
| 硬编码 URL / 密钥 | `backend/` 非测试 | 无发现；`error_redaction.py` 含 redact 模式 |
| SQL 拼接注入 | `backend/app/db/` `storage/` `sync/` | `write_manager` / `file_registry` 使用 `quote_ident`；staging 表名为内部 uuid 前缀；reconcile `compare_table` 来自 `conflict_id[:8]`（UUID 片段，非用户输入） |
| `subprocess`/`eval` | `backend/app/db/` | 无发现 |

### 必跑 pytest

```bash
cd quant-monitor-desk-wt-review-r3-post-r3x-strict-audit
uv run pytest tests/test_db_validation_gate.py tests/test_write_manager.py tests/test_raw_store.py -q
```

**结果：** exit 0，**54 passed**（12 + 22 + 20）。

关键用例覆盖：

- `test_openSevereConflict_rejectsEvenWhenReportPassed` — severe OPEN 阻断 gate
- `test_writeManager_withoutGate_raisesValueError` — 无 gate 拒绝构造
- `test_dbValidationGate_writeManagerIntegration_rejectsFailed` — WM+DbGate 集成
- `test_stagedEvidence_pathEscape_rejected` — ADV-A1-004 路径逃逸
- `test_register_validationRejected_persistsFailedAudit` — 失败审计

## Findings

### [HIGH] `register_staged_file_registry_rows` 仍为可调用 WriteManager 旁路（无生产调用方，回归面未消除）

- **Location:** `backend/app/storage/staged_evidence.py:34-92`
- **Description:** 全仓库唯一的 `INSERT INTO file_registry` 裸写路径；注释标明「Documented staging exception: bypasses WriteManager」。`rg` 显示 **backend 无 import 调用方**（Layer1 Phase 3 已改走 `_register_clean_file_registry_rows` → `FileRegistry` + `WriteManager`）；仅 `tests/test_raw_store.py`、`tests/test_r3x_ponytail_pilot_prep_bucket_a.py` 直接调用。
- **Impact:** 当前 runtime 未走此路径，但 API 仍公开；未来接线或 copy-paste 可瞬间恢复无 audit / 无 gate 的 `file_registry` 写入，违反 `write_manager.md` §1「任何 clean 表写入必须经过 WriteManager」精神（`file_registry` 为索引 clean 表）。
- **Proof of concept:** 测试中 `register_staged_file_registry_rows(con, result, data_root=...)` 可在无 `validation_report`、无 `write_audit_log` 的情况下插入 `quality_flag=STAGED` 行（`test_stagedEvidence_allowedPath_registersRow`）。
- **Recommendation:** 将函数降为 `_` 私有并限制 `tests` 导入，或加 `warnings.warn` + 运行时 `raise NotImplementedError` 除非 `QMD_ALLOW_STAGED_BYPASS=1`；长期删除并由 `FileRegistry` + metadata-only gate 统一。

### [WARN] ReconcileJobRunner 裸 `adapter.fetch` 不经 DataSourceService / RoutePlanner

- **Location:** `backend/app/sync/runners.py:859-868`
- **Description:** `ReconcileJobRunner.run` 构造 `FetchRequest` 后直接 `adapter.fetch(req, con=con, job_id=job_id)`，未经过 `DataSourceService.fetch`（无 route plan、capability 矩阵、disabled-source fail-closed）。对比：incremental/backfill 经 `_fetch_with_guard`（L42-74），仍可能裸 adapter，但至少统一 guard + fetch_log。
- **Impact:** reconcile re-fetch **不写 clean 表**（仅 staging compare + `source_conflict` UPDATE），故 **不绕过 ValidationGate 写 clean**；但若传入错误/未授权 adapter，可触发非预期源拉取（与 R3Y-AUD-02 交叉）。
- **Proof of concept:** `orch.run_reconcile(conflict_id, adapter=_BackfillCountAdapter())`（`test_sync_orchestrator.py:597`）—— adapter 由调用方注入，无 registry 路由校验。
- **Recommendation:** reconcile fetch 改经 `DataSourceService.fetch` 或至少 `SourceRegistry.get` + capability 校验；文档化「reconcile adapter 必须由 orchestrator 从 conflict 行 `competing_source` 解析」。

### [WARN] Metadata-only `file_registry` 写入使用弱化 synthetic validation_report（非 full DQ）

- **Location:** `backend/app/layer1_axes/ingestion.py:110-147` + `ingestion.py:501-518`；`backend/app/ops/staged_pilot.py:620-660`（`_StagedPilotValidationGate`）
- **Description:**
  - Layer1 Phase 3：`_ensure_staged_file_registry_validation_report` 插入 `can_write_clean=True`、`quality_flags='staged_file_registry_metadata_only'`，再经 `DbValidationGate` + `WriteManager` 写 `file_registry`。
  - `DbValidationGate._SYNTHETIC_QUALITY_MARKERS`（`validation_gate.py:79-81`）仅含 `raw_file_registry_metadata_only`，**不含** `staged_file_registry_metadata_only` / `staged_raw_metadata_only`，故 synthetic 标记依赖 `can_write_clean` 字段而非 quality_flags 阻断。
  - Staged pilot 使用 `_StagedPilotValidationGate` 子类，在 `can_write_clean=false` + `staged_raw_metadata_only` 时 **显式放行** metadata append（`staged_pilot.py:645-655`）。
- **Impact:** 设计意图为「metadata-only 不得触发 full clean write」；实际 **仍写 DB `file_registry`**（经 WriteManager + audit），但 **未经 DataQualityValidator 全量规则**。与 `DbValidationGate` 对 `raw_file_registry_metadata_only` 的阻断策略 **不一致**，增加误配置风险。
- **Recommendation:** 统一 synthetic marker 枚举；Layer1 与 staged_pilot 共用同一 metadata-only report 工厂；`can_write_clean=false` + 白名单 quality_flag 作为唯一放行条件（与 `_StagedPilotValidationGate` 对齐）。

### [INFO] Clean 表直写扫描无额外旁路

- **Location:** `rg "INSERT INTO (security_bar|axis_observation|cross_asset)" backend/` → 无匹配
- **Description:** sync/Layer1/Layer2 writer 均 staging → `WriteManager.write`。
- **Impact:** 无。
- **Recommendation:** 保持 CI grep invariant。

### [INFO] Severe conflict 阻断 — runtime + 测试双证

- **Location:** `validation_gate.py:122-147,243-247`；`runners.py:270-277`；`ingestion_commit.py:229-233`
- **Description:** Gate 按 `run_id`/`job_id` 查 OPEN/UNRESOLVED severe；orchestrator 在 `_write_clean` 前返回 `WAITING_RECONCILE`；Layer1 commit 前置 conflict 检查 + write 时 DbGate 二次阻断。
- **Impact:** 正面；`test_openSevereConflict_rejectsEvenWhenReportPassed`、`test_backfillJob_severeConflict_blocksCleanWrite`、`test_layer1Observation_severeConflict_blocksCleanWrite` 通过。
- **Recommendation:** 无。

## 反证结论（修复是否进入 runtime）

| 声称 | 反证结果 | 证据 |
|------|----------|------|
| clean table 仅经 WriteManager | **PASS**（主路径） | `SyncWritePipeline`、`FileRegistry`、Layer1/2 writers；无 clean 表裸 INSERT |
| DbValidationGate 执行 write_contract 拒绝条件 | **PASS** | failed/can_write_clean/manual_review/schema_drift/severe — 均有测试 |
| severe conflict 阻断 clean write | **PASS** | gate + orchestrator 双检查；54 pytest 含 severe 用例 |
| staged_evidence 路径逃逸修复 (ADV-A1-004) | **PASS** | `_resolve_under_data_root` + `test_stagedEvidence_pathEscape_rejected` |
| staged_evidence WriteManager 旁路消除 | **WARN** | 函数仍存在、测试仍调用；生产 backend 无 caller |
| backfill severe 后继续写 | **PASS**（已修） | `_finalize_staged` L270-277 |
| reconcile 不经 ValidationGate 写 clean | **PASS**（不写 clean） | reconcile 仅 UPDATE `source_conflict` + staging compare |
| reconcile fetch 经 source route | **WARN** | 裸 `adapter.fetch` L868 |

**总结：** PROMPT_13 核心修复（`DbValidationGate`、`WriteManager` 强制 gate、severe 阻断、路径 containment）**已进入 sync / Layer1 commit / FileRegistry 主路径**。残留风险为 **文档化但未退役的 `register_staged_file_registry_rows` 旁路 API**、**metadata-only gate 策略分裂**、**reconcile fetch 不经 DataSourceService**（不写 clean，属授权/路由面）。

## 阻塞项 / 建议

| 优先级 | 项 | 阻塞 pilot v2? |
|--------|-----|----------------|
| P1 | 删除或硬门禁 `register_staged_file_registry_rows` | 建议修，非硬 BLOCK（当前无生产 caller） |
| P2 | 统一 synthetic metadata quality_flags + gate 子类策略 | WARN 管控即可 |
| P2 | Reconcile fetch 接入 DataSourceService（与 AUD-02 联动） | WARN |
| — | Severe conflict / WM+Gate 主路径 | 不阻塞 |

**建议下一步：** 允许 sandbox clean-write rehearsal **附带控件**：禁止新代码 import `register_staged_file_registry_rows`；staged pilot 继续仅用 `_StagedPilotValidationGate`；reconcile 任务卡注明 adapter 来源约束。

---

## Security Audit Report（A3 摘要）

### Summary

- Critical: 0
- High: 1
- Medium: 0
- Low: 2
- Info: 2

### Positive Observations

- `WriteManager.__init__` 拒绝 `gate=None`（`write_manager.py:60-64`）。
- `DbValidationGate` 非 stub：拒绝未知 report、stub 前缀无 DB 行时失败（`test_dbValidationGate_isNotStubBehavior`）。
- 失败写路径保留 `write_audit_log` + optional sidecar（`write_manager.py:217-275`）。
- `FileRegistry` 全路径经 `WriteManager`；`RawStore` 测试验证 validation reject 不留行。

### Recommendations

1. 加 `scripts/check_write_bypass.py` 或扩展现有 loop CI：fail on `INSERT INTO file_registry` outside migrations。
2. 将 `_StagedPilotValidationGate` 行为写入 `docs/modules/data_validation_and_conflict.md` 作为唯一 metadata-only 例外表。
3. Reconcile 与 AUD-02 合并修复 source route。

---

*审计 agent: R3Y-AUD-03 · worktree `quant-monitor-desk-wt-review-r3-post-r3x-strict-audit` · 基准 master @ 61436a51 · 只读*
