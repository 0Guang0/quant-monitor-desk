# A4 audit-quality — B3V-DATA schema_hash fail-closed

> Dimension: Code Quality (A4 only)  
> Scope: unstaged diff on `fix/round3v-schema-hash-fail-closed`  
> Worktree: `../quant-monitor-desk-wt-b3v-data`  
> Skills: `code-review-and-quality` + `doubt-driven-development`  
> Authority: `agents/code-reviewer.md` · `agents/audit-adversarial-authority.md`  
> Mode: **只读**（无代码修复）

---

## Verdict: **PASS**

实现与 `data_adapter_contract.md` VR-DATA-001 段、任务卡 `B02_02` §2–§6 语义一致：adapter 层对 json/csv/parquet 在 `SUCCESS`+`row_count>0` 时强制非空 `schema_hash`，推导失败返回 `SCHEMA_DRIFT`；ValidationGate 对带结构化路径后缀且缺 hash 的 fetch_log 行 fail-closed。新增测试均含五字段中文 docstring，pytest 子集通过。无 P0 逻辑/安全阻塞项；下列为 NON-BLOCKING 计划外缺口与可维护性建议。

---

## 审查范围

| 文件 | 变更摘要 |
|------|----------|
| `backend/app/datasources/adapters/skeleton_base.py` | CSV/Parquet 有界 `_infer_schema_hash`；结构化缺 hash → `SCHEMA_DRIFT` |
| `backend/app/db/validation_gate.py` | `_fetch_log_is_structured` + `_schema_hash_blocks_write` fail-closed 分支 |
| `specs/contracts/data_adapter_contract.md` | Structured schema_hash 契约段 |
| `tests/test_adapter_skeletons.py` | CSV/Parquet 推导 + 损坏文件负向 |
| `tests/test_data_adapter_contract.py` | 契约文档冻结断言 |
| `tests/test_db_validation_gate.py` | 缺 hash 结构化 fetch → `ValidationRejected` |

---

## 轴评分（1–5）

| 轴 | 分 | 理由 |
|----|----|------|
| Correctness | 4 | 主路径（adapter + gate 后缀路径）正确；gate 二级分类存在计划外 fail-open 窗口（见 A4-02） |
| Readability | 4 | `_canonical_schema_hash` 抽取合理；`validation_gate` 新增 helper 清晰，但 `job_id` 未使用 |
| Architecture | 4 | Layer1 adapter / Layer4 gate 分工符合 Playbook；`_STRUCTURED_FILE_TYPES` 双模块重复可接受 |
| Error handling | 4 | infer 失败统一 `None` → adapter `SCHEMA_DRIFT`；parquet temp 文件 `finally` 清理完整 |
| Test quality | 4 | 五字段齐全、负向未削弱；缺 gate `file_registry` 回退路径单测 |

---

## §3.4 发现表

| 轴 | ID | 发现 | 阻塞? | 证据 |
|----|-----|------|-------|------|
| Correctness | A4-01 | Gate 仅在 `raw_file_paths` 含 `.json/.csv/.parquet` 后缀时可靠识别结构化；无后缀且 `file_registry` 无该 source 的结构化历史时，`current_hash is None` 走 `return False`（fail-open） | NON-BLOCKING | `validation_gate.py:249-250`；契约已注明 registry 闭合 defer 至 B02-DATA-05 |
| Correctness | A4-02 | `_fetch_log_is_structured` 的 `file_registry` 回退按 `source_id` 全局 `ORDER BY fetch_time DESC LIMIT 1`，未与 `job_id`/当前 fetch 关联；可能把历史结构化文件误判为当前 fetch 类型（偏向 fail-closed，安全方向） | NON-BLOCKING | `validation_gate.py:195-206` |
| Maintainability | A4-03 | `_fetch_log_is_structured(..., job_id=...)` 形参 `job_id` 未使用，易误导后续维护者 | NON-BLOCKING | `validation_gate.py:183-190` |
| Error handling | A4-04 | CSV 推导仅 UTF-8；合法非 UTF-8 表头会 infer 失败 → `SCHEMA_DRIFT`（fail-closed，符合契约「推导失败不得 SUCCESS」） | NON-BLOCKING | `skeleton_base.py:38-43` |
| Resource / I/O | A4-05 | Parquet 推导将完整 payload 写入 `mkstemp` 临时文件（上限受 `DEFAULT_MAX_PAYLOAD_BYTES=10MB` 约束）；契约写「LIMIT 0 语义」而实现为落盘 + `DESCRIBE` | NON-BLOCKING | `skeleton_base.py:56-82`；符合 MASTER §0.3a Ponytail |
| Test | A4-06 | 无单测覆盖 gate「`raw_file_paths` 为空 + `file_registry` 有 structured file_type」回退分支 | NON-BLOCKING | 对抗搜索：`tests/test_db_validation_gate.py` 仅 `.csv` 后缀路径 |
| Test | A4-07 | `test_dataAdapterContract_documentsStructuredSchemaHashRequirement` 为契约字符串存在性检查，不验证运行时行为（对 AC-DATA-01 文档冻结足够，非 tautological 生产逻辑测试） | NON-BLOCKING | `tests/test_data_adapter_contract.py:810-826` |

---

## 计划外发现

| ID | 场景 | 若只按 MASTER §8 用例测会漏什么 | 严重度 |
|----|------|-----------------------------------|--------|
| OP-01 | 非 skeleton 路径写入 `fetch_log`：`SUCCESS`+`row_count>0`+`schema_hash=NULL`，`raw_file_paths` 无结构化后缀，且 source 无 structured `file_registry` 行 | Gate 不拦截 clean-write | NON-BLOCKING（registry/多写入路径 defer） |
| OP-02 | 同 source 先 structured 后 schemaless：`raw_file_paths` 为空时 gate 可能仍因历史 `file_registry` 判 structured | 误拒 schemaless 写入（fail-closed 偏安全） | NON-BLOCKING |
| OP-03 | Parquet 损坏测试断言 `FAILED` 或 `SCHEMA_DRIFT` 均可，但 adapter 实现固定返回 `SCHEMA_DRIFT` | 无功能缺口；断言略宽 | 信息性 |

**对抗搜索声明：** 已对照 diff、`B02_02` §4 forbidden、`data_adapter_contract.md` VR-DATA-001 段、`validation_gate._schema_hash_blocks_write` 全分支、adapter `_fetch_impl` 成功/失败路径及三测试文件新增用例。

---

## DOUBT（对抗性）

| Claim | Attack | Result |
|-------|--------|--------|
| 「结构化 SUCCESS 绝不能缺 schema_hash 写库」 | Adapter 已拦；Gate 仅后缀+registry 启发式 | **部分成立** — 主路径闭环；OP-01 为 defense-in-depth 缺口 |
| 「损坏 CSV/Parquet 不会 SUCCESS」 | `test_skeletonFetch_corrupt*` + infer `None` → `SCHEMA_DRIFT` | **成立** |
| 「schema_hash 漂移仍拒绝」 | 既有 `test_schemaHashDriftWithoutApproval_rejects` 未改 | **成立** |
| 「有界推导不全文件扫描」 | CSV 64KiB 前缀；Parquet 落盘整文件但 ≤10MB payload cap | **成立**（A6 本任务 SKIP，见 A4-05） |

**必选 DOUBT 结论（file:line）：** `validation_gate.py:249-250` — 当 gate 无法将 fetch 分类为 structured 时，`current_hash is None` 直接 `return False`，不阻断写入；与 adapter 层 fail-closed 形成不对称。计划未写此边界；建议 B02-DATA-05 registry 闭合或追加「无后缀 + registry 回退」单测后再收紧。

---

## Checklist（code-reviewer.md）

- [x] 无 P0 逻辑/安全阻塞
- [x] 错误处理可观测（`error_message="structured fetch missing schema_hash"`；gate `ValidationRejected` match schema_hash）
- [x] 风格与邻近模块一致（复用 `_shape`、stdlib csv、既有 DuckDB 模式）
- [x] 测试变更保留 purpose（中文五字段）
- [x] 判定基于 diff 与 pytest，非覆盖率 KPI

---

## 验证结果

| 检查 | 命令 | 结果 |
|------|------|------|
| Pytest 子集 | `uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest` | **PASS**（103 passed） |
| Ruff | `uv run ruff check` 触及文件 | **4×E501** 均在既有行（非本 diff 新增）；本 diff 新增代码无 ruff 违规 |

---

## 做得好的地方

- `_canonical_schema_hash` 消除 JSON/CSV/Parquet 三处重复 canonical 逻辑，符合 ponytail「删重复」。
- Adapter 在 raw 已落盘后才判 `SCHEMA_DRIFT`，保留 `raw_file_paths`/`content_hash` 证据链。
- Gate 新分支在 `current_hash is None` 之前先检查 structured+SUCCESS+row_count，不破坏既有 schemaless 放行。
- 损坏文件负向测试接受 `FAILED|SCHEMA_DRIFT`，未削弱 B3V-AUD-05 意图。
- 契约段与实现推导边界（64KiB CSV、Parquet DESCRIBE）对齐。

---

## A4 门控结论

| 项 | 值 |
|----|-----|
| 维度 | A4 Code Quality |
| 结论 | **PASS** |
| BLOCKING 计数 | 0 |
| 建议跟进 | A4-01/02/06 → B02-DATA-05 或后续 hardening slice；A4-03 删除未用 `job_id` 或实现 job 级关联 |

*审计时间：2026-06-25 · 只读 · 未修改生产代码*
