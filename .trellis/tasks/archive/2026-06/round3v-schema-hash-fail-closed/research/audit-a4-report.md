# A4 audit-quality — B3V-DATA schema_hash fail-closed

> Dimension: Code Quality (A4 only)  
> Scope: 任务实现 `1bc0260d`（Repair 后 HEAD）+ 分支 `master...HEAD` 增量  
> Worktree: `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-data`  
> Branch: `fix/round3v-schema-hash-fail-closed`  
> Skills: `code-review-and-quality` + `doubt-driven-development`  
> Authority: `agents/code-reviewer.md` · `agents/audit-adversarial-authority.md` · `AUDIT.plan.md`  
> Mode: **只读**（无代码修复）

---

## Verdict: **PASS**

实现与 `data_adapter_contract.md` VR-DATA-001 段、`B02_02` §2–§6 语义一致：adapter 层对 json/csv/parquet 在 `SUCCESS`+`row_count>0` 时强制非空 `schema_hash`，推导失败返回 `SCHEMA_DRIFT`；ValidationGate 对结构化 fetch（路径后缀 **或** `file_registry` 回退）且缺 hash 的 `fetch_log` 行 fail-closed。Repair `1bc0260d` 已补齐三后缀 parametrize 与 registry 回退单测（原 A4-06/G-01/G-03）。无 P0 逻辑/安全阻塞；下列为 NON-BLOCKING 计划外缺口与可维护性建议。

---

## 审查范围

### 任务实现（`1bc0260d` · 已在 HEAD 祖先链）

| 文件                                                | 变更摘要                                                                  |
| --------------------------------------------------- | ------------------------------------------------------------------------- |
| `backend/app/datasources/adapters/skeleton_base.py` | CSV/Parquet 有界 `_infer_schema_hash`；结构化缺 hash → `SCHEMA_DRIFT`     |
| `backend/app/db/validation_gate.py`                 | `_fetch_log_is_structured` + `_schema_hash_blocks_write` fail-closed 分支 |
| `specs/contracts/data_adapter_contract.md`          | Structured schema_hash 契约段                                             |
| `tests/test_adapter_skeletons.py`                   | CSV/Parquet 推导 + 损坏文件负向                                           |
| `tests/test_data_adapter_contract.py`               | 契约文档冻结断言                                                          |
| `tests/test_db_validation_gate.py`                  | 缺 hash 结构化 fetch（三后缀 parametrize）+ registry 回退                 |

### 分支增量（`master...HEAD` · 非核心逻辑）

| 文件                                                | 变更摘要                              | A4 判定                                      |
| --------------------------------------------------- | ------------------------------------- | -------------------------------------------- |
| `.trellis/tasks/round3v-schema-hash-fail-closed/**` | Plan/Execute 证据与 QC 文档           | 任务元数据，无运行时影响                     |
| `tests/conftest.py`                                 | R3H-04 / R3G fred 授权 YAML bootstrap | **计划外** 全库卫生；与 schema_hash 逻辑无关 |

---

## 轴评分（1–5）

| 轴             | 分  | 理由                                                                                      |
| -------------- | --- | ----------------------------------------------------------------------------------------- |
| Correctness    | 5   | 主路径（adapter + gate 后缀/registry 回退）正确；Repair 闭合原 G-01/G-03 测试缺口         |
| Readability    | 4   | `_canonical_schema_hash` 抽取合理；`job_id` 形参仍未使用（A4-03）                         |
| Architecture   | 4   | Layer1 adapter / Layer4 gate 分工符合 Playbook；`_STRUCTURED_FILE_TYPES` 双模块重复可接受 |
| Error handling | 4   | infer 失败统一 `None` → adapter `SCHEMA_DRIFT`；parquet temp 文件 `finally` 清理完整      |
| Test quality   | 5   | 五字段齐全、负向未削弱；Repair 后 gate 三后缀 + registry 回退均有单测                     |

---

## §3.4 发现表

| 轴               | ID    | 发现                                                                                                                                                                                                        | 阻塞?        | 证据                                                                 |
| ---------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------------------------------------------------------------------- |
| Correctness      | A4-01 | Gate 仅在能分类为 structured（路径后缀 **或** `file_registry` 有 structured 行）时 fail-closed；无后缀且 source 无 structured `file_registry` 历史时，`current_hash is None` 走 `return False`（fail-open） | NON-BLOCKING | `validation_gate.py:249-250`；契约 defer registry 闭合至 B02-DATA-05 |
| Correctness      | A4-02 | `_fetch_log_is_structured` 的 `file_registry` 回退按 `source_id` 全局 `ORDER BY fetch_time DESC LIMIT 1`，未与 `job_id`/当前 fetch 关联；可能把历史 structured 误判为当前 fetch 类型（偏向 fail-closed）    | NON-BLOCKING | `validation_gate.py:195-206`                                         |
| Maintainability  | A4-03 | `_fetch_log_is_structured(..., job_id=...)` 形参 `job_id` 未使用，易误导后续维护者                                                                                                                          | NON-BLOCKING | `validation_gate.py:183-190`                                         |
| Error handling   | A4-04 | CSV 推导仅 UTF-8；合法非 UTF-8 表头会 infer 失败 → `SCHEMA_DRIFT`（fail-closed，符合契约「推导失败不得 SUCCESS」）                                                                                          | NON-BLOCKING | `skeleton_base.py:38-43`                                             |
| Resource / I/O   | A4-05 | Parquet 推导将完整 payload 写入 `mkstemp` 临时文件（上限受 `DEFAULT_MAX_PAYLOAD_BYTES=10MB` 约束）；契约写「LIMIT 0 语义」而实现为落盘 + `DESCRIBE`                                                         | NON-BLOCKING | `skeleton_base.py:56-82`；符合 MASTER §0.3a Ponytail                 |
| Defense-in-depth | A4-08 | `FetchLogWriter._validate_for_persist` 不校验 structured+SUCCESS+hash；非 skeleton 直写 `fetch_log` 可绕过 adapter 守卫（OP-01）                                                                            | NON-BLOCKING | `fetch_log.py:44-55`；RE-DEFER → B02-DATA-05                         |
| Test             | A4-07 | `test_dataAdapterContract_documentsStructuredSchemaHashRequirement` 为契约字符串存在性检查，不验证运行时行为（对 AC-DATA-01 文档冻结足够）                                                                  | NON-BLOCKING | `tests/test_data_adapter_contract.py:810-826`                        |
| Scope hygiene    | A4-09 | 分支 `conftest.py` 新增 R3H/R3G 授权 bootstrap，超出 B3V-DATA allowed files；无 schema_hash 行为变更                                                                                                        | NON-BLOCKING | `tests/conftest.py:39-40,55-88`                                      |

**Repair 已闭合（本轮不再列为 OPEN）：**

| 原 ID        | 修复                    | 证据                                                                                     |
| ------------ | ----------------------- | ---------------------------------------------------------------------------------------- |
| A4-06 / G-01 | Gate 三后缀 parametrize | `test_missingSchemaHashOnStructuredFetch_rejects` · `test_db_validation_gate.py:258-301` |
| G-03         | registry 回退单测       | `test_missingSchemaHash_registryFallback_rejects` · `test_db_validation_gate.py:304-349` |

---

## 计划外发现

| ID    | 场景                                                                                                                      | 若只按 MASTER §5.3 测会漏什么              | 严重度       | 处置                      |
| ----- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | ------------ | ------------------------- |
| OP-01 | 非 skeleton 路径写入 `fetch_log`：`SUCCESS`+`row_count>0`+`schema_hash=NULL`，无结构化后缀且无 structured `file_registry` | Gate 不拦截 clean-write                    | NON-BLOCKING | RE-DEFER → B02-DATA-05    |
| OP-02 | 同 source 先 structured 后 schemaless：`raw_file_paths` 为空时 gate 可能仍因历史 `file_registry` 判 structured            | 误拒 schemaless 写入（fail-closed 偏安全） | NON-BLOCKING | ACCEPTED                  |
| OP-03 | Parquet 损坏测试断言 `FAILED` 或 `SCHEMA_DRIFT` 均可，adapter 实现固定返回 `SCHEMA_DRIFT`                                 | 无功能缺口；断言略宽                       | 信息性       | WONT-FIX                  |
| OP-04 | `conftest.py` 全库 bootstrap 与 B3V-DATA 任务卡 allowed files 不一致                                                      | 合并时可能引入无关 diff 噪音               | NON-BLOCKING | 主会话合并前可拆分 commit |

**对抗搜索声明：** 已对照 `1bc0260d` diff、`B02_02` §4 forbidden、`data_adapter_contract.md` VR-DATA-001 段、`validation_gate._schema_hash_blocks_write` 全分支、adapter `_fetch_impl` 成功/失败路径、`FetchLogWriter._validate_for_persist`、生产 adapter 继承链（全部 7 个 vendor adapter → `SkeletonAdapterBase`）、三测试文件新增/修复用例及 `master...HEAD` 分支增量。

---

## DOUBT（对抗性）

| Claim                                        | Attack                                                        | Result                                                             |
| -------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------ |
| 「结构化 SUCCESS 绝不能缺 schema_hash 写库」 | Adapter 已拦；Gate 后缀+registry 启发式                       | **主路径成立** — OP-01/A4-08 为 defense-in-depth 缺口，已 RE-DEFER |
| 「损坏 CSV/Parquet 不会 SUCCESS」            | `test_skeletonFetch_corrupt*` + infer `None` → `SCHEMA_DRIFT` | **成立**                                                           |
| 「schema_hash 漂移仍拒绝」                   | 既有 `test_schemaHashDriftWithoutApproval_rejects` 未改       | **成立**                                                           |
| 「有界推导不全文件扫描」                     | CSV 64KiB 前缀；Parquet 落盘整文件但 ≤10MB payload cap        | **成立**（A6 本任务 SKIP）                                         |
| 「Repair 削弱 B3V-AUD-05」                   | diff 审查：仅 additive 负向                                   | **不成立**                                                         |

**必选 DOUBT 结论（file:line）：** `fetch_log.py:44-55` — `_validate_for_persist` 仅校验 status/row_count/必填字段，**不**拦截 structured+SUCCESS+NULL `schema_hash`；与 adapter 层 fail-closed 形成不对称。生产主路径经 `SkeletonAdapterBase` 已闭合；旁路写入属已知 defer 窗口（OP-01），建议 B02-DATA-05 或 FetchLogWriter 加固时一并处理。

---

## Checklist（code-reviewer.md）

- [x] 无 P0 逻辑/安全阻塞
- [x] 错误处理可观测（`error_message="structured fetch missing schema_hash"`；gate `ValidationRejected` match schema_hash）
- [x] 风格与邻近模块一致（复用 `_shape`、stdlib csv、既有 DuckDB 模式）
- [x] 测试变更保留 purpose（中文五字段）
- [x] 判定基于 diff 与 pytest，非覆盖率 KPI

---

## 验证结果

| 检查        | 命令                                                                                                                                                                 | 结果                            |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| Pytest 子集 | `uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest-a4-20260628` | **PASS**（106 passed · exit 0） |
| Ruff        | `uv run ruff check backend/app/datasources/adapters/skeleton_base.py backend/app/db/validation_gate.py`                                                              | **All checks passed**           |

> 注：复用已占用的 `.audit-sandbox/pytest` 在 Windows 上可能因 DuckDB lock 导致 teardown `PermissionError`；审计使用独立 basetemp 路径规避。

---

## 做得好的地方

- `_canonical_schema_hash` 消除 JSON/CSV/Parquet 三处重复 canonical 逻辑，符合 ponytail「删重复」。
- Adapter 在 raw 已落盘后才判 `SCHEMA_DRIFT`，保留 `raw_file_paths`/`content_hash` 证据链。
- Gate 新分支在 `current_hash is None` 之前先检查 structured+SUCCESS+row_count，不破坏既有 schemaless 放行。
- Repair 补齐三后缀 parametrize 与 registry 回退单测，闭合首轮 A4-06/G-03 缺口。
- 损坏文件负向测试接受 `FAILED|SCHEMA_DRIFT`，未削弱 B3V-AUD-05 意图。
- 契约段与实现推导边界（64KiB CSV、Parquet DESCRIBE）对齐。

---

## A4 门控结论

| 项            | 值                                                                                                      |
| ------------- | ------------------------------------------------------------------------------------------------------- |
| 维度          | A4 Code Quality                                                                                         |
| 结论          | **PASS**                                                                                                |
| BLOCKING 计数 | 0                                                                                                       |
| OPEN 计数     | 0（NON-BLOCKING 已 disposition）                                                                        |
| 建议跟进      | A4-01/08 → B02-DATA-05；A4-03 删除未用 `job_id` 或实现 job 级关联；A4-09 合并前考虑拆分 conftest commit |

_审计时间：2026-06-28 · 只读 · 未修改生产代码_
