# MASTER 计划 — B3V-OPS Contract Drift & Write Modes

> **Execute 入口** — 契约/runtime 对齐；**不得** production clean write / live fetch / registry 闭合。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`  
> **必须读原文：** `B02_01_contract_drift_and_write_modes.md`（摘要见 Source Context Index）

---

## 0. 元信息

| 字段                      | 值                                                             |
| ------------------------- | -------------------------------------------------------------- |
| 任务 slug                 | `round3v-contract-drift-write-modes`                           |
| Playbook / Manifest       | B3V-OPS · `B3V-C01`                                            |
| 分支                      | `fix/round3v-contract-drift-write-modes`                       |
| Worktree                  | `../quant-monitor-desk-wt-b3v-ops`                             |
| 模型                      | `composer-2.5`                                                 |
| manifest_protocol_version | `3`                                                            |
| analysis_waiver           | `false`                                                        |
| skip_phase4_reason        | 无新 package · 无 ≥2 caller 新公共 API · 无 schema migration   |
| 原计划                    | `research/source-index.md` · `research/original-plan-trace.md` |

### Batch 3V 边界（Playbook §2.5 / §2.6 · hardening §3）

| Owns                                                | Must not                                         |
| --------------------------------------------------- | ------------------------------------------------ |
| `ops_db_inspect_contract.yaml` · `db_inspector.py`  | `validation_gate` · RawStore · sync · layer5     |
| `write_contract.yaml` · WriteManager 模式语义       | reserved 模式实现 · production clean write       |
| `tests/test_contract_drift_ops_write.py` + 相关回归 | registry 三件套直接闭合 · migration · live fetch |

### Failure modes / 回滚

| 场景                  | 处理                                        |
| --------------------- | ------------------------------------------- |
| inspect 非 read_only  | 中止；revert                                |
| reserved 模式意外写行 | 中止；不勾 GREEN                            |
| 改 forbidden 文件组   | 立即停止                                    |
| 回滚                  | revert 本分支 allowed 文件；无 DB migration |

### 0.1 门控速查

| 项        | 值                                 |
| --------- | ---------------------------------- |
| 怎么测    | §9 RED→GREEN；任务卡 §7 命令       |
| 怎么验收  | §10 Tier A                         |
| 什么叫过  | §2 AC 全绿 + drift/parity 测       |
| prod-path | 本任务 **无** Tier B（无写库验收） |

### 0.3 Execute 强制必读

Phase 0 **逐条 Read `implement.jsonl`**；先读 `research/integration-ledger.md`。

### 0.3a Ponytail

MUST Read `.cursor/rules/ponytail.mdc`；优先 YAML loader 删重复常量；WriteManager 仅必要早拒/消息 touch。

### 0.3b 测试纪律

五字段 docstring；RED 必须先 FAIL；禁止削弱漂移测目的。

### Source Context Index（Playbook §3.1 + §3.2）

#### §3.1 共用底座

| 路径                                                              | 摘要                    | implement |
| ----------------------------------------------------------------- | ----------------------- | --------- |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md`                                | §3.1+§3.2+§4 正式线     | [x]       |
| `BATCH_3V_TASK_CARD_MANIFEST.md`                                  | C01 依赖与分支锁        | [x]       |
| `BATCH_3V_HARDENING_RULES.md`                                     | 禁 production-live 措辞 | [x]       |
| `BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`                       | Batch 3V 入口           | [x]       |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                               | Round 3V.1 血缘         | [x]       |
| `GLOBAL_EXECUTION_RULES.md` 等 ×3                                 | 全局纪律                | [x]       |
| `staged_acceptance_policy.md`                                     | 分层验收                | [x]       |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | VR 路由                 | [x]       |
| Registry 三件套 + `UNRESOLVED_ITEM_TASK_COVERAGE.md`              | **只读**；本任务不闭合  | [x]       |

#### §3.2 B3V-OPS（C01）

| 路径                                           | 摘要                                                | implement |
| ---------------------------------------------- | --------------------------------------------------- | --------- |
| `B02_01_contract_drift_and_write_modes.md`     | **必须读原文** · VR AC                              | [x]       |
| `specs/contracts/ops_db_inspect_contract.yaml` | key_tables + deferred SSOT                          | [x]       |
| `docs/modules/ops_db_inspect.md`               | Playbook 债务；仓库无文件；SSOT=YAML+`db_inspector` | [x]       |
| `docs/ops/db_inspect_cli.md`                   | CLI 漂移对照；引用 inspect 契约                     | [x]       |
| `specs/contracts/write_contract.yaml`          | 写模式契约                                          | [x]       |
| `specs/contracts/runtime_versions.md`          | runtime 锁                                          | [x]       |
| `backend/app/ops/db_inspector.py`              | inspect 运行时                                      | [x]       |
| `backend/app/db/write_manager.py`              | SUPPORTED/UNSUPPORTED                               | [x]       |
| `tests/test_ops_db_inspector.py`               | inspect 回归                                        | [x]       |
| `tests/test_write_manager.py`                  | write 回归                                          | [x]       |
| `tests/test_db_validation_gate.py`             | gate 回归（只跑，不改）                             | [x]       |
| `tests/test_contract_drift_ops_write.py`       | 漂移/parity 新测                                    | [x]       |

---

## 1. 目标与目的

### 1.1 目标

- `ops_db_inspect_contract.yaml` 成为 db-inspect `key_tables` 与 `deferred_item_mapping` 唯一真源（运行时加载）。
- `write_contract.yaml` 明确 `implemented_modes` / `reserved_modes`；与 `WriteManager` 一致。
- 漂移与 parity 测试可检测契约变更未同步代码。

### 1.2 目的

关闭 verified audit `VR-OPS-001`、`VR-WRITE-001` 的**技术证据**（registry 行由主会话 Batch 收口）。

### 1.3 前置

- Post Batch 01 master 已合并。
- 无 B3V-DATA / B3V-STOR 硬依赖；可与 B3V-REG 并行。

### 1.4 约束

- db-inspect 只读；无网络；无 DB mutation。
- 不实现 reserved 写模式；不改 production clean write 权限。

### 1.5 停止条件

| #   | 事件                                   | 处理                       |
| --- | -------------------------------------- | -------------------------- |
| 1   | 触发写库 / migration                   | 中止                       |
| 2   | inspect 打开非 read_only               | 中止                       |
| 3   | scope 超出任务卡 allowed               | 退回 Plan                  |
| 4   | RED 异常（非本步预期 FAIL）            | 停当前 §9 步               |
| 5   | **GitNexus impact HIGH 且未跑 impact** | 禁止改 `WriteManager` 符号 |
| 6   | **Agent 编辑 registry 三件套**         | 立即停止（主会话专属）     |
| 7   | 为绿削弱漂移测 purpose                 | 停止；回 Plan              |

### 1.6 原计划归并

| 来源                                       | 内容                                         |
| ------------------------------------------ | -------------------------------------------- |
| `B02_01_contract_drift_and_write_modes.md` | VR-OPS/WRITE；六切片中五切片执行，CLOSE 排除 |
| `BATCH_3V_HARDENING_RULES.md`              | TDD · ponytail · 禁 production-ready         |
| 纠偏                                       | `research/source-index.md` §A                |

---

## 2. 架构与设计

**2.1 架构：** Ops 只读 inspect 路径与 DB WriteManager 写路径分离；契约在 `specs/contracts/`。  
**2.2 设计：** `db_inspector` 启动时加载 YAML → 暴露 `KEY_TABLES` / `DEFERRED_ITEM_MAPPING`；`write_contract` 顶层 `implemented_modes` + `reserved_modes`；`write_request.write_mode` enum = 并集。  
**2.3 规则：** GLOBAL + Batch 3V hardening；db-inspect `duckdb_open_mode: read_only`。  
**2.4 契约：** `ops_db_inspect_contract.yaml` · `write_contract.yaml` · `runtime_versions.md`。  
**2.5 决策：** 无 Round DECISIONS.md；以任务卡 + hardening 为准。

### 2.6 预期结果（AC）

| AC                | 预期结果                                       | 验证链              |
| ----------------- | ---------------------------------------------- | ------------------- |
| AC-OPS-DRIFT      | YAML 与 inspect 常量/输出模型一致；漂移测绿    | S1 → §9.1–9.2 → §10 |
| AC-WRITE-SPLIT    | 契约分 implemented/reserved；parity 绿         | S2 → §9.3–9.4 → §10 |
| AC-WRITE-RESERVED | reserved 稳定拒绝、无写副作用                  | S3 → §9.5 → §10     |
| AC-BOUND          | 无 DB 写 / 无 reserved 实现 / 无 registry 闭合 | §3.2 · Audit        |
| AC-EVIDENCE       | execute-evidence 齐；VR 可主会话登记           | §11                 |

---

## 3. 需求与场景矩阵

| 场景# | Given                 | When                 | Then                           | AC                | 测试（§5.2）          | 验证 Tier |
| ----- | --------------------- | -------------------- | ------------------------------ | ----------------- | --------------------- | --------- |
| S1    | 契约 YAML 与代码同步  | 跑 ops 漂移测        | key_tables + deferred 全等     | AC-OPS-DRIFT      | 改 YAML 无代码 → FAIL | Tier A    |
| S2    | write_contract 已分栏 | 跑 parity 测         | implemented == SUPPORTED_MODES | AC-WRITE-SPLIT    | 契约少模式 → FAIL     | Tier A    |
| S3    | reserved 在契约中     | `WriteManager.write` | ValueError + 无行写入          | AC-WRITE-RESERVED | 每 reserved 模式      | Tier A    |

**3.1 需求说明：** 文档与代码单一真源；漂移可机检。  
**3.2 范围：** in — 上表 allowed · out/defer — manual_patch 实现、production clean write、validation_gate、registry 闭合、B02-CLOSE-01

| out / defer                         | 原因                  |
| ----------------------------------- | --------------------- |
| `B02-CLOSE-01` registry             | Plan 门禁：主会话收口 |
| `validation_gate` / RawStore / sync | 他卡所有权            |
| reserved 模式运行时                 | 任务卡 §4 禁止        |

---

## 4. 预期结果

见 §2.6。

---

## 5. 测试契约

> purpose **冻结**；改 purpose 须回 Plan。

### 5.0 规范

1. 五字段：`覆盖范围` / `测试对象` / `目的/目标` / `验证点` / `失败含义`
2. 漂移测须对 **全量** key_tables 与 deferred_item_mapping 断言，不得仅轴表子集

### 5.1 测试文件路径（写死）

| 测试文件路径                             | 目标文件                      | 测试目的（冻结）                 | §9 步   |
| ---------------------------------------- | ----------------------------- | -------------------------------- | ------- |
| `tests/test_contract_drift_ops_write.py` | `db_inspector.py` + contracts | YAML↔runtime 漂移与 write parity | 9.2–9.5 |
| `tests/test_ops_db_inspector.py`         | `db_inspector.py`             | 只读 inspect 回归                | 9.0     |
| `tests/test_write_manager.py`            | `write_manager.py`            | 写路径回归                       | 9.0     |
| `tests/test_db_validation_gate.py`       | validation gate               | 未改 gate 回归                   | 9.0     |

### 5.2 成功/失败语义

| 能力                       | 成功怎么测                             | 失败怎么测                   | 场景 |
| -------------------------- | -------------------------------------- | ---------------------------- | ---- |
| ops 漂移                   | 运行时表/deferred 与 YAML 相等         | 仅改 YAML 一行 → pytest FAIL | S1   |
| write parity (implemented) | `implemented_modes == SUPPORTED_MODES` | 契约删 `append_only` → FAIL  | S2   |
| write parity (reserved)    | `reserved_modes == UNSUPPORTED_MODES`  | 契约多 reserved → FAIL       | S2   |
| reserved 拒绝              | 每 reserved `write()` 抛约定错误       | 若执行 INSERT → FAIL         | S3   |

### 5.3 用例设计

| 测试文件                           | `test_*` 名称                                            | 断言语义                           | 场景 | RED 命令                                                                                    |
| ---------------------------------- | -------------------------------------------------------- | ---------------------------------- | ---- | ------------------------------------------------------------------------------------------- |
| `test_contract_drift_ops_write.py` | `test_opsInspect_keyTables_matchContract`                | 集合与顺序与 YAML 一致             | S1   | `pytest tests/test_contract_drift_ops_write.py::test_opsInspect_keyTables_matchContract -v` |
| 同上                               | `test_opsInspect_deferredMapping_matchContract`          | deferred id + evidence_fields 一致 | S1   | `pytest …::test_opsInspect_deferredMapping_matchContract -v`                                |
| 同上                               | `test_writeContract_implementedModes_matchWriteManager`  | implemented == SUPPORTED_MODES     | S2   | `pytest …::test_writeContract_implementedModes_matchWriteManager -v`                        |
| 同上                               | `test_writeContract_reservedModes_matchUnsupportedModes` | reserved == UNSUPPORTED_MODES      | S2   | `pytest …::test_writeContract_reservedModes_matchUnsupportedModes -v`                       |
| 同上                               | `test_writeManager_reservedModes_rejectWithoutWrite`     | 各 reserved ValueError + 行数不变  | S3   | `pytest …::test_writeManager_reservedModes_rejectWithoutWrite -v`                           |

### 5.4 四层测试

| 层   | 环境     | 命令                                                                                                                                                  | 通过   |
| ---- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 单元 | local/ci | `uv run pytest tests/test_contract_drift_ops_write.py tests/test_ops_db_inspector.py tests/test_write_manager.py tests/test_db_validation_gate.py -q` | exit 0 |
| 集成 | local/ci | 同上 + `uv run ruff check backend/app/ops backend/app/db tests`                                                                                       | exit 0 |
| 管道 | N/A      | 本任务无 prod-path 写库                                                                                                                               | —      |
| E2E  | N/A      | 无 live fetch                                                                                                                                         | —      |

---

## 6. 验证

| Tier | 环境     | 命令                                                                                                                                                  | 场景  | 通过条件 | 勾  |
| ---- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | -------- | --- |
| A    | local/ci | `uv sync --locked`                                                                                                                                    | —     | exit 0   | [x] |
| A    | local/ci | `uv run pytest tests/test_ops_db_inspector.py tests/test_write_manager.py tests/test_db_validation_gate.py tests/test_contract_drift_ops_write.py -q` | S1–S3 | exit 0   | [x] |
| A    | local/ci | `uv run ruff check backend/app/ops backend/app/db tests`                                                                                              | —     | exit 0   | [x] |

**6.1 交接门槛：** §9 证据齐 · §5.1 文件已建 · §1.5 未触发 · **未** finish-work

---

## 7. Red Flags

| 风险                    | 预防                         |
| ----------------------- | ---------------------------- |
| WriteManager HIGH blast | 每步 `impact()`；最小 diff   |
| 双份常量残留            | OPS-01 删字面量，只留 loader |
| 水平合并 VR             | §8 五切片顺序                |
| registry agent 闭合     | 停止条件 #6                  |
| 假绿漂移测              | RED 必须先 FAIL              |

---

## 8. 实现顺序（垂直切片）

| 序  | ID       | 交付物（完标准）                                           | 依赖     | AC                |
| --- | -------- | ---------------------------------------------------------- | -------- | ----------------- |
| 1   | OPS-01   | YAML loader；`KEY_TABLES`/`DEFERRED_ITEM_MAPPING` 来自契约 | —        | AC-OPS-DRIFT      |
| 2   | OPS-02   | 漂移测 key_tables + deferred 全量                          | OPS-01   | AC-OPS-DRIFT      |
| 3   | WRITE-01 | `write_contract` implemented/reserved 分栏                 | —        | AC-WRITE-SPLIT    |
| 4   | WRITE-02 | parity 测 implemented == SUPPORTED_MODES                   | WRITE-01 | AC-WRITE-SPLIT    |
| 5   | WRITE-03 | reserved 稳定拒绝测                                        | WRITE-01 | AC-WRITE-RESERVED |

---

## 9. 实现步骤（RED/GREEN）

### 9.0 Boot

> **必读：** §0.3 逐条 `implement.jsonl`；先读 `research/integration-ledger.md`。

| RED / GREEN 命令                                                              | 证据                            | 绑定 Execute Skill                | 已执行 |
| ----------------------------------------------------------------------------- | ------------------------------- | --------------------------------- | ------ |
| `uv run pytest tests/test_ops_db_inspector.py tests/test_write_manager.py -q` | `9.0-red.txt` / `9.0-green.txt` | trellis-execute · gitnexus-impact | [x]    |

### 9.1 OPS-01 — Contract loader

| 字段               | 内容                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------ |
| 切片               | OPS-01（§8 序 1）                                                                    |
| RED / GREEN        | `uv run pytest tests/test_ops_db_inspector.py -q` → `9.1-red.txt` / `9.1-green.txt`  |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines · testing-guidelines · gitnexus-impact |
| 通过               | loader 读 YAML；无重复硬编码列表                                                     |
| 已执行             | [x]                                                                                  |

### 9.2 OPS-02 — Ops drift tests

| 字段               | 内容                                                                                                                                                                                     |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 切片               | OPS-02                                                                                                                                                                                   |
| RED / GREEN        | `uv run pytest tests/test_contract_drift_ops_write.py::test_opsInspect_keyTables_matchContract tests/test_contract_drift_ops_write.py::test_opsInspect_deferredMapping_matchContract -v` |
| 绑定 Execute Skill | test-driven-development · incremental-implementation                                                                                                                                     |
| 通过               | RED FAIL（测先写）；GREEN 全绿                                                                                                                                                           |
| 已执行             | [x]                                                                                                                                                                                      |

### 9.3 WRITE-01 — Write contract split

| 字段               | 内容                                                                                                             |
| ------------------ | ---------------------------------------------------------------------------------------------------------------- |
| 切片               | WRITE-01                                                                                                         |
| RED / GREEN        | `uv run pytest tests/test_contract_drift_ops_write.py::test_writeContract_implementedModes_matchWriteManager -v` |
| 绑定 Execute Skill | test-driven-development · karpathy-guidelines                                                                    |
| 通过               | YAML 含 implemented_modes / reserved_modes                                                                       |
| 已执行             | [x]                                                                                                              |

### 9.4 WRITE-02 — Implemented + reserved parity

| 字段               | 内容                                                                                                                                                                                                            |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 切片               | WRITE-02                                                                                                                                                                                                        |
| RED / GREEN        | `uv run pytest tests/test_contract_drift_ops_write.py::test_writeContract_implementedModes_matchWriteManager tests/test_contract_drift_ops_write.py::test_writeContract_reservedModes_matchUnsupportedModes -v` |
| 绑定 Execute Skill | test-driven-development · incremental-implementation                                                                                                                                                            |
| 通过               | `implemented_modes == SUPPORTED_MODES` 且 `reserved_modes == UNSUPPORTED_MODES`                                                                                                                                 |
| 已执行             | [x]                                                                                                                                                                                                             |

### 9.5 WRITE-03 — Reserved reject

| 字段               | 内容                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------- |
| 切片               | WRITE-03                                                                                                      |
| RED / GREEN        | `uv run pytest tests/test_contract_drift_ops_write.py::test_writeManager_reservedModes_rejectWithoutWrite -v` |
| 绑定 Execute Skill | test-driven-development · gitnexus-impact                                                                     |
| 通过               | 三 reserved 模式稳定拒绝                                                                                      |
| 已执行             | [x]                                                                                                           |

---

## 10. Execute 交接 DoD

- [x] §9 证据齐 · §5.4+§6 绿 · `validate-execute-handoff` 0 · 未 finish-work · **未**改 registry

---

## 11. Execute Skill 冻结

| Skill                      | 本任务   | 绑定       | 已读 | 已执行 |
| -------------------------- | -------- | ---------- | ---- | ------ |
| trellis-execute            | 必做     | Boot       | [ ]  | [ ]    |
| test-driven-development    | 必做     | §9 RED     | [ ]  | [ ]    |
| incremental-implementation | 必做     | §9 SLICE   | [ ]  | [ ]    |
| karpathy-guidelines        | 必做     | GREEN      | [ ]  | [ ]    |
| testing-guidelines         | 必做     | 写测       | [ ]  | [ ]    |
| gitnexus-impact            | 必做     | 改 symbol  | [ ]  | [ ]    |
| systematic-debugging       | 条件     | DEBUG      | [ ]  | [ ]    |
| trellis-implement          | 必做     | Execute    | [ ]  | [ ]    |
| trellis-check              | **不用** | → Audit A1 | —    | —      |

路径见 `execute-skill-paths.yaml`。Audit → `AUDIT.plan.md`。
