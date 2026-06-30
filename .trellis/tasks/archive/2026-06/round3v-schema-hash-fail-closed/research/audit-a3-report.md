# Audit A3 报告 — B3V-DATA schema_hash fail-closed

| 字段     | 值                                                                                           |
| -------- | -------------------------------------------------------------------------------------------- |
| 维度     | **A3** Security + SQL（DuckDB）                                                              |
| 任务     | `round3v-schema-hash-fail-closed` / Playbook **B3V-DATA**                                    |
| Worktree | `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-data`                                      |
| 分支     | `fix/round3v-schema-hash-fail-closed`                                                        |
| HEAD     | `93815e00` — chore(batch3v-data): execute handoff evidence and loop_manifest AC fix          |
| 审计模式 | **只读**（不改码、不 commit、不写生产 `data/`）                                              |
| 模板     | `agents/security-auditor.md` + `agents/sql-pro.md` + `agents/audit-adversarial-authority.md` |
| 日期     | 2026-06-28                                                                                   |

---

## 1. 审计范围

### 1.1 Trace Authority（AUDIT.plan §0.1 / §1）

| 来源                                                                | 用途                                                                |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `AUDIT.plan.md` §1 A3 覆写                                          | 通过条件：diff 无 production clean write；无 live fetch；零写库路径 |
| `B02_02_schema_hash_fail_closed.md` §4 forbidden                    | 禁止 production clean write / silent accept                         |
| `research/source-index.md`                                          | 切片血缘与接线清单                                                  |
| `specs/contracts/data_adapter_contract.md` § Structured schema_hash | 信任边界                                                            |
| `BATCH_3V_HARDENING_RULES.md`                                       | Batch 边界（间接）                                                  |

### 1.2 审阅文件集

**切片实现（分支当前代码态，已含合并后的 B3V-DATA 逻辑）：**

| 文件                                                | A3 相关性                                     |
| --------------------------------------------------- | --------------------------------------------- |
| `backend/app/db/validation_gate.py`                 | 读路径 SQL；schema_hash fail-closed           |
| `backend/app/datasources/adapters/skeleton_base.py` | 有界 infer；DuckDB 临时读；adapter 不写 clean |
| `specs/contracts/data_adapter_contract.md`          | 结构化豁免 / 信任边界                         |
| `tests/test_db_validation_gate.py`                  | 负向 gate 证据（静态引用）                    |
| `tests/test_adapter_skeletons.py`                   | infer / SCHEMA_DRIFT 证据（静态引用）         |
| `tests/test_data_adapter_contract.py`               | 契约测试（静态引用）                          |

**`git diff master...HEAD` 增量（本分支 tip 相对 master）：**

| 文件                                                | A3 相关性                                                                |
| --------------------------------------------------- | ------------------------------------------------------------------------ |
| `tests/conftest.py`                                 | pytest 启动时向 `.audit-sandbox/` 物化 live-auth fixture（R3H/R3G 邻接） |
| `.trellis/tasks/round3v-schema-hash-fail-closed/**` | 任务证据 / manifest（无运行时代码）                                      |

> **说明：** `validation_gate.py`、`skeleton_base.py`、契约与三测试文件在 `master...HEAD` diff 中**无增量**（实现已合入 master）；A3 仍按 AUDIT Trace 对**当前分支代码态**做全量静态审阅，并对分支 tip 的 `conftest.py` 增量单独标注。

---

## 2. A3 覆写通过条件核对

| 条件                           | 结果     | 证据                                                                                                                                |
| ------------------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| diff 无 production clean write | **PASS** | 分支 tip diff 仅 `conftest.py` + 任务元数据；两生产模块无 `WriteManager` / DML                                                      |
| 无 live fetch 代码             | **PASS** | 切片生产文件无 `https?://`、`enable.qmt`、`enable.xqshare`；`conftest` 仅复制 sandbox fixture，不发起网络                           |
| 零写库路径（本 slice 新增）    | **PASS** | `validation_gate` 仅 `SELECT` + 抛 `ValidationRejected`；`skeleton_base` 经既有 `RawEvidenceStore.save` 写 raw，未新增 clean 表写入 |

**A3 覆写结论：PASS**

---

## 3. §3.3 安全发现

### 3.1 威胁面摘要

| 威胁类              | 本切片暴露面                                    | 结论                                                                   |
| ------------------- | ----------------------------------------------- | ---------------------------------------------------------------------- |
| SQL 注入            | DuckDB `execute` 于 gate + parquet infer        | 无注入面（全参数化）                                                   |
| 未授权写库          | ValidationGate / Adapter                        | 无新增 clean 写路径；gate 方向为 **更严** fail-closed                  |
| 密钥 / token 泄露   | 新增逻辑 + conftest bootstrap                   | 无（fixture 模板无 secret/token）                                      |
| 有界 I/O / 资源滥用 | CSV 64KiB 前缀；payload 10MiB；parquet 临时文件 | 有界，符合 `resource_limits` 意图                                      |
| Live / 外网 fetch   | conftest 邻接 bootstrap                         | 未在 B3V-DATA 生产路径引入；模板 `allow_production_clean_write: false` |

### 3.2 分级发现表

| ID  | 等级 | BLOCKING | 威胁 | 发现              | 证据           |
| --- | ---- | -------- | ---- | ----------------- | -------------- |
| —   | —    | —        | —    | **无 P0/P1 发现** | 见 §4 静态扫描 |

### 3.3 SQL 专项（sql-pro）

| 检查项                                 | 结果    | 位置                                                                                           |
| -------------------------------------- | ------- | ---------------------------------------------------------------------------------------------- |
| 参数绑定 `?`                           | PASS    | `validation_gate.py:195-205,223-231,254-262`                                                   |
| 无 f-string / `.format` 拼 SQL（生产） | PASS    | `rg` 零匹配（两生产 py）                                                                       |
| Parquet infer                          | PASS    | `skeleton_base.py:56-67` — `read_parquet(?)`，`path` 来自 `tempfile.mkstemp`，非用户拼接进 SQL |
| 热路径 EXPLAIN                         | **N/A** | 本 slice 无 migration / 无新索引；gate 为点查 `LIMIT 1`                                        |
| schema/registry diff（A7 邻接）        | PASS    | 分支 tip 无 migration / registry 文件变更                                                      |

**参数化示例（gate 结构化判定与 hash 检查）：**

```sql
SELECT file_type
FROM file_registry
WHERE source = ?
  AND file_type IN ('json', 'csv', 'parquet')
ORDER BY fetch_time DESC
LIMIT 1
-- params: [source_id]
```

```sql
SELECT schema_hash, raw_file_paths, row_count, status
FROM fetch_log
WHERE job_id = ?
ORDER BY fetch_time DESC
LIMIT 1
-- params: [job_id]
```

---

## 4. DOUBT 静态扫描（可复现）

在 worktree 对切片生产文件执行 `security-auditor.md` 基线：

```text
# SQL 拼接
rg -n 'execute\(f|f".*SELECT|f'"'"'.*SELECT' backend/app/db/validation_gate.py backend/app/datasources/adapters/skeleton_base.py
→ 0 matches

# 密钥 / URL
rg -n 'https?://|api[_-]?key|secret|token|password' backend/app/db/validation_gate.py backend/app/datasources/adapters/skeleton_base.py
→ 0 matches

# 写库 / 迁移
rg -n 'writer\(|apply_migrations|INSERT |UPDATE |DELETE ' backend/app/db/validation_gate.py backend/app/datasources/adapters/skeleton_base.py
→ 0 matches

# 危险执行（skeleton_base）
rg -n 'subprocess|os\.system|eval\(|exec\(' backend/app/datasources/adapters/skeleton_base.py
→ 0 matches
```

### 4.1 DOUBT 三类对抗搜索

| 类                    | 搜索范围                                   | 结果                                                       |
| --------------------- | ------------------------------------------ | ---------------------------------------------------------- |
| 1. 硬编码 URL 变体    | 两生产 py + contract + conftest diff       | **无发现**                                                 |
| 2. JWT / API key 模式 | 同上 + `tests/fixtures/**prediction*fred*` | **无发现**（模板仅 `authorization_present` / ticker 列表） |
| 3. SQL 拼接           | 两生产 py                                  | **无发现**                                                 |

---

## 5. 信任边界与 fail-closed 行为（对抗性）

### 5.1 Adapter 层（`skeleton_base.py`）

- 结构化类型 `json|csv|parquet` + `row_count > 0` + infer 失败 → **`SCHEMA_DRIFT`**，非 silent `SUCCESS`（`L183-202`）。
- Payload 上限 `DEFAULT_MAX_PAYLOAD_BYTES = 10 * 1024 * 1024`（`L20,147-158`）。
- CSV infer 仅读 64KiB 前缀（`L22,39`）。
- Parquet infer：临时文件 + 进程内 `duckdb.connect()`，`read_parquet(?)` 参数绑定，finally 清理（`L56-82`）；无 ATTACH / 无用户可控路径进 SQL 文本。

### 5.2 Gate 层（`validation_gate.py`）

- 结构化 + `SUCCESS` + `row_count>0` + `schema_hash IS NULL` → **block clean write**（`L242-248`）。
- `write_mode ∈ {manual_patch, schema_migration}` 仍跳过 schema_hash 检查（`L217-218`）——为审批写入模式，契约已知，**非本 diff 引入的旁路**。
- `_fetch_log_is_structured`：`raw_file_paths` 后缀优先，否则 `file_registry` 按 `source` 回退最近 structured 行（`L183-206`）。

### 5.3 GitNexus 查询

`query("schema_hash validation gate fail-closed structured fetch")` → 命中 `DbValidationGate._enforce_report`（`validation_gate.py:207-274`）参与 `assert_can_write` 流程；定义侧含 `test_missingSchemaHashOnStructuredFetch_rejects` 等，与切片 AC 一致。

---

## 6. 计划外发现

> 对抗性搜索：若只跑 MASTER §8 用例，下列项仍可能被忽略。

| ID         | 等级 | BLOCKING     | 发现                                                                                                           | 理由                                                                        | 建议                                                              |
| ---------- | ---- | ------------ | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| A3-PLAN-01 | P2   | NON-BLOCKING | `_fetch_log_is_structured` 的 `file_registry` 回退仅按 `source` 取最近 structured 行，未关联 `job_id`/`run_id` | 偏向 **误杀**（fail-closed），非 fail-open 绕过                             | 后续若误拒增多，可收紧为 job/run 级关联；本任务 AC 不要求         |
| A3-PLAN-02 | P3   | NON-BLOCKING | Parquet infer 每次 `duckdb.connect()` + `mkstemp`                                                              | 有 payload 上限与 finally 清理；高并发 fetch 下临时文件 churn               | 文档已声明有界；无需本 slice 改码                                 |
| A3-PLAN-03 | P3   | NON-BLOCKING | 直接 SQL 注入 `fetch_log`（绕过 adapter）且路径无 structured 后缀、registry 无 structured 行                   | 需已有 DB 写权限；非本 diff 攻击面                                          | 运维/DB 权限面；不在 B3V-DATA scope                               |
| A3-PLAN-04 | P3   | NON-BLOCKING | 分支 tip `conftest.py` 在 `pytest_configure` 自动物化 R3H/R3G live-auth YAML 至 `.audit-sandbox/`              | 模板无密钥；`allow_production_clean_write: false`；仅当目标文件不存在时复制 | 保持 fixture 为 template；勿将真实 API key 写入 `tests/fixtures/` |

**显式声明：** 已按计划外表完成对抗搜索；无 BLOCKING 项。

---

## 7. 与任务卡 / 契约一致性

| 要求                                      | 状态                                                            |
| ----------------------------------------- | --------------------------------------------------------------- |
| B02 §4 禁止 production clean write        | 满足                                                            |
| AC-DATA-03 gate fail-closed（缺 hash）    | 代码 + `test_missingSchemaHashOnStructuredFetch_rejects` 对齐   |
| AC-DATA-04 corrupt csv/parquet 非 SUCCESS | adapter `SCHEMA_DRIFT` 路径 + 测试                              |
| contract § Structured schema_hash         | 实现一致                                                        |
| B3V-AUD-05 不得削弱 gate 负向测试         | 静态审阅：保留 reject 测试（含 registry fallback），未见 weaken |

---

## 8. 验证结果（A3 静态）

| 项                              | 结果                                         |
| ------------------------------- | -------------------------------------------- |
| 静态 rg 基线                    | PASS                                         |
| SQL 参数化                      | PASS                                         |
| A3 覆写（零新增写库 / 无 live） | PASS                                         |
| GitNexus query                  | PASS（命中 gate 执行流）                     |
| TypeCheck / Lint                | **未执行**（只读 A3）                        |
| A8 pytest 子集                  | **未执行**（归 A8 维；命令见 AUDIT.plan §1） |

---

## 9. 总结

| 指标         | 值                                                     |
| ------------ | ------------------------------------------------------ |
| 审阅文件     | 7（2 生产 py + 1 contract + 3 测试 + 1 conftest 增量） |
| P0/P1 发现   | 0                                                      |
| P2/P3 计划外 | 4（均 NON-BLOCKING）                                   |
| **A3 判定**  | **PASS**                                               |

本切片在 SQL 安全与写路径控制上符合 AUDIT.plan A3 覆写：生产路径全部为参数化读查询，强化 schema_hash fail-closed，未引入 production clean write、live fetch 或密钥暴露。分支 tip 的 `conftest` bootstrap 限于 sandbox fixture 物化且无真实凭据。剩余 P2/P3 为分类启发式、资源 hygiene 与邻接测试基础设施，不构成 merge 阻断。

---

_审计员角色：Audit-A3 · B3V-DATA · 只读_
