# MASTER 计划 — B3V-DATA schema_hash fail-closed

> **Execute 入口** — 无 production clean write；registry 闭合归主会话。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`

---

## 0. 元信息

| 字段                      | 值                                    |
| ------------------------- | ------------------------------------- |
| 任务 slug                 | `round3v-schema-hash-fail-closed`     |
| Playbook ID               | B3V-DATA · Manifest `B3V-C02`         |
| 分支                      | `fix/round3v-schema-hash-fail-closed` |
| Worktree                  | `../quant-monitor-desk-wt-b3v-data`   |
| 模型                      | `composer-2.5`                        |
| VR                        | `VR-DATA-001`                         |
| manifest_protocol_version | `3`                                   |
| analysis_waiver           | `false`                               |
| 原计划                    | `research/original-plan-trace.md`     |

### Batch 3V 边界（Playbook §2.5 / §2.6）

| Owns                                                    | Must not                                         |
| ------------------------------------------------------- | ------------------------------------------------ |
| `validation_gate.py` + adapter `schema_hash` 路径       | 全文件扫描                                       |
| `data_adapter_contract.md` schema_hash 段               | production clean write                           |
| `skeleton_base.py` `_infer_schema_hash` / `_fetch_impl` | db-inspect / RawStore / sync / registry / layer5 |
| `tests/test_db_validation_gate.py` 等本任务测试         | 为便利 weaken gate（B3V-AUD-05）                 |

### Failure modes / 回滚

| 场景                        | 处理                       |
| --------------------------- | -------------------------- |
| 触发 production clean write | HARD_STOP；revert          |
| 修改 forbidden 文件组       | 立即停止                   |
| 削弱 gate 负向测试目的      | 停止条件 #4                |
| 回滚                        | revert 本分支 allowed 文件 |

### 0.1 门控速查

| 项        | 值                                                            |
| --------- | ------------------------------------------------------------- |
| 怎么测    | §9 RED→GREEN；任务卡 §7 pytest 子集 + 全量 `uv run pytest -q` |
| 怎么验收  | §6 Tier A + 任务卡 §7                                         |
| 什么叫过  | AC-DATA-01..05（registry 除外）                               |
| prod-path | Tier A only（无 live fetch）                                  |

### 0.3 Execute 强制必读

Phase 0 **逐条 Read `implement.jsonl`**；先读 `research/integration-ledger.md`。

### 0.3a Ponytail

MUST Read `.cursor/rules/ponytail.mdc`；复用 `_shape` JSON 指纹；CSV stdlib；Parquet DuckDB LIMIT 0；无新依赖。

### 0.3b 测试纪律

五字段 docstring；RED 必须先 FAIL；禁止削弱测试目的。

### Source Context Index（Playbook §3.1 + §3.3）

#### §3.1 共用底座

| 路径                                                              | 摘要                   | implement |
| ----------------------------------------------------------------- | ---------------------- | --------- |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md`                                | §2.5 锁、§4 正式线     | [x]       |
| `BATCH_3V_TASK_CARD_MANIFEST.md`                                  | C02 路由               | [x]       |
| `BATCH_3V_HARDENING_RULES.md`                                     | 禁 production 措辞     | [x]       |
| `BATCH_3V_ADVERSARIAL_AUDIT.md`                                   | B3V-AUD-05 gate weaken | [x]       |
| `ROUND_3_VERIFIED_AUDIT_CLEANUP/README.md`                        | Round 3V 入口          | [x]       |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                               | R3V-B02-DATA-01        | [x]       |
| `GLOBAL_EXECUTION_RULES.md` 等 ×3                                 | 全局纪律               | [x]       |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | VR-DATA-001            | [x]       |
| Registry 三件套 + `UNRESOLVED_ITEM_TASK_COVERAGE.md`              | **只读**；闭合主会话   | [x]       |

#### §3.3 B3V-DATA

| 路径                                           | 摘要                                                | implement  |
| ---------------------------------------------- | --------------------------------------------------- | ---------- |
| `B02_02_schema_hash_fail_closed.md`            | 权威 AC                                             | trace only |
| `data_adapter_contract.md`                     | 结构化 schema_hash                                  | [x]        |
| `skeleton_base.py`                             | infer + fetch                                       | [x]        |
| `validation_gate.py`                           | fail-closed                                         | [x]        |
| `adapters/__init__.py` + `source_registry.py`  | adapter 注册邻接（playbook `registry.py` 路径纠偏） | [x]        |
| `data_quality_rules.yaml`                      | SCHEMA_DRIFT                                        | [x]        |
| `write_contract.yaml`                          | schema_hash_changed                                 | [x]        |
| `resource_limits.yaml`                         | 有界读取                                            | [x]        |
| `test_db_validation_gate.py`                   | gate 测试                                           | [x]        |
| `test_data_adapter_contract.py`                | 契约测试                                            | [x]        |
| `test_adapter_skeletons.py`                    | adapter 测试                                        | [x]        |
| `test_data_quality_validator.py`               | 质量邻接                                            | [x]        |
| `docs/modules/data_validation_and_conflict.md` | 模块语义                                            | [x]        |

---

## 1. 目标与目的

### 1.1 目标

结构化 JSON/CSV/Parquet 的 `SUCCESS` 抓取必须携带可信 `schema_hash`；ValidationGate 在 hash 缺失或漂移时 fail-closed，阻止 clean-write。

### 1.2 目的

关闭 verified audit `VR-DATA-001`，消除「无 schema_hash 绕过 schema drift 检查」的底座风险。

### 1.3 前置

- post Batch 01 `master` 基线
- B3V 协调包 playbook 已提交

### 1.4 约束

- 无 live fetch；无 production clean write；无全文件扫描
- **不 Execute registry 闭合**（B02-DATA-05 → 主会话）
- **未改什么（Playbook §8.2）：** db-inspect 契约、WriteManager 模式表、RawStore、sync 矩阵、registry 行、Layer5 runtime。

### 1.5 停止条件

| #   | 事件                                 | 处理                    |
| --- | ------------------------------------ | ----------------------- |
| 1   | 修改 RawStore/sync/registry/layer5   | 禁止；退回 Plan         |
| 2   | 生产库 clean write 或 migration      | HARD_STOP               |
| 3   | scope 偏离 B02_02                    | 退回 Plan               |
| 4   | RED 异常 / 削弱负向测试目的          | 停当前 §9 步            |
| 5   | GitNexus impact HIGH/CRITICAL 未确认 | 停；主会话裁定          |
| 6   | 为过关删除 gate 拒绝分支             | HARD_STOP（B3V-AUD-05） |

### 1.6 原计划归并

| 来源                       | 内容                         |
| -------------------------- | ---------------------------- |
| `B02_02`                   | DATA-01..04 + §6 测试        |
| `BATCH_3V_HARDENING_RULES` | 禁 production 语言           |
| B02-DATA-05                | **deferred** 主会话 registry |

---

## 2. 架构与设计

**2.1 架构** Adapter → fetch_log/file_registry → validation_report → WriteManager → DbValidationGate

**2.2 设计**

1. **契约层**：定义 structured file types 与 SUCCESS 必填 `schema_hash`；schemaless 契约列举豁免（不改 registry yaml）。
2. **Adapter 层**：扩展 `_infer_schema_hash`；infer 失败或结构化 SUCCESS 无 hash → 非 SUCCESS。
3. **Gate 层**：`_schema_hash_blocks_write` 对 structured fetch：current hash NULL → block；baseline 存在且 current 不同 → block（既有）；quality_flags `SCHEMA_DRIFT` → block（既有）。

**2.3 规则** GLOBAL + BATCH_3V_HARDENING §3–§4 + Playbook §2.2

**2.4 契约** `data_adapter_contract.md` · `write_contract.yaml` · `data_quality_rules.yaml`

**2.5 决策** 有界推导优先于全量读；DuckDB 用于 Parquet schema 探测（已在依赖树）；registry schemaless 字段留主会话

---

## 3. 需求与场景矩阵

| 场景# | Given                      | When             | Then                   | AC         | 测试      | Tier |
| ----- | -------------------------- | ---------------- | ---------------------- | ---------- | --------- | ---- |
| S1    | CSV SUCCESS row_count>0    | infer 成功       | schema_hash 非空       | AC-DATA-02 | adapter   | B    |
| S2    | Parquet SUCCESS            | infer 成功       | schema_hash 非空       | AC-DATA-02 | adapter   | B    |
| S3    | 结构化 fetch_log hash=NULL | assert_can_write | ValidationRejected     | AC-DATA-03 | gate      | B    |
| S4    | 损坏 CSV/Parquet           | adapter fetch    | FAILED 或 SCHEMA_DRIFT | AC-DATA-04 | adapter   | B    |
| S5    | baseline≠current hash      | assert_can_write | ValidationRejected     | AC-DATA-05 | gate 回归 | B    |

**3.1 需求说明**：结构化源不得 silent 缺 hash；gate 不得 fail-open。

**3.2 范围** in: 契约、infer、gate、测试 · out: registry 闭合、RawStore、sync、layer5

---

## 4. 预期结果

| #          | 预期结果                        | 验证链       |
| ---------- | ------------------------------- | ------------ |
| AC-DATA-01 | 契约写明结构化 schema_hash 要求 | S1–S2 → §9.1 |
| AC-DATA-02 | CSV/Parquet 有 hash             | S1–S2 → §9.2 |
| AC-DATA-03 | Gate 缺 hash 拒绝               | S3 → §9.3    |
| AC-DATA-04 | 损坏文件不可写                  | S4 → §9.4    |
| AC-DATA-05 | 漂移仍拒绝                      | S5 → §9.3    |

---

## 5. 测试契约

### 5.0 规范

1. 五字段 docstring
2. 负向断言必须保留（B3V-AUD-05）
3. RED 后 GREEN 前 Read karpathy + testing-guidelines

### 5.1 测试文件路径

| 测试文件路径                          | 目标文件             | 测试目的（冻结）                            | §9       |
| ------------------------------------- | -------------------- | ------------------------------------------- | -------- |
| `tests/test_adapter_skeletons.py`     | `skeleton_base.py`   | CSV/Parquet infer + corrupt 不 SUCCESS      | 9.2, 9.4 |
| `tests/test_db_validation_gate.py`    | `validation_gate.py` | 缺 hash fail-closed + 漂移回归              | 9.3      |
| `tests/test_data_adapter_contract.py` | 契约                 | 结构化 SUCCESS 须 schema_hash（若在校验层） | 9.1      |

### 5.2 成功怎么测 / 失败怎么测

| 能力              | 成功怎么测         | 失败怎么测           | 场景  |
| ----------------- | ------------------ | -------------------- | ----- |
| CSV infer         | hash 稳定非空      | corrupt → 非 SUCCESS | S1,S4 |
| Parquet infer     | hash 非空          | corrupt → 非 SUCCESS | S2,S4 |
| Gate missing hash | ValidationRejected | 允许写               | S3    |
| Gate drift        | ValidationRejected | 允许写               | S5    |

### 5.3 用例设计

| 测试文件                     | test\_\* 名称                                          | 断言语义                     | 场景 | RED 命令                                                                                       |
| ---------------------------- | ------------------------------------------------------ | ---------------------------- | ---- | ---------------------------------------------------------------------------------------------- |
| `test_adapter_skeletons.py`  | `test_inferSchemaHash_csvHeader_producesStableHash`    | CSV header → 非空 hash       | S1   | `pytest tests/test_adapter_skeletons.py::test_inferSchemaHash_csvHeader_producesStableHash -v` |
| `test_adapter_skeletons.py`  | `test_inferSchemaHash_parquetColumns_producesHash`     | Parquet 列指纹               | S2   | 同上模块 ::parquet                                                                             |
| `test_adapter_skeletons.py`  | `test_skeletonFetch_corruptCsv_notSuccessEligible`     | status≠SUCCESS 或无可写 hash | S4   | 同上 ::corruptCsv                                                                              |
| `test_adapter_skeletons.py`  | `test_skeletonFetch_corruptParquet_notSuccessEligible` | 同上 Parquet                 | S4   | 同上 ::corruptParquet                                                                          |
| `test_db_validation_gate.py` | `test_missingSchemaHashOnStructuredFetch_rejects`      | ValidationRejected           | S3   | `pytest tests/test_db_validation_gate.py::test_missingSchemaHashOnStructuredFetch_rejects -v`  |
| `test_db_validation_gate.py` | `test_schemaHashDriftWithoutApproval_rejects`          | 既有回归                     | S5   | 既有                                                                                           |

### 5.4 四层测试

| 层   | 环境 | 命令                  | 通过   |
| ---- | ---- | --------------------- | ------ |
| 单元 | ci   | 任务卡 §7 pytest 子集 | exit 0 |
| 集成 | ci   | `uv run pytest -q`    | exit 0 |
| 管道 | —    | N/A                   | —      |
| E2E  | —    | N/A                   | —      |

---

## 6. 验证

| Tier | 环境     | 命令                                                                                    | 场景   | 通过   |
| ---- | -------- | --------------------------------------------------------------------------------------- | ------ | ------ |
| A    | local/ci | `uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py -q` | S1–S5  | exit 0 |
| A+   | local/ci | `uv run pytest tests/test_adapter_skeletons.py tests/test_data_quality_validator.py -q` | S1–S5  | exit 0 |
| B    | local/ci | `uv run ruff check backend/app/datasources backend/app/db tests`                        | —      | exit 0 |
| C    | local/ci | `uv run pytest -q`                                                                      | 全回归 | exit 0 |

**6.1 交接门槛**：§9 证据齐 · §5.1 用例存在 · §1.5 未触发 · registry **不**在本任务勾选

---

## 7. Red Flags

| 风险                | 预防                      |
| ------------------- | ------------------------- |
| Gate weaken         | §5.3 负向冻结             |
| 全文件 Parquet 扫描 | DuckDB LIMIT 0 / metadata |
| 与 B3V-STOR 冲突    | 只读 RawStore             |
| registry 并发编辑   | Execute 禁止              |

---

## 8. 实现顺序

| 序  | ID      | 交付物                         | 依赖    | AC            |
| --- | ------- | ------------------------------ | ------- | ------------- |
| 1   | DATA-01 | 契约 schema_hash 段            | —       | AC-DATA-01    |
| 2   | DATA-02 | CSV/Parquet infer + fetch 守卫 | DATA-01 | AC-DATA-02,04 |
| 3   | DATA-03 | Gate fail-closed               | DATA-01 | AC-DATA-03,05 |
| 4   | DATA-04 | 损坏文件负向测试 GREEN         | DATA-02 | AC-DATA-04    |

---

## 9. 实现步骤

### 9.0 Boot

**必读**：§0.3 Execute 强制必读 → 逐条 `implement.jsonl`；先读 `research/integration-ledger.md`。

| RED/GREEN                                                                           | 证据                            | Skill                             | [x] |
| ----------------------------------------------------------------------------------- | ------------------------------- | --------------------------------- | --- |
| `uv run pytest tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q` | `9.0-red.txt` / `9.0-green.txt` | trellis-execute · gitnexus-impact | [x] |

### 9.1 DATA-01 — 契约

| 字段  | 内容                                            |
| ----- | ----------------------------------------------- |
| RED   | 契约测试（若有）或文档对照测试 RED              |
| GREEN | 更新 `data_adapter_contract.md` structured 规则 |
| Skill | TDD · karpathy · testing-guidelines             |
| 证据  | `9.1-red.txt` / `9.1-green.txt`                 |

### 9.2 DATA-02 — Adapter infer

| 字段   | 内容                                                    |
| ------ | ------------------------------------------------------- |
| RED    | `test_inferSchemaHash_csvHeader_*` + parquet FAIL       |
| GREEN  | `skeleton_base._infer_schema_hash` + `_fetch_impl` 守卫 |
| impact | `_infer_schema_hash` upstream（LOW）                    |
| 证据   | `9.2-red.txt` / `9.2-green.txt`                         |

### 9.3 DATA-03 — ValidationGate

| 字段   | 内容                                                   |
| ------ | ------------------------------------------------------ |
| RED    | `test_missingSchemaHashOnStructuredFetch_rejects` FAIL |
| GREEN  | `_schema_hash_blocks_write` fail-closed                |
| impact | `_schema_hash_blocks_write`（LOW）                     |
| 证据   | `9.3-red.txt` / `9.3-green.txt`                        |

### 9.4 DATA-04 — Corrupt 负向

| 字段  | 内容                             |
| ----- | -------------------------------- |
| RED   | corrupt csv/parquet tests FAIL   |
| GREEN | adapter 返回 FAILED/SCHEMA_DRIFT |
| 证据  | `9.4-red.txt` / `9.4-green.txt`  |

---

## 10. Execute 交接 DoD

- [x] §9 证据齐 · 任务卡 §7 pytest 子集全绿 · §11 Skill `[x]` · `validate-execute-handoff` 0
- [x] **不** finish-work · **不** registry 闭合

---

## 11. Execute Skill 冻结

| Skill                      | 本任务   | 绑定       | 已读 | 已执行 |
| -------------------------- | -------- | ---------- | ---- | ------ |
| trellis-execute            | 必做     | Boot       | [x]  | [x]    |
| test-driven-development    | 必做     | §9 RED     | [x]  | [x]    |
| incremental-implementation | 必做     | §9 SLICE   | [x]  | [x]    |
| karpathy-guidelines        | 必做     | GREEN      | [x]  | [x]    |
| testing-guidelines         | 必做     | 写测       | [x]  | [x]    |
| gitnexus-impact            | 必做     | 改 symbol  | [x]  | [x]    |
| systematic-debugging       | 条件     | DEBUG      | [ ]  | [ ]    |
| trellis-implement          | inline   | Execute    | [x]  | [x]    |
| trellis-check              | **不用** | → Audit A1 | —    | —      |

路径见 `execute-skill-paths.yaml`。
