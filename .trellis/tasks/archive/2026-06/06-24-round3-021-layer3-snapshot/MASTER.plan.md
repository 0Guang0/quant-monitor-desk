# MASTER 计划 — Round 3 Batch 4 `021` Layer 3 Industry Chain Snapshot Builder

> **Execute 入口** — staged-only；**不得**声称 production-live readiness。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`

---

## 0. 元信息

| 字段                      | 值                                                             |
| ------------------------- | -------------------------------------------------------------- |
| 任务 slug                 | `06-24-round3-021-layer3-snapshot`                             |
| 分支                      | `feature/round3-021-layer3-snapshot`                           |
| 前置                      | `020` merged；`R3-B3-STAGED-DOWNSTREAM-GATE` CLOSED            |
| manifest_protocol_version | `3`                                                            |
| analysis_waiver           | `false`                                                        |
| 原计划                    | `research/source-index.md` · `research/original-plan-trace.md` |

### Staged downstream limitations（§16 强制）

1. `BATCH3_STAGED_DOWNSTREAM_GATE.md` — staged-only
2. `R3-B2.75-REQ2-EM` — **DEFERRED**；不得作 live 前提
3. `production_live_pilot_policy.md` — 不解锁生产访问
4. fixture-backed Layer5 bars；无 live vendor / production DB writes
5. D-09 — Layer 2–5 不复制 Layer1 全套标准化字段；lineage 仅 contract 必需子集
6. 禁止修改 `snapshot_lineage_contract.yaml`（023A 写权限）

### Failure modes / 回滚

| 场景             | 处理                                                                     |
| ---------------- | ------------------------------------------------------------------------ |
| as_of 未来数据   | `Layer3SnapshotError`；无部分 snapshot                                   |
| 非 staged L5 源  | 拒绝 build                                                               |
| scope 偏离       | 停止 Execute；回 Plan                                                    |
| lineage 字段缺失 | fail-fast（对齐 contract）                                               |
| 回滚             | 删除本分支新增 `snapshot_builder.py` + tests/fixtures；无 prod migration |

### 0.1 门控速查

| 项        | 值                                                    |
| --------- | ----------------------------------------------------- |
| 怎么测    | §8 RED→GREEN；`tests/test_layer3_snapshot_builder.py` |
| 怎么验收  | §10 Tier A                                            |
| 什么叫过  | §2 全部 AC + batch3 staged gate 仍绿                  |
| prod-path | Tier B：`pytest -q` 全库回归                          |
| 6.pre     | `research/gitnexus-execute-summary.md`                |

### 0.3 Execute 强制必读清单

**规则：** Phase 0 Boot **必须 Read `implement.jsonl` 每一条**；先读 `research/integration-ledger.md`。  
**禁止**在 §8.0 枚举路径清单 — 以 §0.3 + implement.jsonl 为准。

### 0.3a Execute 工程纪律 — Ponytail

**正式 Execute 全程强制**：

1. Boot 起 MUST Read `.cursor/rules/ponytail.mdc`；**每个 §8.x 步开始前**重新对照 ladder。
2. **写任何业务代码前**爬 ladder：YAGNI → 复用 `layer2_sensors/snapshot_builder.py` / `core/snapshot_lineage.py` → stdlib → 最小 diff。
3. **禁止**为本任务新增抽象层、未请求 helper、新依赖；有意简化用 `ponytail:` 注释标天花板。
4. TDD 顺序不变：RED → karpathy-guidelines → testing-guidelines → ponytail ladder → GREEN。
5. 每步 GREEN 证据须含一行 ponytail self-check。

### 0.3b Execute 工程纪律 — 测试与回归（强制）

1. **TDD 不可跳过**：每个 §8.x 步 MUST 先 RED → Read `karpathy-guidelines` + `testing-guidelines` → 再 GREEN。
2. **每步 GREEN 后** MUST Read `incremental-implementation`；仅跑当前步 RED + 已绿用例；**Tier B 全库 `uv run pytest -q` 仅 §8.6 一次**。
3. **任何代码修复后** MUST 至少跑 `uv run pytest tests/test_layer3_snapshot_builder.py -q`；§8.6 前不得跳过 Tier B。
4. **禁止弱化测试目的**：不得为通过而删除业务语义断言或改写 AC 覆盖面；允许重构测试实现，但 AC 不变。
5. **测试注释（中文）**：每个 `test_*` 须含 **目的**、**测试对象**、**验证点**、**失败含义**（对齐 `purpose`/`target`/`verifies`/`failure_meaning`）；**目的**与**失败含义**须通俗可读；**验证点**可附 AC/契约名。
6. **ponytail 违规**（过度抽象、未请求依赖）→ **停止当前 §8 步**，删 bloat 后再 GREEN。

### 0.4 上下文打包（v3）

Execute 以 MASTER inline + ledger pointer 为准。`context_pack.json` 空壳时以 `implement.jsonl` 为唯一路由（不双轨）。

### 0.5 Execute 开场白

```text
进入 Execute。MUST Read trellis-execute SKILL + ponytail（§0.3a）。Phase 0（§0.3 + ledger）→ §8.x（每步 ponytail ladder）→ §10 → Audit。勿 finish-work。
```

---

## 1. 目标

交付 `IndustryChainSnapshotBuilder`：消费 `020` `IndustryChainLoader` 的 typed 结果 + staged Layer5 bar fixture，生成 `industry_chain_daily_snapshot` 行、Layer5 映射视图、以及 contract-scoped lineage envelope。

### 1.1 目的

为 Batch 5 Layer4/完整 Layer5 集成提供可审计、可测试的 Layer3 日度快照骨架；证明 `as_of` 与未来数据边界。

### 1.2 前置

- `020` `IndustryChainLoader` merged（`backend/app/layer3_chains/loader.py`）
- Batch 3 staged gate CLOSED
- `R3-B23A-EVIDENCE-FOUNDATION` 最小契约稳定（本任务仅用 staged fixture，不依赖 live L5）
- **不**依赖 B-19 / `06-24-round3-real-data-staged-pilot-v2` merge；前置仅为 `020` + staged gate

### 1.3 约束

- staged-only；allowed：`backend/app/layer3_chains/snapshot_builder.py`、`backend/app/layer3_chains/lineage.py`（如需）、`tests/test_layer3_snapshot_builder.py`、`tests/fixtures/layer3_l5_staged_bars/**`
- forbidden：layer2/4/5 runtime 包内生产代码、datasources live fetch、lineage contract 写、production DB、FastAPI/CLI、registry 源文件修改

### 1.5 停止条件

| #   | 事件                                            | 处理                           |
| --- | ----------------------------------------------- | ------------------------------ |
| 1   | Plan 未 freeze / 用户未批准                     | 禁止 `task.py start`           |
| 2   | 触发 forbidden 路径修改                         | 立即停止；revert               |
| 3   | RED 非预期全库红                                | 停当前 §8 步                   |
| 4   | 声称 production-live                            | 中止；修正 MASTER/AUDIT        |
| 5   | 尝试 live Layer5 fetch 或读生产 DuckDB 行情     | **自定义停损** — 违反 AC-021-6 |
| 6   | `R3-B2.75-REQ2-EM` 被当作 unblock 依据          | 停止；回协调者                 |
| 7   | Execute 试图关闭 `ADV-R3X-LINEAGE-001` 全量范围 | 停止；仅允许 §3.2 登记边界     |

### 1.6 原计划归并

| 来源                                           | 内容                                   |
| ---------------------------------------------- | -------------------------------------- |
| `021_implement_layer3_snapshot_builder.md`     | snapshot + Layer5 mapping view         |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` § Batch 4 | as_of + lineage 主题                   |
| `layer3_industry_shock_anchor.md` §8.12.6      | daily snapshot 七步流程（staged 子集） |
| `snapshot_lineage_contract.yaml`               | required_fields + validation_tests     |
| 020 MASTER §3.2                                | lineage defer 边界延续                 |

---

## 2. 预期结果（AC）

| ID       | 预期结果                                                                                      | 验证链                                                          |
| -------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| AC-021-1 | loader 结果 + staged L5 bars → per-anchor snapshot 行                                         | §8.3; `test_layer3Snapshot_buildsFromStagedLoaderAndL5_success` |
| AC-021-2 | lineage envelope 含 `LINEAGE_REQUIRED_FIELDS` 全字段（`rebuild_reason` 可空）与 source hashes | §8.2; `test_layer3Snapshot_lineageRequiredFieldsComplete`       |
| AC-021-3 | `no_future_data`：as_of 之后观测拒绝                                                          | §8.4; `test_snapshotRejectsFutureInput`                         |
| AC-021-4 | `event_only` anchor 无价量字段                                                                | §8.5; `test_layer3Snapshot_eventOnly_skipsPriceFields`          |
| AC-021-5 | Layer5 mapping view 暴露 instrument_id + bar 字段                                             | §8.3; `test_layer3Snapshot_layer5MappingView_nonEventOnly`      |
| AC-021-6 | 仅 staged fixture 源                                                                          | §8.3; `test_layer3Snapshot_nonStagedL5Source_rejects`           |
| AC-021-7 | Tier A 门禁                                                                                   | §10                                                             |

---

## 3. 范围

### 3.1 In scope

- `backend/app/layer3_chains/snapshot_builder.py`
- `backend/app/layer3_chains/lineage.py`（可选；若 inline 更短则 ponytail 合并进 builder）
- `tests/test_layer3_snapshot_builder.py`
- `tests/fixtures/layer3_l5_staged_bars/`（最小 staged bar 子集，对齐 loader fixture anchor ticker）

### 3.2 Out of scope · defer · register

| 项                                                                               | 范围边界                                                                                                                                                                                                             | 偿还 / 登记                                                                                                |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **`ADV-R3X-LINEAGE-001`** — L3/L4 **完整** cross-layer snapshot lineage 持久化   | **021 in-scope：** L3 staged snapshot 骨架 + contract-scoped pytest（`test_snapshotRejectsFutureInput` 等）。**Out：** L4 market snapshot lineage、生产 DuckDB lineage 表写回、全量 `upstream_snapshot_ids` 跨层闭包 | **`022`/Batch 5** 完整 lineage；本 MASTER **仅登记 defer 边界**，Execute **不得**声称已关闭 ADV-R3X 全量项 |
| **`R3Y-LINEAGE-VR-001`** — R3Y AUD-06 要求的三 registry SSOT 行 + VR pytest 矩阵 | **021 in-scope：** 本表显式边界（Plan registry 可读）。**Out：** `AUDIT_DEFERRED_REGISTRY.md` / `UNRESOLVED_ISSUES_REGISTRY.md` 新增行、`test_round3_audit_registry_alignment.py` 扩展                               | **registry hygiene slice**（`fix-r3y-registry-lineage-defer`）；021 Execute **不改**三 registry 文件       |
| Layer4 market snapshots                                                          | 完整 market structure                                                                                                                                                                                                | `022`                                                                                                      |
| 完整 Layer5 evidence chain                                                       | instrument registry / bar ingest                                                                                                                                                                                     | `023`                                                                                                      |
| WriteManager DB sync / clean table 写                                            | 可选 sandbox                                                                                                                                                                                                         | defer；非 AC-021-7 必须                                                                                    |
| FastAPI `GET /api/layer3/*`                                                      | API 层                                                                                                                                                                                                               | Round 4+                                                                                                   |
| CLI `layer3 build-snapshot`                                                      | ops 入口                                                                                                                                                                                                             | Batch 6 / ops repay                                                                                        |
| `commodity` vs `public_equity` loader 语义（§8.12.11）                           | loader 硬规则外                                                                                                                                                                                                      | 已在 020 defer；021 不扩 loader                                                                            |
| `test_incrementalRebuildPreservesAsOfBoundary` 全量集成                          | incremental rebuild 跨日管道                                                                                                                                                                                         | Batch 5+；021 仅 stub/单测级 as_of 边界                                                                    |

### 3.3 禁止修改

- `backend/app/layer2_sensors/**`、`backend/app/layer4/**`、`backend/app/layer5/**`
- `specs/contracts/snapshot_lineage_contract.yaml`
- `specs/layer3_global_industry_chains/**`（registry 源）
- `docs/AUDIT_DEFERRED_REGISTRY.md`、`docs/UNRESOLVED_ISSUES_REGISTRY.md`（→ R3Y hygiene slice）
- production DB / live fetch

---

## 4. 代码地图

| 路径                                                 | 操作                                              |
| ---------------------------------------------------- | ------------------------------------------------- |
| `backend/app/layer3_chains/snapshot_builder.py`      | 创建 — `IndustryChainSnapshotBuilder`             |
| `backend/app/layer3_chains/lineage.py`               | 创建（可选）— `Layer3LineageBuilder`              |
| `backend/app/layer3_chains/models.py`                | 扩展 — snapshot row / mapping view / lineage 类型 |
| `tests/fixtures/layer3_l5_staged_bars/manifest.yaml` | 创建 — staged L5 bar bundle                       |
| `tests/fixtures/layer3_l5_staged_bars/*.json`        | 创建 — 对齐 MSFT 等 loader fixture anchor         |
| `tests/test_layer3_snapshot_builder.py`              | 创建 — §5.3 用例                                  |

---

## 5. 测试契约

### 5.0 规范

1. 注释：`purpose` / `target` / `verifies` / `failure_meaning`（中文）；`verifies` 标注 contract 规则
2. 只 mock 外部 I/O；as_of / lineage / event_only 逻辑用真实 fixture 值
3. 每测至少一条业务语义断言
4. 失败路径统一 `pytest.raises(Layer3SnapshotError)` + message 含规则语义

### 5.1 测试文件路径

| 路径                                    | 目标                                            | 测试目的                  | §8 步   |
| --------------------------------------- | ----------------------------------------------- | ------------------------- | ------- |
| `tests/test_layer3_snapshot_builder.py` | `backend/app/layer3_chains/snapshot_builder.py` | staged snapshot + lineage | 8.2–8.6 |

### 5.2 成功/失败语义

| 能力          | 成功怎么测                             | 失败怎么测                       | 场景 |
| ------------- | -------------------------------------- | -------------------------------- | ---- |
| snapshot 构建 | loader + L5 fixture → 非空 snapshot 行 | 缺 bar / 坏 manifest → 拒绝      | S1   |
| lineage       | envelope 含 hashes + layer_id=layer3   | 缺 hash → 拒绝                   | S2   |
| as_of 边界    | 过滤未来观测                           | 未来 trade_time → 拒绝           | S3   |
| event_only    | 无价量；可有 event 占位                | event_only 出现 price → 不应生成 | S4   |
| L5 mapping    | view 含 instrument_id + close          | 非 staged 源 → 拒绝              | S5   |

### 5.3 用例设计

| 测试文件                                | `test_*` 名称                                             | contract / AC | 断言语义                                                                   | §8  |
| --------------------------------------- | --------------------------------------------------------- | ------------- | -------------------------------------------------------------------------- | --- |
| `tests/test_layer3_snapshot_builder.py` | `test_layer3Snapshot_buildsFromStagedLoaderAndL5_success` | AC-021-1      | ≥1 非 event_only snapshot；含 as_of_timestamp                              | 8.3 |
| 同上                                    | `test_layer3Snapshot_nonStagedL5Source_rejects`           | AC-021-6      | manifest `source_mode != staged_fixture_only` 拒绝                         | 8.3 |
| 同上                                    | `test_layer3Snapshot_lineageRequiredFieldsComplete`       | AC-021-2      | 对 `LINEAGE_REQUIRED_FIELDS` 逐字段 `is not None`（`rebuild_reason` 可空） | 8.2 |
| 同上                                    | `test_snapshotRejectsFutureInput`                         | AC-021-3      | 未来观测 → 拒绝                                                            | 8.4 |
| 同上                                    | `test_layer3Snapshot_eventOnly_skipsPriceFields`          | AC-021-4      | OPENAI event_only 行无 latest_price                                        | 8.5 |
| 同上                                    | `test_layer3Snapshot_layer5MappingView_nonEventOnly`      | AC-021-5      | MSFT mapping 含 instrument_id + close                                      | 8.3 |
| 同上                                    | `test_layer3Snapshot_missingL5Bar_rejects`                | fail-fast     | 缺 ticker bar → 无部分结果                                                 | 8.3 |

**AUDIT A8 补测（Execute 未列）：** 空 loader 结果 — 见 `AUDIT.plan.md` §2 A8。

### 5.4 四层测试

| 层      | 范围                | 命令                                                           | 通过                         |
| ------- | ------------------- | -------------------------------------------------------------- | ---------------------------- |
| L1 单元 | snapshot + lineage  | `uv run pytest tests/test_layer3_snapshot_builder.py -q`       | exit 0                       |
| L2 集成 | 无 DB 写            | N/A 本任务                                                     | —                            |
| L3 管道 | batch3 staged gates | `uv run pytest tests/test_batch3_staged_downstream_gate.py -q` | exit 0                       |
| L4 E2E  | 全量回归            | `uv run pytest -q`                                             | exit 0；**仅 §8.6 执行一次** |

---

## 6. 接口/契约

- **权威 lineage：** `specs/contracts/snapshot_lineage_contract.yaml`（只读）
- **模块：** `docs/modules/layer3_industry_shock_anchor.md` §8.6.6 / §8.12.6（staged 子集）
- **loader 输入：** `backend/app/layer3_chains/loader.py` → `IndustryChainLoadResult`
- **模式参考：** `backend/app/layer2_sensors/snapshot_builder.py` + `lineage.py` + `backend/app/core/snapshot_lineage.py`

### 6.1 Staged Layer5 bar 协议（冻结 — 对齐 020 bundle）

| 项               | 约定                                                                                   |
| ---------------- | -------------------------------------------------------------------------------------- |
| 默认 bundle 常量 | `STAGED_LAYER3_L5_BARS_DIR` → `tests/fixtures/layer3_l5_staged_bars/`                  |
| mode 落点        | **`manifest.yaml` 根字段 `source_mode: staged_fixture_only`**                          |
| manifest 内容    | anchor ticker → instrument_id + bar 列表（trade_date, close, volume, as_of_timestamp） |
| 校验时机         | `build()` 首步读 manifest；非 staged → `Layer3SnapshotError`                           |
| fixture 体量     | 覆盖 loader fixture 中 ≥1 非 event_only anchor；总 bundle < 50KB                       |

### 6.2 Python API（示意）

```python
class IndustryChainSnapshotBuilder:
    def build(
        self,
        *,
        load_result: IndustryChainLoadResult,
        as_of: datetime,
        trade_date: date,
        l5_bundle_dir: Path | None = None,
    ) -> IndustryChainSnapshotBuildResult: ...
```

`IndustryChainSnapshotBuildResult` 含：`snapshots`、`lineage_envelopes`、`layer5_mapping_views`。

### 6.3 Staged snapshot row 字段冻结（021 子集）

| 字段                                         | 必填          | 说明               |
| -------------------------------------------- | ------------- | ------------------ |
| `anchor_id`, `trade_date`, `as_of_timestamp` | 是            | 快照键与边界       |
| `latest_price`, `pct_change_1d`              | 非 event_only | 来自 staged L5 bar |
| `volume`, `amount`                           | 可选          | staged 有则填      |
| `latest_event_title`, `latest_event_time`    | 可选          | event 占位         |
| `quality_flags`, `source_validation_status`  | 是            | 至少空列表/默认    |
| `open_interest`                              | 可选          | future 类 anchor   |

不得复制 Layer1 全量标准化字段（D-09）。

### 6.4 Layer5MappingView 冻结

| 字段              | 必填 | manifest 映射                          |
| ----------------- | ---- | -------------------------------------- |
| `instrument_id`   | 是   | `manifest.yaml` anchor → instrument_id |
| `trade_date`      | 是   | bar `trade_date`                       |
| `close`           | 是   | bar `close`                            |
| `volume`          | 可选 | bar `volume`                           |
| `as_of_timestamp` | 是   | bar `as_of_timestamp`                  |

---

## 7. Red Flags

| 风险                              | 预防                                          |
| --------------------------------- | --------------------------------------------- |
| live Layer5 fetch                 | AC-021-6 staged manifest                      |
| 写入 Layer3 全量行情历史          | 模块 doc §8.12.11；只 snapshot 行             |
| 绕过 as_of                        | AC-021-3                                      |
| 改 lineage contract / 三 registry | §3.3 + §3.2 R3Y boundary                      |
| 声称关闭 ADV-R3X 全量 lineage     | §3.2 显式 defer                               |
| 弱断言假绿                        | GLOBAL_TESTING_POLICY                         |
| production-live 声称              | §0 + gate tests                               |
| 过度工程                          | §0.3a ponytail；复用 L2 snapshot/lineage 模式 |

---

## 8. 实现步骤（RED/GREEN）

### 8.0 Boot gate

| 字段       | 内容                                                                                                                                          |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 按 **§0.3** 读 `implement.jsonl` + `integration-ledger.md`；§0.3a ponytail；创建测试骨架 + `layer3_l5_staged_bars` 最小 manifest；基线 pytest |
| RED 命令   | `uv run pytest tests/test_layer3_snapshot_builder.py -q`                                                                                      |
| GREEN 命令 | `uv sync --locked` + `research/execute-evidence/8.0-boot-reads.txt`                                                                           |
| RED 证据   | `research/execute-evidence/8.0-red.txt`                                                                                                       |
| GREEN 证据 | `research/execute-evidence/8.0-green.txt`                                                                                                     |
| 已执行     | [x]                                                                                                                                           |

### 8.1 Models

| 字段       | 内容                                                                                                                                |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 扩展 `models.py`：`IndustryChainDailySnapshotRow`、`Layer5MappingView`、`Layer3LineageEnvelope`、`IndustryChainSnapshotBuildResult` |
| RED 命令   | `uv run pytest tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_buildsFromStagedLoaderAndL5_success -q`                   |
| GREEN 命令 | 同上 exit 0                                                                                                                         |
| RED 证据   | `research/execute-evidence/8.1-red.txt`                                                                                             |
| GREEN 证据 | `research/execute-evidence/8.1-green.txt`                                                                                           |
| 已执行     | [x]                                                                                                                                 |

### 8.2 Lineage builder

| 字段       | 内容                                                                                               |
| ---------- | -------------------------------------------------------------------------------------------------- |
| 做什么     | `Layer3LineageBuilder`（或 inline）复用 `core/snapshot_lineage.py`；`layer_id=layer3`              |
| RED 命令   | `uv run pytest tests/test_layer3_snapshot_builder.py::test_snapshotLineageContainsSourceHashes -q` |
| GREEN 命令 | 同上 exit 0                                                                                        |
| RED 证据   | `research/execute-evidence/8.2-red.txt`                                                            |
| GREEN 证据 | `research/execute-evidence/8.2-green.txt`                                                          |
| 已执行     | [x]                                                                                                |

### 8.3 Snapshot builder core

| 字段       | 内容                                                                                                                                                                                                                                                                                                                                                                             |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | `IndustryChainSnapshotBuilder.build()` — join loader anchors + staged L5 bars + mapping view                                                                                                                                                                                                                                                                                     |
| RED 命令   | `uv run pytest tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_buildsFromStagedLoaderAndL5_success tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_layer5MappingView_nonEventOnly tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_nonStagedL5Source_rejects tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_missingL5Bar_rejects -q` |
| GREEN 命令 | 同上 exit 0                                                                                                                                                                                                                                                                                                                                                                      |
| RED 证据   | `research/execute-evidence/8.3-red.txt`                                                                                                                                                                                                                                                                                                                                          |
| GREEN 证据 | `research/execute-evidence/8.3-green.txt`                                                                                                                                                                                                                                                                                                                                        |
| 已执行     | [x]                                                                                                                                                                                                                                                                                                                                                                              |

### 8.4 as_of / no_future_data

| 字段       | 内容                                                                                      |
| ---------- | ----------------------------------------------------------------------------------------- |
| 做什么     | 过滤 `as_of_timestamp` 之后观测；对齐 contract `no_future_data`                           |
| RED 命令   | `uv run pytest tests/test_layer3_snapshot_builder.py::test_snapshotRejectsFutureInput -q` |
| GREEN 命令 | 同上 exit 0                                                                               |
| RED 证据   | `research/execute-evidence/8.4-red.txt`                                                   |
| GREEN 证据 | `research/execute-evidence/8.4-green.txt`                                                 |
| 已执行     | [x]                                                                                       |

### 8.5 event_only anchors

| 字段       | 内容                                                                                                     |
| ---------- | -------------------------------------------------------------------------------------------------------- |
| 做什么     | `event_only=true` 跳过价量；允许 event 占位字段                                                          |
| RED 命令   | `uv run pytest tests/test_layer3_snapshot_builder.py::test_layer3Snapshot_eventOnly_skipsPriceFields -q` |
| GREEN 命令 | 同上 exit 0                                                                                              |
| RED 证据   | `research/execute-evidence/8.5-red.txt`                                                                  |
| GREEN 证据 | `research/execute-evidence/8.5-green.txt`                                                                |
| 已执行     | [x]                                                                                                      |

### 8.6 Final gates

| 字段       | 内容                                                            |
| ---------- | --------------------------------------------------------------- |
| 做什么     | Tier A + batch3 gate + **Tier B 全库 pytest（本任务唯一一次）** |
| GREEN 命令 | 见 §10                                                          |
| RED 证据   | `research/execute-evidence/8.6-red.txt`                         |
| GREEN 证据 | `research/execute-evidence/8.6-green.txt`                       |
| 已执行     | [x]                                                             |

---

## 9. 四层测试（汇总）

见 §5.4。

---

## 10. Tier 验收

| Tier | 命令                                                                                          | 通过                     |
| ---- | --------------------------------------------------------------------------------------------- | ------------------------ |
| A    | `uv sync --locked`                                                                            | exit 0                   |
| A    | `uv run pytest tests/test_layer3_snapshot_builder.py -q`                                      | exit 0                   |
| A    | `uv run pytest tests/test_batch3_staged_downstream_gate.py -q`                                | exit 0                   |
| A    | `uv run ruff check backend/app/layer3_chains tests/test_layer3_snapshot_builder.py`           | exit 0                   |
| A    | `uv run python -m compileall backend/app/layer3_chains tests/test_layer3_snapshot_builder.py` | exit 0                   |
| B    | `uv run pytest -q`                                                                            | exit 0；**仅 §8.6 执行** |

**交接：** §8 证据齐 → Audit（非 finish-work）。§8.1–8.5 每步 GREEN 后仅跑当前步 RED 用例 + 既有全绿用例，**不**跑 Tier B。

---

## 11. Execute Skill 冻结

| Skill                                    | 本任务                        | 已执行 |
| ---------------------------------------- | ----------------------------- | ------ |
| trellis-execute                          | 必做                          | [x]    |
| test-driven-development                  | 必做                          | [x]    |
| incremental-implementation               | 必做（每步 GREEN 后 §0.3b-2） | [x]    |
| karpathy-guidelines                      | 必做                          | [x]    |
| testing-guidelines                       | 必做                          | [x]    |
| ponytail（`.cursor/rules/ponytail.mdc`） | 必做                          | [x]    |
| gitnexus-impact                          | 必做                          | [x]    |
| trellis-check                            | **不用**                      | —      |
| ponytail-review                          | **不用**                      | —      |

路径见 `execute-skill-paths.yaml`。

---

## 12. Audit 交接

- [x] §8 全部步骤已执行
- [x] `validate-execute-handoff` 通过
- [ ] 无 production-live 声称
- [ ] §3.2 ADV-R3X / R3Y 边界未被 Execute 越界关闭
