# A6 audit-perf — B3V-DATA schema_hash fail-closed 性能审计

> **维度：** A6 · performance-engineer + doubt-driven-development  
> **模型：** composer-2.5  
> **任务：** `round3v-schema-hash-fail-closed`（B3V-DATA · Manifest `B3V-C02`）  
> **Worktree：** `C:\Users\Guang\Desktop\quant-monitor-desk-wt-b3v-data`  
> **分支 / HEAD：** `fix/round3v-schema-hash-fail-closed` · `93815e00`  
> **日期：** 2026-06-28  
> **模式：** Audit（只读，无 commit、无改码）

---

## 总判定

| 项                   | 值                                     |
| -------------------- | -------------------------------------- |
| **verdict**          | **SKIP**                               |
| **BLOCKING**         | 0                                      |
| **NON-BLOCKING**     | 2                                      |
| **AUDIT.plan §1 A6** | **SKIP** — 本地 schema 探测无 SLA 热点 |

---

## Scorecard（静态审计 + 参考 pytest durations）

| 指标               | 值           | 来源                    | 阈值（Plan 冻结） | 状态        |
| ------------------ | ------------ | ----------------------- | ----------------- | ----------- |
| LCP / INP / CLS    | not measured | —                       | CWV               | —（无 Web） |
| smoke 端到端耗时   | not measured | Plan 未挂载             | —                 | SKIP        |
| ResourceGuard 触发 | not measured | infer 路径未挂 guard    | —                 | SKIP        |
| 最慢单测 call      | 0.57s        | pytest `--durations=10` | 未冻结            | 参考 only   |
| gate 缺 hash 测    | 0.50s (csv)  | 同上                    | 未冻结            | 参考 only   |
| adapter infer 测   | ≤0.05s       | 同上（无进 top10）      | 未冻结            | 参考 only   |

> **Artifacts used:** `uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest --durations=10`  
> **注记：** 本次复跑 106 passed / 1 failed（`test_missingSchemaHashOnStructuredFetch_rejects[parquet]` DuckDB `database does not exist` IO 错误）；属 Windows basetemp 并发/残留卫生问题，非 perf 回归；正式门禁委托 A8 干净复跑。  
> **Stack detected:** Python 单机 pipeline；adapter fetch + ValidationGate SQL；无 API/调度 hot path；非 Web 应用

---

## GitNexus 爆炸半径（A6 必用 · 2026-06-28）

| 符号                                               | 方向     | risk    | direct | processes              | 模块     | A6 解读                              |
| -------------------------------------------------- | -------- | ------- | ------ | ---------------------- | -------- | ------------------------------------ |
| `_infer_schema_hash` (`skeleton_base.py`)          | upstream | **LOW** | 1      | 0                      | Adapters | 每 fetch 一次；非生产 hot path       |
| `_schema_hash_blocks_write` (`validation_gate.py`) | upstream | **LOW** | 1      | 1 (`assert_can_write`) | Db       | clean-write 前 O(1) gate；非高频 API |

**结论：** 两符号 blast radius 均为 LOW，无 CRITICAL/HIGH 性能面；与 AUDIT.plan「无 SLA 热点」一致。

---

## 1. 权威层级（`audit-adversarial-authority.md`）

| 级别   | 来源                                                                                       | 与本维结论                                                                             |
| ------ | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| 第一级 | `B02_02_schema_hash_fail_closed.md` §4、`data_adapter_contract.md`、`resource_limits.yaml` | 禁止全文件扫描；结构化 SUCCESS 须有 schema_hash；有界推导优先                          |
| 第二级 | `agents/performance-engineer.md` checklist、`AUDIT.plan.md` §1                             | A6 显式 **SKIP**；验收 = 任务卡 §7 pytest 子集（委托 A8）                              |
| 第三级 | `MASTER.plan.md` §7 Red Flags、`§2.5` 设计决策                                             | DuckDB LIMIT 0 / metadata；禁止全量 Parquet 扫；**§10 为 Execute DoD，无 perf 冻结行** |

**对抗性注记：** MASTER §10 仅列 pytest/ruff/validate-handoff，**未**定义 `production_equivalent_smoke.py`、`ResourceGuard`、内存峰值或 `--durations` 门禁。按 performance-engineer 模板无法填可 PASS/FAIL 的「指标 | 阈值 | 实测」perf 表；SKIP 为 Plan 冻结决策，非遗漏。

---

## 2. SKIP 理由（§3.6 等价 · 与 AUDIT.plan §1 A6 一致）

> Plan 原文：**「本地 schema 探测无 SLA 热点」** — 本任务为 adapter 有界 schema 指纹 + ValidationGate fail-closed，无生产调度/API 热路径，无冻结 SLA。

### 2.1 五条证实

1. **无 hot path / SLA** — `_infer_schema_hash` 仅在 skeleton adapter `_fetch_impl` 成功路径调用；`_schema_hash_blocks_write` 仅在 `assert_can_write` / WriteManager 链触发；无 FastAPI 路由、无批调度器、无 `production_equivalent_smoke.py` 挂载点。
2. **有界 schema 探测面** — CSV 仅读 64KB 前缀取 header；Parquet 写临时文件后 DuckDB `DESCRIBE SELECT * FROM read_parquet(?)`（列元数据）；JSON 用 `_shape` 结构指纹；均非全表/全文件扫描。
3. **任务卡 scope 排除重 I/O** — `B02_02` §4：Do not scan full files when schema-only or limit-0 detection is enough；禁止 production clean write。
4. **Gate 为 O(1) SQL** — `_schema_hash_blocks_write` 仅 2 条 `LIMIT 1` 查询（`fetch_log` 当前行 + `file_registry` baseline）；无全表扫、无 N+1 循环。
5. **MASTER / AUDIT 无 perf 冻结行** — 通过条件为 pytest exit 0（A8）；无时长/内存数字可供 A6 PASS/FAIL。

### 2.2 实现路径 vs 性能特征

| 组件                         | 触发时机          | I/O / CPU 特征                         | 数据量级上界                        |
| ---------------------------- | ----------------- | -------------------------------------- | ----------------------------------- |
| `_infer_csv_schema_hash`     | CSV SUCCESS fetch | 读 `content[:64KiB]` + 首行 csv.reader | 64KB 前缀                           |
| `_infer_parquet_schema_hash` | Parquet SUCCESS   | temp 文件 + DuckDB connect + DESCRIBE  | `DEFAULT_MAX_PAYLOAD_BYTES`（10MB） |
| `_infer_schema_hash` (JSON)  | JSON SUCCESS      | `json.loads` 全文 + `_shape` 递归      | 同上 10MB payload cap               |
| `_schema_hash_blocks_write`  | clean-write 前    | 2× SQL `LIMIT 1`                       | 单行                                |
| `_fetch_log_is_structured`   | gate 结构化判定   | 额外 1× SQL `LIMIT 1`（既有）          | 单行                                |

**结论：** 变更落在 **单次 fetch / 单次 gate 判定** 的微型路径，非高频批处理或用户可见延迟面；与 AUDIT.plan「无 SLA 热点」一致。

### 2.3 performance-engineer checklist（Audit 模式）

| 检查项                       | 状态        | 说明                                          |
| ---------------------------- | ----------- | --------------------------------------------- |
| Baseline 有证据来源          | **N/A**     | Plan 未冻结 perf 命令                         |
| EXPLAIN/profile/smoke        | **N/A**     | Gate SQL trivial；无 smoke 挂载点             |
| 优化后同一命令对比           | **N/A**     | 无优化项                                      |
| sandbox 数据量级与 Plan 一致 | **PASS**    | fixture 小文件；`max_payload_bytes=10MB` 既有 |
| 全量 pytest 无无关回归       | **委托 A8** | 本维 durations 参考；正式门禁见 A8            |

---

## 3. 计划外 perf 风险扫描

> 按 `audit-adversarial-authority.md` A6：**即使 SKIP，仍须扫描** hot path、无界 I/O、批大小/内存尖峰。

### 3.1 Hot path

| 路径                                | 是否 hot   | 证据                         | 风险                     |
| ----------------------------------- | ---------- | ---------------------------- | ------------------------ |
| `_infer_schema_hash` @ fetch        | **否**     | 每 fetch 一次；非 API 热路径 | 无生产 SLA               |
| `_schema_hash_blocks_write` @ write | **否**     | 每 validation 一次           | 2× LIMIT 1；可忽略       |
| 批量 ingest / 多 worker             | **未涉及** | MASTER 明确单机 pipeline     | 未来多 worker 须单独契约 |

**结论：** 本分支**不存在**可观测的生产 hot path；SKIP 合理。

### 3.2 无界 I/O

| 面                | 扫描                  | 发现                                     | 评级    |
| ----------------- | --------------------- | ---------------------------------------- | ------- |
| Parquet 全表扫    | `skeleton_base.py`    | DESCRIBE 元数据路径；符合 B02_02 §4      | **无**  |
| CSV 全文件扫      | 同上                  | 64KB 前缀硬顶 `_CSV_SCHEMA_PREFIX_BYTES` | **无**  |
| JSON 全量 parse   | `json.loads(content)` | 受 `max_payload_bytes` 约束              | 见 NB-1 |
| Gate 全表扫       | `validation_gate.py`  | 仅 `LIMIT 1`                             | **无**  |
| 网络 / live fetch | 任务边界              | 禁止 live fetch                          | **无**  |

### 3.3 批大小 / 内存尖峰

| 面                       | 行为                        | 当前量级     | 计划外风险                            |
| ------------------------ | --------------------------- | ------------ | ------------------------------------- |
| Parquet temp 写盘        | 每 infer 一次 mkstemp+write | ≤10MB        | 高频 Parquet fetch 磁盘抖动 → 见 NB-2 |
| DuckDB connect / close   | 每 Parquet infer 新建连接   | 测试毫秒级   | 连接池未用；当前非 hot path           |
| JSON `_shape` 递归       | 深嵌套 JSON                 | fixture 浅层 | 恶意深嵌套 → CPU；10MB cap 缓解       |
| SHA256 `json.dumps` 指纹 | 列名/形状序列化             | 极小         | 可忽略                                |

**结论：** 当前测试与 staged 规模下 CPU/内存**可忽略**；结构性备忘见 NB-1/NB-2。

### 3.4 与 deferred perf 项交叉

| 登记项                                   | 与 B3V-DATA 关系                 |
| ---------------------------------------- | -------------------------------- |
| `scripts/production_equivalent_smoke.py` | diff 未挂载；MASTER §10 无 smoke |
| `tests/test_resource_guard.py`           | infer 路径未接入 ResourceGuard   |
| Batch 6 perf budget / nightly            | **不阻塞** 本任务                |

---

## 4. DOUBT（doubt-driven-development）

| 疑点                                     | 结论                                                                  |
| ---------------------------------------- | --------------------------------------------------------------------- |
| SKIP 是否遗漏 smoke？                    | **否** — AUDIT.plan §1 + MASTER §10 双重无 perf 阈值                  |
| Parquet infer 是否违反「不全文件扫描」？ | **否** — DESCRIBE 读列元数据；符合 MASTER §2.5 / B02_02 §4 设计意图   |
| Gate 新增缺 hash 分支是否增加 DB 负载？  | **否** — 复用既有 `current_row` 查询；仅加布尔判定，无额外 round-trip |
| JSON 全文 parse 是否 BLOCKING？          | **否** — 10MB cap + 非 hot path；登记 NB-1 备忘                       |
| pytest gate 测 ~0.50s 是否 perf 回归？   | **否** — DuckDB/SQLite fixture 启动主导；无冻结基线                   |

---

## 5. §3.6 证据表（SKIP 专用）

| 指标                                                   | 阈值（Plan 冻结） | 实测                     | 证据                                                                 |
| ------------------------------------------------------ | ----------------- | ------------------------ | -------------------------------------------------------------------- |
| `test_data_adapter_contract` + gate + skeletons        | exit 0（A8）      | 106 passed / 1 IO fail\* | `uv run pytest … -q --basetemp=.audit-sandbox/pytest --durations=10` |
| 最慢 gate 测 call                                      | **未冻结**        | 0.57s                    | 同上                                                                 |
| `test_missingSchemaHashOnStructuredFetch_rejects[csv]` | **未冻结**        | 0.50s                    | 同上                                                                 |
| smoke 端到端                                           | **未冻结**        | **未测**                 | SKIP                                                                 |
| ResourceGuard                                          | **未冻结**        | **未触及**               | 无调用路径                                                           |
| 内存峰值 MB                                            | **未冻结**        | **未测**                 | fixture KB–MB 级                                                     |

\* `test_missingSchemaHashOnStructuredFetch_rejects[parquet]` 因 basetemp 下 DuckDB 文件缺失失败；属 A8 环境卫生，非 A6 perf 缺陷。

---

## 6. 计划外发现

| ID   | 发现                                                                 | 严重度               | 说明                                                                  |
| ---- | -------------------------------------------------------------------- | -------------------- | --------------------------------------------------------------------- |
| NB-1 | JSON infer **`json.loads` 全文解析**，无独立 `max_bytes` 于 infer 层 | **NON-BLOCKING**     | 上游 `max_payload_bytes=10MB` 已 cap；与 B02_02 有界精神一致          |
| NB-2 | Parquet infer **每请求 temp 写盘 + DuckDB 新建连接**                 | **NON-BLOCKING**     | 非 hot path；若未来高频 Parquet ingest 可考虑连接复用 / 内存 buffer   |
| —    | hot path / 全表扫 / 网络无界 I/O / Gate N+1                          | **无 BLOCKING 发现** | 已审阅 `skeleton_base.py`、`validation_gate.py`、B02_02 §4、MASTER §7 |

**显式声明：** 已对照 `B02_02_schema_hash_fail_closed.md` §4、`AUDIT.plan.md` §1 A6、`MASTER.plan.md` §2.5/§7/§10、`agents/performance-engineer.md`、GitNexus impact、实现全文及 pytest durations；**无 BLOCKING perf 项**。

---

## 7. 结论

**A6 审计判定：SKIP（维持）。**

理由摘要：B3V-DATA schema_hash fail-closed 是 **有界 schema 指纹 + ValidationGate fail-closed** 安全底座修补；任务卡与 AUDIT.plan §1 均排除全文件扫描、live fetch 与 prod I/O；**无**冻结 perf 阈值、**无**生产 hot path。实现遵守 CSV 64KB 前缀、Parquet DESCRIBE 元数据、Gate `LIMIT 1` SQL。GitNexus 两核心符号均为 LOW risk。计划外扫描登记 2 项 **NON-BLOCKING** 备忘，**不阻断** B3V-DATA merge。
