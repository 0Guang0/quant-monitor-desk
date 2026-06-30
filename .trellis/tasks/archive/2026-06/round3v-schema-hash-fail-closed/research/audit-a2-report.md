# A2 Ponytail Audit — B3V-DATA schema_hash fail-closed

> **Task:** `round3v-schema-hash-fail-closed` · Playbook `B3V-DATA` / `B3V-C02`  
> **Agent:** audit-ponytail (A2) · **只读**  
> **Worktree:** `quant-monitor-desk-wt-b3v-data` · branch `fix/round3v-schema-hash-fail-closed`  
> **Authority:** `agents/audit-a2-ponytail.md` + `agents/audit-adversarial-authority.md` + `AUDIT.plan.md`  
> **Diff base:** commit `1bc0260d`（`fix(data): schema_hash fail-closed for structured fetches`）  
> **复核日期:** 2026-06-28

---

## Verdict: **PASS**

实现 diff 净增 **+381 行**（6 文件，+396 / −15），与 AC-DATA-01..05 及 B02_02 切片规模匹配：契约段、CSV/Parquet 有界 infer、Gate fail-closed、冻结负向测试。无 factory/registry 框架、无新依赖、无计划外抽象层。**阻塞项 0**；下列均为可选收缩（建议级）。

---

## git diff --stat（A2 checklist）

| 文件                                                | Δ 行                     |
| --------------------------------------------------- | ------------------------ |
| `backend/app/datasources/adapters/skeleton_base.py` | +103                     |
| `backend/app/db/validation_gate.py`                 | +68                      |
| `specs/contracts/data_adapter_contract.md`          | +22                      |
| `tests/test_adapter_skeletons.py`                   | +103                     |
| `tests/test_data_adapter_contract.py`               | +18                      |
| `tests/test_db_validation_gate.py`                  | +97                      |
| **合计**                                            | **+396 / −15，net +381** |

**MASTER §8 触及文件：** `data_adapter_contract.md`（DATA-01）、`skeleton_base.py`（DATA-02/04）、`validation_gate.py`（DATA-03）、§5.1 三测试文件 — 与 diff 一致，无计划外生产路径。

---

## DOUBT（≥20 行可简化？）

| 攻击                               | 和解                                                                                                                              |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 「+103 行 skeleton 是否过度？」    | 三格式 infer + fail-closed 守卫；`_canonical_schema_hash` 反而消除 JSON 路径重复；Parquet 需 DuckDB+临时文件（MASTER §0.3a 既定） |
| 「Gate +68 行是否 wrapper 膨胀？」 | `_fetch_log_is_structured` 实现契约「suffix **或** file_registry.file_type」双路径，非 speculative 抽象                           |
| 「测试 +218 行是否 setup 膨胀？」  | **是** — corrupt CSV/Parquet 两测 ~55 行结构重复，可参数化收缩 ≥20 行（见 A2-05）                                                 |

**DOUBT 结论：** 至少 **1 处** ≥20 行可简化（测试重复）；生产代码无 ≥20 行且无 AC 依据的整块可删。

---

## §3.2 候选删改表

| 候选删改（file:line）                                                                                                                   | ponytail 梯级                                               | 是否阻塞                       |
| --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------ |
| `validation_gate.py:82` — `_STRUCTURED_FILE_TYPES` **定义但未使用**；SQL `200` 行硬编码 `('json','csv','parquet')`                      | 梯级 5（删死常量或用于 SQL）                                | 建议                           |
| `validation_gate.py:82-83` + `skeleton_base.py:21` — structured 类型双份维护                                                            | 梯级 2（复用单一常量；suffix 可由 file_type 派生）          | 建议                           |
| `validation_gate.py:168-206` — `_raw_paths_indicate_structured` 与 `_fetch_log_is_structured` 可合并为单函数（净减 ~10–15 行，未达 20） | 梯级 6（最小代码）                                          | 建议                           |
| `validation_gate.py:187` — `_fetch_log_is_structured(..., job_id=...)` 的 `job_id` **未使用**                                           | 梯级 5（删死参）                                            | 建议                           |
| `skeleton_base.py:56-82` — `_infer_parquet_schema_hash` mkstemp/finally 样板偏长；缺 `ponytail:` 天花板注释（临时文件 I/O）             | 梯级 4（`NamedTemporaryFile` 更短）+ 梯级 7（应标注天花板） | 建议                           |
| `skeleton_base.py:188-202` — SCHEMA_DRIFT 早退与 SUCCESS `FetchResult` 字段块重复                                                       | 梯级 2（与现有 error 早退风格一致；可小 helper 但未强制）   | 建议                           |
| `tests/test_adapter_skeletons.py:733-790` — `test_skeletonFetch_corruptCsv_*` / `corruptParquet_*` 夹具与断言几乎相同                   | 梯级 2（`@pytest.mark.parametrize` 复用 `StubFetchPort`）   | 建议                           |
| `tests/test_data_adapter_contract.py:810-826` — 契约 md 字符串探针                                                                      | 梯级 1（AC-DATA-01 要求契约可测）                           | **不算**（MASTER explicit AC） |
| `specs/contracts/data_adapter_contract.md:43-63` — 契约段 +22 行                                                                        | 梯级 1（AC-DATA-01 交付物）                                 | **不算**                       |

---

## 计划外发现（对抗性搜索）

已读：`skeleton_base.py`、`validation_gate.py`、契约 diff、`test_adapter_skeletons.py`（新增段）、`test_db_validation_gate.py`（新增测）、`docs/modules/data_validation_and_conflict.md`（schema_hash 语义）、`B02_02_schema_hash_fail_closed.md` §4 forbidden。

| ID    | 发现                                                                                                                                          | 与 MASTER 关系                                                 | 阻塞                         |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------- |
| PO-01 | `validation_gate.py:195-205` file_registry 回退查询按 `source_id` 取最近一条，**未按 job_id 过滤** — 可能把无关历史 file_type 判为 structured | 契约允许 file_registry 分类，但未限定 job 范围；计划未写此边界 | 非 A2（语义/正确性 → A4/A5） |
| PO-02 | Parquet infer 每次 `duckdb.connect()` 无连接复用                                                                                              | MASTER §0.3a 允许 DuckDB；非 hot path                          | 非阻塞（A6 SKIP）            |
| PO-03 | 无共享 `STRUCTURED_FILE_TYPES` 模块 — 两处 frozenset 漂移风险；且 gate 侧常量未接线                                                           | 计划未要求集中常量                                             | 建议（A2-01）                |

**计划外 bloat：** 未发现计划外新模块、新依赖或仅单调用 wrapper factory。

---

## 与 A4 交叉引用

| A2 项                                               | A4 可能接续                                      |
| --------------------------------------------------- | ------------------------------------------------ |
| infer 失败统一 `return None` → adapter SCHEMA_DRIFT | 错误模型是否应区分 corrupt vs empty header（A4） |
| `_infer_parquet_schema_hash` 吞掉 `duckdb.Error`    | 是否应记录可观测 reason（A4 日志/错误模型）      |
| Gate `int(row_count or 0)`                          | 类型脆弱断言（A4）                               |
| PO-01 registry 回退未按 job 过滤                    | 正确性/边界（A4/A5）                             |

---

## 做得好的地方（ponytail 合规）

- **梯级 2：** JSON 复用既有 `_shape` + 抽出 `_canonical_schema_hash`，未重写指纹逻辑。
- **梯级 3/4：** CSV 用 stdlib `csv`；Parquet 用已在依赖树的 DuckDB `DESCRIBE`（非全文件扫描）。
- **梯级 1：** 未引入 pyarrow/pandas 或新 registry 框架。
- **YAGNI：** 改动限于 B3V-DATA allowed 文件组；无 RawStore/sync/layer5 扩散。
- **测试：** 五字段 docstring 齐全；负向 gate 测试保留（B3V-AUD-05 对齐）。

---

## §4.3 / 阻塞队列（A2 贡献）

| ID  | Priority | Blocks finish-work? |
| --- | -------- | ------------------- |
| —   | —        | **No**              |

全部 A2 项为 P3 可选收缩或它维（PO-01 → A4/A5）。**§4.3 count (A2): 0**

---

## 建议收缩（Audit 不应用）

1. **A2-01：** 在 `skeleton_base` 导出常量，或 `validation_gate` 从契约单一源导入；suffix 由 `.{ft}` 生成；删除 gate 侧未用 `_STRUCTURED_FILE_TYPES` 或接线到 SQL。
2. **A2-03：** 删除 `_fetch_log_is_structured` 未用 `job_id` 参数。
3. **A2-04：** Parquet 路径加 `ponytail:` 注释；考虑 `NamedTemporaryFile(delete=False)` 缩短 finally。
4. **A2-05：** `@pytest.mark.parametrize("file_type,corrupt", [("csv", ...), ("parquet", ...)])` 合并 corrupt 测试（估 −25~30 LOC）。

**估 optional shrink：** ~35–45 LOC（主要为测试），占 net +381 的 ~10%。

---

## Verification（A2 维度）

| Check                   | Result                       |
| ----------------------- | ---------------------------- |
| `git diff --stat`       | 已记录（上表，`1bc0260d`）   |
| 每候选 file:line + 梯级 | 已列 §3.2                    |
| A4 交叉                 | 已列                         |
| 阻塞 vs 建议            | 阻塞 0 / 建议 7              |
| Build / pytest          | **未跑**（A2 只读；A8 负责） |

---

_A2 only · 未执行 A1/A3–A8 · 未改代码_
