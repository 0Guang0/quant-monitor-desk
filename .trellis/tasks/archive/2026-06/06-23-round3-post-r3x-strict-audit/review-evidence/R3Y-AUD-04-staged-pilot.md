# R3Y-AUD-04 — Real-data staged pilot 反证

**Result:** WARN

**审计基准：** `master` @ `61436a51`（review worktree 只读）  
**审计员：** PROMPT_18 `r3y-aud-04-staged-pilot`（security-auditor 视角）  
**日期：** 2026-06-23

---

## 目标与反证假设

验证 PROMPT_14 real-data staged pilot 在 runtime 是否满足：

1. **只写 raw / staging / sandbox**，不触达 production clean write 或 production DuckDB 写入路径。
2. **不可旁路** `DataSourceService` / `SourceRoutePlanner` / `WriteManager` / `DbValidationGate` / `ResourceGuard`。
3. **`production_db_no_mutation_proof`** 在四类情形下可信：DB **存在**、**缺失**、**schema-only 漂移**、**row-count-only 漂移**（含非 KEY 表）。

反证假设（若成立则 BLOCK）：

- staged pilot 可通过配置或代码路径写入 `DATA_ROOT/duckdb/quant_monitor.duckdb`。
- fetch 可不经 route/guard 直达 adapter 或 raw INSERT。
- `proof_status=VERIFIED` 可在 production 实际变异时仍被解读为「未变异」。

---

## 读取文件（含 call path 追溯）

| 层级       | 路径                                                                                                    | 作用                                                       |
| ---------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 编排入口   | `backend/app/ops/staged_pilot.py`                                                                       | 授权门禁、route preview、sandbox fetch、证据落盘           |
| 变异证明   | `backend/app/ops/mutation_proof.py`                                                                     | `key_table_row_counts` / `build_production_mutation_proof` |
| KEY 表集合 | `backend/app/ops/db_inspector.py` (`KEY_TABLES`)                                                        | no-mutation 行数快照范围                                   |
| 服务层     | `backend/app/datasources/service.py`                                                                    | `preview_route` / `fetch` / `check_resource_guard`         |
| 存储契约   | `backend/app/storage/staged_evidence.py`                                                                | `STAGED` quality_flag；文档说明 pilot 走 WriteManager      |
| Fetch 端口 | `backend/app/ops/staged_pilot_fetch_ports.py`                                                           | staged 专用 FetchPort（与 live 区分）                      |
| 测试       | `tests/test_staged_pilot.py`                                                                            | 26 项门禁与 mock 路径测试                                  |
| 派发说明   | `.trellis/tasks/06-23-round3-post-r3x-strict-audit/research/parallel-audit-dispatch.md`                 | AUD-04 范围与交付格式                                      |
| 任务卡     | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_post_r3x_strict_adversarial_audit.md` | 四类 proof 与 bypass 必答项                                |

### Runtime call path（live fetch 成功路径）

```
run_full_staged_pilot
  → capture_route_preview_matrix (dry_run, DataSourceService.preview_route + ResourceGuard)
  → capture_raw_and_staging_evidence
      → run_staged_pilot_raw_only
          → validate_authorization (raw_only, write_target=sandbox, allow_clean_write=false)
          → preview_staged_pilot (ResourceGuard via service.check_resource_guard)
          → _ensure_sandbox_db → ConnectionManager(sandbox_db)
          → DataSourceService(fetch_port=staged, route_planner=_ExplicitSourceRoutePlanner, data_root=sandbox)
          → service.fetch(con=sandbox) → ResourceGuard(con) 二次检查
          → _StagedPilotFileRegistry.register_on_connection → WriteManager.write(stg_file_registry)
          → _StagedPilotValidationGate.assert_can_write (metadata-only 窄豁免)
          → raw path is_relative_to(sandbox_root) 断言
          → build_production_mutation_proof(DEFAULT_PRODUCTION_DB, before_*)
  → capture_validation_report (结构校验 + declared_validators 引用，allow_clean_write=false)
```

---

## 核查方法（code trace + pytest）

### 代码追溯要点

**写入边界**

- `validate_authorization`（`staged_pilot.py:232-238`）强制 `raw_only=true`、`write_target=sandbox`、`allow_clean_write=false`。
- `run_staged_pilot_raw_only`（`744-758`）将 `ConnectionManager`、`data_root`、`file_registry` 全部绑定 sandbox；`DEFAULT_PRODUCTION_DB` 仅用于 `read_bytes` / `key_table_row_counts` 快照（`715-718`, `782-786`）。
- 成功 fetch 后对 `result.raw_file_paths` 做 `is_relative_to(sandbox_root)` 检查（`790-792`），路径逃逸则 `StagedPilotAuthorizationError`。
- `_StagedPilotFileRegistry` 写入 `stg_file_registry` + `quality_flag=STAGED`（`543-612`），经 `WriteManager`，非 production clean 表。

**旁路核查**

| 组件               | staged pilot 是否经过 | 备注                                                                                                                                                                                           |
| ------------------ | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DataSourceService  | ✅                    | preview + fetch 均构造 `DataSourceService`                                                                                                                                                     |
| SourceRoutePlanner | ✅                    | `_ExplicitSourceRoutePlanner` 包装内层 planner                                                                                                                                                 |
| WriteManager       | ✅                    | `_StagedPilotFileRegistry` → `write_manager.write`；测试 `test_stagedPilot_mockFetchSuccess_usesWriteManagerStagedQualityFlag` 覆盖                                                            |
| DbValidationGate   | ⚠️ 窄豁免             | `_StagedPilotValidationGate`（`620-660`）在 `can_write_clean=false` 且 `quality_flags=staged_raw_metadata_only` 时允许 `append_only` 写 staging；仅 sandbox con                                |
| ResourceGuard      | ✅                    | preview：`service.check_resource_guard`（`388-390`）；fetch：`DataSourceService.fetch` 内 `ResourceGuard(con=con).check()`（`service.py:160-174`）；full pilot 另写 `resource_guard_caps.json` |

**未实际执行的「声明型」校验**

- `capture_validation_report`（`1014-1132`）对 raw JSON 做轻量结构检查，**不调用** `DataQualityValidator` / `SourceConflictValidator` 运行时；仅在 payload 中 `declared_validators` 引用契约路径（`sandbox_validation_note` 已说明）。
- `_staged_conflict_check_summary` 显式 `NO_CONFLICT_CHECK_DEFERRED`（单源 micro-fetch 策略）。

**no-mutation proof 四类情形**

| 情形                                               | 实现行为                                                                                                                                          | 测试覆盖                                                                         |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| DB **缺失**                                        | `proof_status=INCONCLUSIVE`，`db_hash_unchanged`/`row_counts_unchanged`=None（`mutation_proof.py:54-63`）                                         | ✅ `test_stagedPilot_mutationProof_inconclusiveWhenProductionDbMissing`          |
| DB **存在**且未变异                                | `proof_status=VERIFIED`，比较 before/after 全文件 hash + `KEY_TABLES` 行数                                                                        | ✅ `test_stagedPilot_captureRouteMatrix_writesEvidenceAndNoMutation`（条件断言） |
| **schema-only** 漂移（非 KEY 表 DDL / 元数据变更） | 全文件 `read_bytes` 比较通常可捕获；但若仅 KEY 表内「行数不变」的 in-place 更新则 hash 可能变而 `row_counts_unchanged` 仍为 true                  | ❌ 无对抗测试                                                                    |
| **row-count-only**（非 `KEY_TABLES` 表增删行）     | `key_table_row_counts` 只扫 `KEY_TABLES`（`db_inspector.py:14-29`）；非 KEY 表变异可使 `row_counts_unchanged=true` 同时 `db_hash_unchanged=false` | ❌ 无对抗测试；且 `proof_status` 仍为 `VERIFIED`                                 |

### pytest 命令与结果

```bash
cd C:\Users\Guang\Desktop\quant-monitor-desk-wt-review-r3-post-r3x-strict-audit
uv run pytest tests/test_staged_pilot.py -q
```

```
..........................                                               [100%]
EXIT:0
```

**26 passed，0 failed。**

---

## Findings

### [HIGH] `proof_status=VERIFIED` 不表示 production 未变异

- **Location:** `backend/app/ops/mutation_proof.py:74-81`
- **Description:** 只要 production DB **文件存在**，`build_production_mutation_proof` 固定返回 `proof_status: "VERIFIED"`，无论 `db_hash_unchanged` / `row_counts_unchanged` 是否为 `False`。
- **Impact:** `run_full_staged_pilot` closeout 的 `mutation_proof_status` 仅取自 `proof_status`（`staged_pilot.py:1207-1220`），叙事可写「mutation proof is VERIFIED」而实际 hash 或行数已变；自动化 gate 若只读 `proof_status` 会**假阴性**。
- **Proof of concept:** 对存在库调用 `build_production_mutation_proof(db, before_counts={...}, before_bytes=old_bytes)`，在另一进程修改 DB 后同一函数仍返回 `VERIFIED` + `db_hash_unchanged=False`。
- **Recommendation:** 将 `proof_status` 语义收紧为：`VERIFIED` 仅当 hash 与 counts 均为 true；否则 `MUTATION_DETECTED` 或 `INCONCLUSIVE`。closeout 应同时输出 `db_hash_unchanged` / `row_counts_unchanged` 作为 gate 条件。

### [WARN] 四类 no-mutation proof 仅「缺失库」有对抗覆盖

- **Location:** `tests/test_staged_pilot.py`（仅 `test_stagedPilot_mutationProof_inconclusiveWhenProductionDbMissing`）；`mutation_proof.py:14-37`（KEY 表范围）
- **Description:** schema-only / 非 KEY 表 row-count / KEY 表 in-place 更新等 adversarial 场景**无**失败路径测试。`capture_route_preview_matrix` 测试在 `VERIFIED` 分支才断言 `row_counts_unchanged is True`，从不构造「检测到变异」样本。
- **Impact:** 无法证明 proof 机制能**可靠拒绝**弱证据；row-count-only 在非 KEY 表上可能 `row_counts_unchanged=true`（误导性安全信号）。
- **Recommendation:** 增加合成 DuckDB fixture：`(a)` 改 `KEY_TABLES` 外表行数；`(b)` 同 KEY 表 hash 变、count 不变；`(c)` 断言期望的 `proof_status` 与 gate 行为。

### [WARN] ValidationGate 刻意窄豁免 + validation 阶段未跑完整 validator

- **Location:** `staged_pilot.py:620-660` (`_StagedPilotValidationGate`)；`663-692` (`_ensure_raw_validation_report` 直接 INSERT)；`1014-1093` (`capture_validation_report`)
- **Description:** sandbox 上通过 stub `validation_report`（`can_write_clean=false`）+ 子类 gate 允许 `stg_file_registry` append；validation 报告阶段仅结构 JSON 检查，DQV/冲突校验为**声明引用**。
- **Impact:** 不是 production bypass（sandbox con 隔离），但若误将 staged PASS 等同于「已通过 DataQualityValidator / SourceConflictValidator」，会高估数据质量与冲突安全。
- **Recommendation:** 证据与 closeout 明确区分「sandbox STAGED metadata write」与「clean-write-ready validation」；pilot v2 前不得提升 `allow_clean_write`。

### [INFO] 正面：sandbox 写入边界与授权 fail-closed 扎实

- **Location:** `staged_pilot.py:201-260`, `790-792`, `433-438`（fixture port 禁止）
- **Description:** 授权文件名/信封/禁用源/网络预算/expanded envelope 均有硬门禁；fixture `StubFetchPort`/`LocalFixtureFetchPort` 被 `_assert_real_fetch_port` 拒绝。

---

## 反证结论（修复是否进入 runtime）

| 主张                                                 | 反证结果                                                                                                                     |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 只写 raw/staging/sandbox                             | **成立** — production DB 无写连接；raw 路径 sandbox 相对性检查；`allow_clean_write=false` 全链路                             |
| 旁路 DataSourceService / RoutePlanner / WriteManager | **不成立** — live fetch 必经三者；有 mock 测试证据                                                                           |
| 旁路 ResourceGuard                                   | **不成立** — preview + fetch 双检查                                                                                          |
| 旁路 ValidationGate（production clean write）        | **不成立** — clean write 未启用；sandbox 有 intentional 窄豁免                                                               |
| no-mutation proof 四类均可信                         | **部分成立** — 缺失→INCONCLUSIVE 可信；存在→依赖子字段；schema-only / row-count-only **未对抗验证**；`proof_status` 语义过宽 |

**总结：** PROMPT_14 staged pilot 的 **sandbox 隔离与主链路集成**已进入 runtime 且测试较全；**production no-mutation 证明的 gate 语义与对抗深度不足**，不足以单独支撑「production 绝对未变异」的强声明。

---

## 阻塞项 / 建议

### 阻塞项（AUD-08 合成时）

- 无 **BLOCK** 级 production 写入旁路。
- **WARN 累积项：** `proof_status` 语义 + 缺失 adversarial mutation 测试 — 建议在 staged pilot v2 / data health v1 go/no-go 中列为**显式控制项**（非单独 BLOCK，但不得忽略子字段）。

### 建议下一步

1. 收紧 `build_production_mutation_proof` 的 `proof_status` 与 closeout gate 字段。
2. 为 schema-only / non-KEY row-count / hash-changed 场景补 3 条对抗测试（可放在 `test_staged_pilot.py` 或 `test_mutation_proof.py`）。
3. pilot v2 扩展样本前：保持 `allow_clean_write=false`；冲突检查 defer 需在 registry 签收后再启用多源 compare。
4. 证据消费者必须同时检查 `db_hash_unchanged` **与** `row_counts_unchanged`，不可仅读 `proof_status`。

---

## 三条关键 Finding（摘要）

1. **`proof_status=VERIFIED` 在 DB 存在时恒为 VERIFIED**，即使 `db_hash_unchanged`/`row_counts_unchanged` 为 false；closeout 叙事存在假安全窗口（`mutation_proof.py:76`, `staged_pilot.py:1207`）。
2. **production 写入旁路未发现**：fetch 经 `DataSourceService`+sandbox `ConnectionManager`+`WriteManager`+双次 `ResourceGuard`；授权与 sandbox 路径检查 fail-closed（`staged_pilot.py:695-792`）。
3. **四类 no-mutation proof 仅「DB 缺失→INCONCLUSIVE」有测试**；schema-only / 非 KEY 表 row-count drift 无对抗覆盖，`KEY_TABLES` 范围留下 row-count-only 盲区（`mutation_proof.py:31-36`, `db_inspector.py:14-29`）。

---

_v0 单 agent 浅表结论见 `review-evidence/v0-monolithic/R3Y-AUD-04-staged-pilot.md`（WARN，本报告为加深版）。_
