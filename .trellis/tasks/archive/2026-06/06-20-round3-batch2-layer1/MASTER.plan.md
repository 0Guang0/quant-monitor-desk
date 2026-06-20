# MASTER 计划 — Round 3 Batch 2 Layer 1

> **Execute 入口**  
> Execute：本文件 + `implement.jsonl`。Audit 见 `AUDIT.plan.md`（Execute 不读）。  
> **Gate：** 本任务 PASS 后才能启动 Round 3 Batch 3（`019` Layer 2）。

---

## 0. 元信息

| 字段                      | 值                                                                |
| ------------------------- | ----------------------------------------------------------------- |
| 任务 slug                 | `06-20-round3-batch2-layer1`                                      |
| 原计划来源                | `017` + `018` + `ROUND3_EARLY_CLOSE_PLAN.md`（lineage consumers） |
| 批次索引                  | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3 Batch 2                   |
| 前置 gate                 | Batch 1 `06-20-round3-batch1-early-ops` archived PASS             |
| Audit 计划                | `.trellis/tasks/06-20-round3-batch2-layer1/AUDIT.plan.md`         |
| 分析豁免                  | `analysis_waiver: false`                                          |
| manifest_protocol_version | `3`                                                               |

### 0.1 原计划任务

| 字段     | 值                                                                                       |
| -------- | ---------------------------------------------------------------------------------------- |
| Round    | Round 3 Batch 2                                                                          |
| 原始任务 | `017_implement_layer1_axis_loader.md`、`018_implement_layer1_interpretation_snapshot.md` |
| 别名项   | `R3-EARLY-LINEAGE-CONSUMERS` ← `ROUND3_EARLY_CLOSE_PLAN.md`                              |
| Item IDs | `017`, `018`, `R3-EARLY-LINEAGE-CONSUMERS`                                               |
| 排除     | `019`–`023`、Layer1 FastAPI、全量 live fetch、Migration 008 CHECK                        |

### 0.2 门控速查

- 实现目录：`backend/app/layer1_axes/`、`backend/app/db/migrations/`、`tests/` — **不得**在 `docs/`/`specs/` 写运行时代码。
- 所有 clean 快照写入经 `DuckDBWriteManager` + `validation_report_id`（**不得**直写 DuckDB writer）。
- 五轴 spec 权威：`specs/layer1_axes/restructured_axes_v1_1/**` + `configs/layer1_axes.yml`。
- FORBIDDEN 指标：仅 registry 登记，**不**进入 `axis_observation`。
- `as_of_timestamp`：输入观测 `publish_timestamp` / 可见时间必须 ≤ `as_of`（`no_future_data`）。
- 禁止 `layer1_axis_contract.yaml` `forbidden_output_terms`（买入/卖出/信号等）。
- 依赖与验收：`specs/contracts/runtime_versions.md`（D-01：`uv sync --locked`）。
- **D-09**：完整标准化字段仅 Layer 1（ADR-0003）。

### 0.7 GLOBAL 与已拍板决策摘要（inline）

**GLOBAL_EXECUTION_RULES：** 无 drive-by；Primary/Validation/FallbackPolicy；禁止 Shadow/Emergency 源角色；禁止 Agent 自由 SQL/联网/直写 clean；禁止交易动作语义。

**GLOBAL_TESTING_POLICY：** RED→GREEN；语义断言（state_bucket、quality_flags、lineage 字段）；禁止仅 `assert called`。

**GLOBAL_RESOURCE_LIMITS：** eco 默认；rolling window 按 `layer1_global_regime_panel.md` §7.3；禁止无界全历史扫描。

**D-09（PENDING_USER_DECISIONS）：** Layer 2–5 不默认复制 Layer 1 全套标准化字段。

**前置 gate（AC-PRE）：** Batch 1 audit PASS + Round 2.6 gates archived PASS。

### 0.8 项目边界（README 摘要）

- 三层追溯：设计/契约 → 原始任务卡 → Trellis 冻结计划 → 实现代码。
- `docs/`、`specs/` 非实现地址；MANIFEST 权威口径不得被 Trellis 覆盖。
- Execute 只读 MASTER + `implement.jsonl`。

### 0.3 Execute 强制必读清单

**规则：** Phase 0 Boot **必须 Read `implement.jsonl` 每一条**；记录于 `execute-evidence/8.0-boot-reads.txt`。

**v3：** 先读 `research/integration-ledger.md`（§0.4）。

**6.pre：** GitNexus → `research/gitnexus-execute-summary.md`。

### 0.4 上下文打包（协议 v3）

Execute 以 MASTER inline 为准；ledger 规定 pointer 原稿的 extract/for。

### 0.5 Execute 开场白（可复制）

```text
进入 Execute。MUST Read .cursor/skills/trellis-execute/SKILL.md。
Phase 0 Boot（§0.3 implement.jsonl 全读 + integration-ledger）→ §8.x → §9/§10 → §11 Audit。勿 finish-work。
```

### 0.6 Source Context Index

| 路径                                                   | 类型          | 已总结？  | Execute must-read? | 原因                                                              |
| ------------------------------------------------------ | ------------- | --------- | ------------------ | ----------------------------------------------------------------- |
| `README.md`                                            | rule          | 是 §0.8   | **是**             | 实现边界                                                          |
| `MIGRATION_MAP.md` §6 Layer1                           | map           | 是        | 否                 | Plan 已纠偏路径                                                   |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3–4.2            | index         | 是        | 否                 | Plan 已归并                                                       |
| `017`/`018` 任务卡                                     | original-task | 是 §2     | 否                 | Plan only                                                         |
| `docs/modules/layer1_global_regime_panel.md`           | design        | 部分      | **是**             | §6 DDL、§7 窗口、§8 流程、§13 测试                                |
| `specs/contracts/layer1_axis_contract.yaml`            | contract      | 否        | **是**             | 字段/forbidden terms                                              |
| `specs/layer1_axes/restructured_axes_v1_1/**`          | domain        | 否        | **是**             | 五轴 YAML + engineering + user_guide 全文（implement 逐文件列出） |
| `specs/layer1_axes/.../*_engineering_rules.md`（×5）   | domain        | 否        | **是**             | AC-017-5 轴级禁止项                                               |
| `specs/layer1_axes/.../*_user_guide.md`（×5）          | domain        | 否        | **是**             | profile 静态解释来源                                              |
| `docs/architecture/03_runtime_flows.md`                | architecture  | 部分      | pointer            | 017 §5 Layer1 运行链路                                            |
| `docs/architecture/04_data_architecture.md`            | architecture  | 部分      | pointer            | 017 §5 数据分层                                                   |
| `docs/quality/final_package_rules.md`                  | rule          | 是        | 否                 | 无临时 round report inline                                        |
| `docs/quality/staged_acceptance_policy.md`             | rule          | 是 §10 注 | **是**             | backend 分层 vs Tier B 加固说明                                   |
| `backend/app/core/resource_guard.py`                   | code          | 否        | **是**             | AC-RES-1                                                          |
| `specs/contracts/resource_limits.yaml`                 | contract      | 否        | **是**             | eco profile 权威                                                  |
| `backend/app/db/validation_gate.py`                    | code          | 否        | **是**             | AC-WRIT-1 DbValidationGate                                        |
| `specs/contracts/snapshot_lineage_contract.yaml`       | contract      | 否        | **是**             | lineage 必填 + 测试名                                             |
| `configs/layer1_axes.yml`                              | config        | 否        | **是**             | spec_root                                                         |
| `docs/adr/ADR-0003-layer1-standardization-only.md`     | ADR           | 是 §0.7   | 否                 | D-09 inline                                                       |
| `docs/modules/duckdb_and_parquet.md`                   | design        | 是        | 否                 | Layer1 表归属摘要                                                 |
| `docs/modules/write_manager.md`                        | rule          | 部分      | **是**             | 快照写入路径                                                      |
| `backend/app/db/write_manager.py`                      | code          | 否        | **是**             | WriteRequest API                                                  |
| `backend/app/validators/data_quality.py`               | code          | 部分      | **是**             | rule_version / fetch lineage                                      |
| `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md` | plan          | 是        | 否                 | lineage 范围 inline                                               |
| `GLOBAL_*.md`                                          | rule          | 是 §0.7   | **是**             | 对照原稿                                                          |
| `specs/contracts/runtime_versions.md`                  | rule          | 是        | **是**             | §10 命令                                                          |
| `docs/quality/PENDING_USER_DECISIONS.md`               | decision      | 是        | **是**             | D-09                                                              |
| `docs/quality/staged_acceptance_policy.md`             | rule          | 是        | 否                 | backend 分层 inline                                               |
| Batch 1 `audit.report.md`                              | gate          | 是        | 否                 | AC-PRE pointer                                                    |
| `specs/schema/schema.sql`                              | schema        | 过滤      | 否                 | axis 表不在此文件；用 migration 011                               |
| Layer1 API / FastAPI                                   | design        | 过滤      | 否                 | Round 4 defer                                                     |

---

## 1. 目标

### 1.1 一句话目标

交付 Layer 1 五轴 spec 加载、registry/profile 初始化、特征与解释快照引擎，并闭合快照 lineage 消费者，使 Layer 1 输出可审计、as_of 安全、可支撑 Batch 3。

### 1.2 非目标

- Layer 2–5（`019`–`023`）。
- FastAPI `/api/layer1/*`（`024`+）。
- 全量 `Layer1AxisFetcher` 生产调度与 live 外部源抓取（可用 fixture observation）。
- Migration 008 DB CHECK（Batch 6）。
- 前端五轴卡片（Round 4 + D-08 用户确认 UI）。

### 1.3 子交付物表（Item ID → AC）

| Item ID                      | MASTER AC                        | 类型        |
| ---------------------------- | -------------------------------- | ----------- |
| `017`                        | AC-017-1..8                      | 实现        |
| `018`                        | AC-018-1..6, AC-WRIT-1, AC-RES-1 | 实现        |
| `R3-EARLY-LINEAGE-CONSUMERS` | AC-LINEAGE-1..4                  | 实现 + 测试 |

---

## 2. 预期结果（A5 trace-ac 追溯用）

| ID           | 预期结果                                                                                                                                                                                                                                                                                                       | 验证链                                                    |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| AC-PRE       | Batch 1 + R2.6 contract/routing gates archived PASS；`uv sync --locked` + 基线 pytest green                                                                                                                                                                                                                    | §8.0; archived audits（Batch1 + `06-19-round2-6-*-gate`） |
| AC-017-1     | `AxisSpecLoader` 从 `configs/layer1_axes.yml` 加载五轴 YAML；五轴 `axis_id` 齐全                                                                                                                                                                                                                               | §8.2; `test_layer1_axis_loader.py`                        |
| AC-017-2     | registry 行含 `layer1_axis_contract.yaml` 必填字段 + module §5.3 超集（`formula`、`quality_rules`、`stale_rules`、`forbidden_substitutes`）                                                                                                                                                                    | §8.2; contract field tests                                |
| AC-017-3     | `is_forbidden=true` / BlindSpot 指标进入 registry 但**不可观测**；无 observation 路径                                                                                                                                                                                                                          | §8.2; forbidden/blindspot tests                           |
| AC-017-4     | migration 011 创建 registry/observation/snapshot/**`axis_snapshot_lineage`** 表且可初始化                                                                                                                                                                                                                      | §8.1; schema tests                                        |
| AC-017-5     | 轴级 `*_engineering_rules.md` 禁止项生效（如混频投影元数据、禁止 substitute）                                                                                                                                                                                                                                  | §8.2; engineering rules tests                             |
| AC-017-6     | `common_axis_rules.md` §4.1 三名 SHADOW 诊断测试通过                                                                                                                                                                                                                                                           | §8.2; shadow diagnostic tests                             |
| AC-017-7     | loader 第四输出 `AxisEngineeringGuardrail` 可校验 forbidden_substitute / 跨轴污染                                                                                                                                                                                                                              | §8.2; `guardrails.py` tests                               |
| AC-017-8     | spec 缺 `indicator_id` 时 loader 拒绝初始化                                                                                                                                                                                                                                                                    | §8.2; `test_axisSpecLoader_missingIndicatorId_rejects`    |
| AC-018-1     | `axis_feature_snapshot` 含 module §7.1 字段：`raw_value`、`z_score`、`robust_z_score`、`percentile_rank`、`percentile_left_tail`、`percentile_right_tail`、`level_state`、`delta_state`、`state_bucket`、`extreme_flags`、`valid_obs_count`、`coverage_ratio`、`quality_flags`；MAD=0 → `ROBUST_Z_UNAVAILABLE` | §8.3; feature tests                                       |
| AC-018-2     | 历史不足 → `INSUFFICIENT_HISTORY` + `state_bucket=insufficient_history`；不伪造 z/percentile                                                                                                                                                                                                                   | §8.3; window tests                                        |
| AC-018-3     | `axis_interpretation_snapshot` 无 `forbidden_output_terms`；命中则 `needs_human_review=true` 或拒绝写入                                                                                                                                                                                                        | §8.4; interpretation tests                                |
| AC-018-4     | 快照拒绝 `as_of` 之后可见的 observation（`no_future_data`）                                                                                                                                                                                                                                                    | §8.3/8.4; future-input tests                              |
| AC-018-5     | fallback 生效时记录 `SOURCE_SWITCHED` quality flag（fixture 驱动）                                                                                                                                                                                                                                             | §8.3; fallback tests                                      |
| AC-018-6     | Layer 2 值试图回写 Layer 1 registry/snapshot 时被阻断（守卫测试）                                                                                                                                                                                                                                              | §8.4; writeback guard test                                |
| AC-WRIT-1    | feature/interpretation 快照经 staging → `DuckDBWriteManager` + `DbValidationGate`（`validation_report_id`）写入 clean 表                                                                                                                                                                                       | §8.5; WriteManager integration test                       |
| AC-RES-1     | `AxisFeatureEngine.compute_features` 在 rolling 计算前调用 `ResourceGuard`（eco profile）；超限时拒绝或降级                                                                                                                                                                                                    | §8.3; resource guard test                                 |
| AC-LINEAGE-1 | `axis_snapshot_lineage` 行含契约全部 `required_fields`（见 §3.4 完整列表）                                                                                                                                                                                                                                     | §8.5; lineage persistence tests                           |
| AC-LINEAGE-2 | lineage 消费 `validation_report.rule_version`、`source_fetch_ids_json`、`source_content_hashes_json`                                                                                                                                                                                                           | §8.5; consumer tests                                      |
| AC-LINEAGE-3 | 契约 `validation_tests` 三名在 pytest 中实现且通过                                                                                                                                                                                                                                                             | §8.5; named tests                                         |
| AC-LINEAGE-4 | 同输入 + 同 `rule_version` + 同 `parameter_hash` → 确定性重建（`deterministic_rebuild`）；Agent 文本不进 `source_dataset_ids`                                                                                                                                                                                  | §8.5; rebuild tests                                       |
| AC-GATE      | 全量 backend 门禁 green                                                                                                                                                                                                                                                                                        | §9–§10                                                    |

---

## 3. 范围与边界

### 3.1 允许修改/创建

- `backend/app/layer1_axes/*.py`（含 `guardrails.py`）
- `backend/app/db/migrations/011_layer1_tables.sql`（含 `axis_snapshot_lineage`）
- `tests/test_layer1_axis_loader.py`
- `tests/test_layer1_interpretation.py`
- `research/execute-evidence/**`（Execute 产出）

### 3.2 Out of scope · 显式 defer

| 项                                   | 偿还批次               | 说明                      |
| ------------------------------------ | ---------------------- | ------------------------- |
| Layer 2 `019`                        | Batch 3                | —                         |
| Layer 3–5 `020`–`023`                | Batch 4–5              | —                         |
| FastAPI Layer1 路由                  | Round 4 `024`          | 设计见 module doc §11     |
| `Layer1AxisFetcher` 生产抓取         | sync/orchestrator 后续 | 本批 fixture observation  |
| Migration 008 CHECK                  | Batch 6                | —                         |
| `quant_monitor layer1` CLI packaging | Round 5 / D2-P1-3      | 本批仅 Python API + tests |

### 3.3 禁止修改

- `frontend/**`
- `backend/app/layer2_sensors/**` 及其他 layer 包
- `backend/app/api/**`
- Batch 1 `backend/app/ops/db_inspector.py`（除非修共享 util 且 impact LOW）
- 绕过 WriteManager 直写 clean 表

### 3.4 WriteManager / lineage 边界

- 快照写入：**DataQualityValidator（如需）→ `validation_report` → `DbValidationGate` → staging → `DuckDBWriteManager` → clean tables**（见 `write_manager.md` §2）。
- **Lineage 持久化：** migration 011 新增 `axis_snapshot_lineage` 表（`snapshot_id` PK），与 `axis_feature_snapshot` / `axis_interpretation_snapshot` 通过 `snapshot_id` + `snapshot_type` 关联；每行存储契约全部字段。
- **Lineage 必填字段（`snapshot_lineage_contract.yaml`）：** `snapshot_id`, `snapshot_type`, `layer_id`, `as_of_timestamp`, `generated_at`, `input_data_window_start`, `input_data_window_end`, `source_dataset_ids`, `source_fetch_ids`, `source_content_hashes`, `rule_version`, `code_version`, `parameter_hash`, `resource_profile`, `upstream_snapshot_ids`, `is_incremental`, `rebuild_reason`。
- **约束：** `no_future_data`；`deterministic_rebuild`；`agent_outputs_not_source`（Agent 文本不得进入 `source_dataset_ids`）。

---

## 4. 代码地图

| 路径                                              | 操作                                                                                                            |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `backend/app/db/migrations/011_layer1_tables.sql` | **创建** — registry + observation + snapshot + **`axis_snapshot_lineage`**（对齐 module doc §6 + lineage 契约） |
| `backend/app/layer1_axes/axis_loader.py`          | **创建** — `AxisSpecLoader`（四输出含 guardrail 输入）                                                          |
| `backend/app/layer1_axes/guardrails.py`           | **创建** — `AxisEngineeringGuardrail`                                                                           |
| `backend/app/layer1_axes/models.py`               | **创建** — dataclasses                                                                                          |
| `backend/app/layer1_axes/feature_engine.py`       | **创建** — `AxisFeatureEngine`（含 ResourceGuard 钩子）                                                         |
| `backend/app/layer1_axes/interpretation.py`       | **创建** — `AxisInterpretationEngine`                                                                           |
| `backend/app/layer1_axes/lineage.py`              | **创建** — `SnapshotLineageBuilder` + DB 持久化                                                                 |
| `backend/app/layer1_axes/writer.py`               | **创建** — Layer1 snapshot WriteManager 薄封装（可选，或与 lineage 合并）                                       |
| `tests/test_layer1_axis_loader.py`                | **创建**                                                                                                        |
| `tests/test_layer1_interpretation.py`             | **创建** — 含 lineage + no-future                                                                               |

**路径纠偏：** 任务卡 `backend/layers/layer1/` → 本表路径为准。

---

## 5. 实现切片（§8 顺序）

1. **8.1** Migration 011 — Layer1 表 DDL
2. **8.2** AxisSpecLoader + registry init（017）
3. **8.3** AxisFeatureEngine + feature snapshot（018-a）
4. **8.4** AxisInterpretationEngine + interpretation snapshot（018-b）
5. **8.5** Lineage 持久化 + WriteManager 集成（R3-EARLY-LINEAGE-CONSUMERS + AC-WRIT-1）
6. **8.6** 全量 Tier A/B 门禁

测试设计详见：`research/layer1-axis-loader-tests.md`、`research/layer1-feature-interpretation-tests.md`、`research/layer1-lineage-tests.md`。

---

## 6. 接口/契约

### Python API（示意）

```python
# axis_loader.py
class AxisSpecLoader:
    def load(self, *, spec_root: Path, enabled_axes: list[str]) -> AxisLoadResult: ...

# feature_engine.py
class AxisFeatureEngine:
    def compute_features(self, *, as_of: datetime, observations: Sequence[AxisObservation]) -> list[FeatureSnapshotRow]: ...

# interpretation.py
class AxisInterpretationEngine:
    def build_interpretation(self, *, as_of: datetime, features: Sequence[FeatureSnapshotRow]) -> list[InterpretationSnapshotRow]: ...

# lineage.py
class SnapshotLineageBuilder:
    def build(self, *, validation_report: ValidationReportRef, ...) -> LineageEnvelope: ...
```

### 契约锚点

- Indicator 字段：`layer1_axis_contract.yaml` `required_indicator_fields`
- Quality flags / state_bucket：同契约 `quality_flags` / `state_bucket`
- Lineage：`snapshot_lineage_contract.yaml` `required_fields` + `validation_tests`
- 配置：`configs/layer1_axes.yml` `spec_root` + `enabled_axes`

---

## 7. Red Flags

| Red Flag                       | 预防                                |
| ------------------------------ | ----------------------------------- |
| FORBIDDEN 指标进入 observation | AC-017-3 测试                       |
| 历史不足伪造 z-score           | AC-018-2                            |
| interpretation 含买卖信号词    | AC-018-3 + contract forbidden terms |
| 读入 as_of 之后数据            | AC-018-4 / AC-LINEAGE-3             |
| 绕过 WriteManager              | code review + A3                    |
| 在 docs/specs 写 .py           | GLOBAL + README                     |
| 实现 Layer2 或 API             | §3.2 defer                          |
| 全市场全历史 rolling           | ResourceGuard + §7.3 窗口策略       |

---

## 8. 实现步骤（RED/GREEN）

### 8.0 Boot gate

| 字段       | 内容                                                                                                                                                                       |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 按 **§0.3** 读 `implement.jsonl` 全表 + `research/integration-ledger.md`；6.pre GitNexus；基线 pytest                                                                      |
| RED 命令   | `uv run python -c "import sys; from pathlib import Path; p=Path('.trellis/tasks/06-20-round3-batch2-layer1/research/execute-boot.md'); sys.exit(0 if p.is_file() else 1)"` |
| GREEN 命令 | 创建 `research/execute-boot.md` + `uv sync --locked` + `uv run pytest -q --co -q`                                                                                          |
| RED 证据   | `execute-evidence/8.0-red.txt`                                                                                                                                             |
| GREEN 证据 | `execute-evidence/8.0-boot-reads.txt`, `execute-evidence/8.0-baseline.txt`                                                                                                 |
| Skill      | trellis-execute Phase 0                                                                                                                                                    |

### 8.1 Layer1 schema migration

| 字段       | 内容                                                                                                                                                                                                                                        |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 新增 `011_layer1_tables.sql`：`axis_registry`, `axis_indicator_registry`, `axis_indicator_profile`, `axis_observation`, `axis_feature_snapshot`, `axis_interpretation_snapshot`, **`axis_snapshot_lineage`**（列对齐 §3.4 + module doc §6） |
| RED 命令   | `uv run pytest tests/test_layer1_axis_loader.py::test_layer1Migration_createsRegistryTables tests/test_layer1_axis_loader.py::test_layer1Migration_createsSnapshotLineageTable -q`                                                          |
| GREEN 命令 | `uv run python scripts/init_db.py` + 上项 pytest                                                                                                                                                                                            |
| RED 证据   | `execute-evidence/8.1-red.txt`                                                                                                                                                                                                              |
| GREEN 证据 | `execute-evidence/8.1-green.txt`                                                                                                                                                                                                            |
| 通过条件   | AC-017-4                                                                                                                                                                                                                                    |
| Skill      | test-driven-development, incremental-implementation, GitNexus impact                                                                                                                                                                        |
| 测试设计   | `research/layer1-axis-loader-tests.md` §migration                                                                                                                                                                                           |

### 8.2 AxisSpecLoader (017)

| 字段       | 内容                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 实现 loader + `guardrails.py`：解析五轴三件套；填充 registry/profile；校验 contract + module §5.3；FORBIDDEN/BlindSpot 仅登记；SHADOW 三名测试；缺 indicator_id 拒绝                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| RED 命令   | `uv run pytest tests/test_layer1_axis_loader.py::test_axisSpecLoader_loadsFiveAxes tests/test_layer1_axis_loader.py::test_axisSpecLoader_forbiddenIndicator_notObservable tests/test_layer1_axis_loader.py::test_axisSpecLoader_blindspot_notObservable tests/test_layer1_axis_loader.py::test_axisSpecLoader_missingIndicatorId_rejects tests/test_layer1_axis_loader.py::test_axisSpecLoader_missingQualityRules_rejects tests/test_layer1_axis_loader.py::test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover tests/test_layer1_axis_loader.py::test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles tests/test_layer1_axis_loader.py::test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly tests/test_layer1_axis_loader.py::test_axisEngineeringGuardrail_rejectsForbiddenSubstitute -q` |
| GREEN 命令 | `uv run pytest tests/test_layer1_axis_loader.py -q`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| RED 证据   | `execute-evidence/8.2-red.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| GREEN 证据 | `execute-evidence/8.2-green.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 通过条件   | AC-017-1..8                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Skill      | test-driven-development, karpathy-guidelines, testing-guidelines, spec-driven-development                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 测试设计   | `research/layer1-axis-loader-tests.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

### 8.3 Feature engine (018-a)

| 字段       | 内容                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | `AxisFeatureEngine`：§7.1 全字段；rolling z/robust_z/percentile；INSUFFICIENT_HISTORY；SOURCE_SWITCHED；`ResourceGuard.check()`；no_future_data                                                                                                                                                                                                                                                                                                               |
| RED 命令   | `uv run pytest tests/test_layer1_interpretation.py::test_axisFeatureEngine_insufficientHistory_noFakeZ tests/test_layer1_interpretation.py::test_axisFeatureEngine_robustZUnavailable_whenMadZero tests/test_layer1_interpretation.py::test_axisFeatureEngine_sourceSwitched_recordsQualityFlag tests/test_layer1_interpretation.py::test_axisFeatureEngine_resourceGuard_ecoProfile tests/test_layer1_interpretation.py::test_snapshotRejectsFutureInput -q` |
| GREEN 命令 | `uv run pytest tests/test_layer1_interpretation.py -k "feature or future" -q`                                                                                                                                                                                                                                                                                                                                                                                 |
| RED 证据   | `execute-evidence/8.3-red.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                |
| GREEN 证据 | `execute-evidence/8.3-green.txt`                                                                                                                                                                                                                                                                                                                                                                                                                              |
| 通过条件   | AC-018-1,2,4,5; AC-RES-1                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Skill      | test-driven-development, incremental-implementation, testing-guidelines                                                                                                                                                                                                                                                                                                                                                                                       |
| 测试设计   | `research/layer1-feature-interpretation-tests.md` §feature                                                                                                                                                                                                                                                                                                                                                                                                    |

### 8.4 Interpretation engine (018-b)

| 字段       | 内容                                                                                                                                                                                     |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | `AxisInterpretationEngine`：level/change labels；forbidden terms；`needs_human_review`；Layer2 回写阻断守卫                                                                              |
| RED 命令   | `uv run pytest tests/test_layer1_interpretation.py::test_axisInterpretation_rejectsForbiddenActionTerms tests/test_layer1_interpretation.py::test_layer2ValueCannotWritebackToLayer1 -q` |
| GREEN 命令 | `uv run pytest tests/test_layer1_interpretation.py -k interpretation -q`                                                                                                                 |
| RED 证据   | `execute-evidence/8.4-red.txt`                                                                                                                                                           |
| GREEN 证据 | `execute-evidence/8.4-green.txt`                                                                                                                                                         |
| 通过条件   | AC-018-3,6                                                                                                                                                                               |
| Skill      | test-driven-development, testing-guidelines                                                                                                                                              |
| 测试设计   | `research/layer1-feature-interpretation-tests.md` §interpretation                                                                                                                        |

### 8.5 Lineage persistence + WriteManager

| 字段       | 内容                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | `SnapshotLineageBuilder` 写入 `axis_snapshot_lineage`；消费 `validation_report`；三名契约测试 + deterministic_rebuild；快照经 WriteManager+ValidationGate 落库                                                                                                                                                                                                                                                                                |
| RED 命令   | `uv run pytest tests/test_layer1_interpretation.py::test_snapshotLineageContainsSourceHashes tests/test_layer1_interpretation.py::test_incrementalRebuildPreservesAsOfBoundary tests/test_layer1_interpretation.py::test_snapshotLineageIncludesAllRequiredFields tests/test_layer1_interpretation.py::test_snapshotDeterministicRebuild_sameInputsSameHash tests/test_layer1_interpretation.py::test_layer1Snapshot_writeViaWriteManager -q` |
| GREEN 命令 | `uv run pytest tests/test_layer1_interpretation.py -k lineage -q`                                                                                                                                                                                                                                                                                                                                                                             |
| RED 证据   | `execute-evidence/8.5-red.txt`                                                                                                                                                                                                                                                                                                                                                                                                                |
| GREEN 证据 | `execute-evidence/8.5-green.txt`                                                                                                                                                                                                                                                                                                                                                                                                              |
| 通过条件   | AC-LINEAGE-1..4; AC-WRIT-1                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Skill      | test-driven-development, spec-driven-development, incremental-implementation                                                                                                                                                                                                                                                                                                                                                                  |
| 测试设计   | `research/layer1-lineage-tests.md`                                                                                                                                                                                                                                                                                                                                                                                                            |

### 8.6 Final gates

| 字段       | 内容                                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------------------ |
| 做什么     | 全量 §9 §10                                                                                            |
| RED 命令   | `uv run pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q`（实现前 fail） |
| GREEN 命令 | 见 §10 Tier A/B                                                                                        |
| RED 证据   | `execute-evidence/8.6-red.txt`                                                                         |
| GREEN 证据 | `execute-evidence/8.6-final-gates.txt`                                                                 |
| 通过条件   | AC-GATE                                                                                                |
| Skill      | trellis-execute, incremental-implementation                                                            |

---

## 9. 四层测试

| 层     | 范围                                                   | 命令                                                                                    |
| ------ | ------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| A 单元 | layer1 loader/feature/interpretation/lineage           | `uv run pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q` |
| B 集成 | migration + init_db + WriteManager/ValidationGate 路径 | `uv run python scripts/init_db.py` + `test_layer1Snapshot_writeViaWriteManager`         |
| C 管道 | 全量 pytest + production_gate                          | `uv run pytest -q`                                                                      |
| D E2E  | N/A — 无 CLI/API 本批                                  | —                                                                                       |

---

## 10. Tier 验收

### Tier A（每步 GREEN 后）

```bash
uv sync --locked
uv run pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q
uv run ruff check backend/app/layer1_axes tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py
```

### Tier B（§8.6 收尾）

> **注：** Tier B 含 `cov 85%` / `production_gate` 为 Round 3 批次加固门禁，超出单任务卡 §11 最小集；与 `staged_acceptance_policy.md` backend 行并存，以 MASTER §10 为准。

```bash
uv sync --locked
uv run pytest -q
uv run pytest -q --cov=backend --cov-fail-under=85
uv run ruff check .
uv run ruff format --check .
uv run python scripts/production_gate.py
uv run python scripts/check_doc_links.py
uv run python -m compileall -q backend scripts tests
```

### Tier C

N/A — 无 frontend 变更。

---

## 11. Audit 交接

- Execute 完成 §8–§10 后运行 `validate-execute-handoff`。
- 交接 `AUDIT.plan.md` + `audit.jsonl`；**不** `finish-work`。
- Audit 须验证：FORBIDDEN 隔离、INSUFFICIENT_HISTORY、lineage 字段、no_future_data、WriteManager 边界。

---

## 12. Execute Skill 冻结清单

| Skill                          | 本任务 | 绑定 §8 | 触发            | @ 指令                                  | 已执行 |
| ------------------------------ | ------ | ------- | --------------- | --------------------------------------- | ------ |
| trellis-execute                | 必做   | 8.0     | 每步            | Read trellis-execute SKILL Phase 0 Boot | [x]    |
| test-driven-development        | 必做   | 8.1–8.5 | 每实现步        | RED 先于 GREEN                          | [x]    |
| incremental-implementation     | 必做   | 8.1–8.5 | 每 GREEN 后     | 全量 pytest 再下一步                    | [x]    |
| karpathy-guidelines            | 必做   | 8.2–8.5 | RED 后 GREEN 前 | 最小正确实现                            | [x]    |
| testing-guidelines             | 必做   | 8.2–8.5 | 每测试步        | 语义断言                                | [x]    |
| spec-driven-development        | 必做   | 8.2,8.5 | 契约步          | 对照 YAML 契约                          | [x]    |
| gitnexus-impact-analysis       | 必做   | 8.1–8.5 | 改符号前        | impact() 上游                           | [x]    |
| api-and-interface-design       | 不用   | —       | —               | 无 HTTP 本批                            | [ ]    |
| ponytail-review                | 不用   | —       | —               | Audit A2 only                           | [ ]    |
| verification-before-completion | 不用   | —       | —               | Audit A5 only；Execute 禁止             | [ ]    |

---

## 13. 原计划归并表

| 原始来源                             | MASTER 归并位置        | manifest                                                           |
| ------------------------------------ | ---------------------- | ------------------------------------------------------------------ |
| `017` 任务卡                         | §2 AC-017-\*; §8.2     | Plan only                                                          |
| `018` 任务卡                         | §2 AC-018-\*; §8.3–8.4 | Plan only；**018 §3 未列 axis contract — 执行须借用 017 契约输入** |
| `ROUND3_EARLY_CLOSE_PLAN` lineage 行 | §2 AC-LINEAGE-\*; §8.5 | 摘要 inline                                                        |
| `layer1_global_regime_panel.md`      | §4/§6/§7 Red Flags     | must-read                                                          |
| `layer1_axis_contract.yaml`          | §6; AC-017-2           | must-read                                                          |
| `snapshot_lineage_contract.yaml`     | §6; AC-LINEAGE-\*      | must-read                                                          |
| `restructured_axes_v1_1/**`          | §6; AC-017-1           | must-read                                                          |
| `MIGRATION_MAP.md` Layer1 行         | §4 路径纠偏            | 已总结                                                             |
| `README.md` 三层模型                 | §0.8                   | must-read                                                          |
