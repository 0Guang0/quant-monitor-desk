# Audit A3 报告 — B3V-DATA schema_hash fail-closed

| 字段 | 值 |
|------|-----|
| 维度 | **A3** Security + SQL（DuckDB） |
| 任务 | `round3v-schema-hash-fail-closed` / Playbook **B3V-DATA** |
| Worktree | `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-data` |
| 分支 | `fix/round3v-schema-hash-fail-closed` |
| 审计模式 | **只读**（不改码、不 commit、不写生产 `data/`） |
| 模板 | `agents/security-auditor.md` + `agents/sql-pro.md` |
| 日期 | 2026-06-25 |

---

## 1. 审计范围

### 1.1 Trace Authority（AUDIT.plan §0.1 / §1）

| 来源 | 用途 |
|------|------|
| `AUDIT.plan.md` §1 A3 覆写 | 通过条件：diff 无 production clean write；无 live fetch；零写库路径 |
| `MASTER.plan.md` §0 Batch 3V 边界 | owns / must-not |
| `B02_02_schema_hash_fail_closed.md` | 任务卡 forbidden / AC |
| `specs/contracts/data_adapter_contract.md` | 结构化 schema_hash 契约 |

### 1.2 Diff 文件（工作区 unstaged vs index）

| 文件 | A3 相关性 |
|------|-----------|
| `backend/app/db/validation_gate.py` | 读路径 SQL；fail-closed 策略 |
| `backend/app/datasources/adapters/skeleton_base.py` | 有界 infer；DuckDB 临时读；adapter 不写 clean |
| `specs/contracts/data_adapter_contract.md` | 信任边界 / 结构化豁免语义 |
| `tests/test_db_validation_gate.py` | 负向 gate 证据（静态引用） |
| `tests/test_adapter_skeletons.py` | infer / SCHEMA_DRIFT 证据（静态引用） |
| `tests/test_data_adapter_contract.py` | 契约测试（静态引用） |

> 注：`git diff master...HEAD` 为空（变更尚未 commit）；本报告基于 `git diff`（工作区）审阅。

---

## 2. A3 覆写通过条件核对

| 条件 | 结果 | 证据 |
|------|------|------|
| diff 无 production clean write | **PASS** | 两生产模块均无 `WriteManager` / `INSERT` / `UPDATE` / `DELETE`；`validation_gate` 仅 `SELECT` + 抛 `ValidationRejected` |
| 无 live fetch 代码 | **PASS** | diff 文件内无 `https?://`、`enable.qmt`、`enable.xqshare`、live pilot 引用 |
| 零写库路径（本 slice 新增） | **PASS** | `skeleton_base` 仍经 `RawEvidenceStore.save` 写 raw 证据（既有行为）；未新增 clean 表写入 |

**A3 覆写结论：PASS**

---

## 3. §3.3 安全发现

### 3.1 威胁面摘要

| 威胁类 | 本 diff 暴露面 | 结论 |
|--------|----------------|------|
| SQL 注入 | DuckDB `execute` 于 gate + parquet infer | 无注入面（全参数化） |
| 未授权写库 | ValidationGate / Adapter | 无新增写路径；gate 方向为 **更严** fail-closed |
| 密钥 / token 泄露 | 新增逻辑 | 无 |
| 有界 I/O / 资源滥用 | CSV 64KiB 前缀；payload 10MiB 上限；parquet 临时文件 | 有界，符合契约 |
| Live / 外网 fetch | — | 未触及 |

### 3.2 分级发现表

| ID | 等级 | BLOCKING | 威胁 | 发现 | 证据 |
|----|------|----------|------|------|------|
| — | — | — | — | **无 P0/P1 发现** | 见 §4 静态扫描 |

### 3.3 SQL 专项（sql-pro）

| 检查项 | 结果 | 位置 |
|--------|------|------|
| 参数绑定 `?` | PASS | `validation_gate.py:195-205,223-231,254-262` |
| 无 f-string / `.format` 拼 SQL | PASS | `rg` 零匹配（两文件） |
| Parquet infer | PASS | `skeleton_base.py:64-67` — `read_parquet(?)`，`path` 来自 `tempfile.mkstemp`，非用户拼接 |
| 热路径 EXPLAIN | **N/A** | 本 slice 无 migration / 无新索引；gate 为点查 `LIMIT 1` |
| schema/registry diff | PASS（A7 邻接） | 无 migration 文件变更 |

**参数化示例（gate 新增查询）：**

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

## 4. DO NOT DOUBT 静态扫描（可复现）

在 worktree 对 diff 生产文件执行 `security-auditor.md` 基线：

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

# 危险执行
rg -n 'subprocess|os\.system|eval\(|exec\(' backend/app/datasources/adapters/skeleton_base.py
→ 0 matches
```

### 4.1 DOUBT 三类对抗搜索

| 类 | 搜索范围 | 结果 |
|----|----------|------|
| 1. 硬编码 URL 变体 | diff 两 py + contract | **无发现** |
| 2. JWT / API key 模式 | 同上 | **无发现** |
| 3. SQL 拼接 | 同上 + 全 backend `execute(f` 基线（本文件无） | **无发现** |

---

## 5. 信任边界与 fail-closed 行为（对抗性）

### 5.1 Adapter 层（`skeleton_base.py`）

- 结构化类型 `json|csv|parquet` + `row_count > 0` + infer 失败 → **`SCHEMA_DRIFT`**，非 silent `SUCCESS`（`L183-202`）。
- Raw 路径由 `RawStore.save` 生成，扩展名与 `file_type` 绑定（`raw_store.py:62-66` `{hash}.{ext}`），后缀检测与类型一致。
- Parquet infer：临时文件 + 进程内 `duckdb.connect()`，无 ATTACH / 无用户可控路径进 SQL。

### 5.2 Gate 层（`validation_gate.py`）

- 新增：结构化 + `SUCCESS` + `row_count>0` + `schema_hash IS NULL` → **block clean write**（`L242-248`）。
- 相对旧逻辑：去掉「缺 `source_id` 即放行」的 fail-open 窗口；缺 hash 时可在仅有 `raw_file_paths` 后缀时仍 block。
- **既有旁路（非本 diff 引入）**：`write_mode ∈ {manual_patch, schema_migration}` 仍跳过 schema_hash 检查（`L217-218`）——为审批写入模式，契约已知。

### 5.3 GitNexus 查询

`query("schema_hash validation gate fail-closed structured fetch")` → 命中 `DbValidationGate._enforce_report`、`assert_can_write` 流程及对应测试，与 diff 一致。

---

## 6. 计划外发现

> 对抗性搜索：若只跑 MASTER §8 用例，下列项仍可能被忽略。

| ID | 等级 | BLOCKING | 发现 | 理由 | 建议 |
|----|------|----------|------|------|------|
| A3-PLAN-01 | P2 | NON-BLOCKING | `_fetch_log_is_structured` 的 `file_registry` 回退仅按 `source` 取最近 structured 行，未关联 `job_id`/`run_id` | 偏向 **误杀**（fail-closed），非 fail-open 绕过；历史 registry 行可能使当前 job 被标为 structured | 后续 slice 若出现误拒，可收紧为 job/run 级关联；本任务 AC 不要求 |
| A3-PLAN-02 | P3 | NON-BLOCKING | Parquet infer 每次 `duckdb.connect()` + `mkstemp` | 有 `DEFAULT_MAX_PAYLOAD_BYTES` 与 finally 清理；高并发 fetch 下临时文件 churn | 文档已声明有界；无需本 slice 改码 |
| A3-PLAN-03 | P3 | NON-BLOCKING | 直接 SQL 注入 `fetch_log`（绕过 adapter）且路径无 structured 后缀、registry 无 structured 行 | 需已有 DB 写权限；非本 diff 攻击面 | 运维/DB 权限面；不在 B3V-DATA scope |

**显式声明：** 已按计划外表完成对抗搜索；无 BLOCKING 项。

---

## 7. 与任务卡 / 契约一致性

| 要求 | 状态 |
|------|------|
| B02 §4 禁止 production clean write | 满足 |
| AC-DATA-03 gate fail-closed（缺 hash） | 代码 + `test_missingSchemaHashOnStructuredFetch_rejects` 对齐 |
| AC-DATA-04 corrupt csv/parquet 非 SUCCESS | adapter `SCHEMA_DRIFT` 路径 + 测试 |
| contract § Structured schema_hash | diff 与实现一致 |
| B3V-AUD-05 不得削弱 gate 负向测试 | 静态审阅：新增/保留 reject 测试，未见 weaken |

---

## 8. 验证结果（A3 静态）

| 项 | 结果 |
|----|------|
| 静态 rg 基线 | PASS |
| SQL 参数化 | PASS |
| A3 覆写（零新增写库 / 无 live） | PASS |
| TypeCheck / Lint | **未执行**（只读 A3；Execute/A8 负责 pytest） |
| A8 pytest 子集 | **未执行**（归 A8 维；命令见 AUDIT.plan §1） |

---

## 9. 总结

| 指标 | 值 |
|------|-----|
| 审阅文件 | 6（2 生产 py + 1 contract + 3 测试） |
| P0/P1 发现 | 0 |
| P2/P3 计划外 | 3（均 NON-BLOCKING） |
| **A3 判定** | **PASS** |

本 slice 在 SQL 安全与写路径控制上符合 AUDIT.plan A3 覆写：全部为参数化读查询，强化 schema_hash fail-closed，未引入 production clean write、live fetch 或密钥暴露。剩余 P2/P3 为分类启发式与运维面 hygiene，不构成 merge 阻断。

---

*审计员角色：trellis-check · A3 only · 只读*
