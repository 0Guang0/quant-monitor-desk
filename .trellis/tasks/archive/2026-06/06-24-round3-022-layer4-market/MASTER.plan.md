# MASTER 计划 — Round 3 Batch 5 `022` Layer 4 Market Structure

> **Execute 入口** — staged-only；**不得**声称 production-live readiness。  
> 索引：`research/source-index.md` · `context_pack.json` · Audit：`AUDIT.plan.md`  
> **Wave C Playbook：** `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.1 + §3.3 + §8.2

---

## 0. 元信息

| 字段                      | 值                                                             |
| ------------------------- | -------------------------------------------------------------- |
| 任务 slug                 | `06-24-round3-022-layer4-market`                               |
| 分支                      | `feature/round3-022-layer4-market` @ `555fd33b`                |
| 前置                      | `021` merged；`R3-B3-STAGED-DOWNSTREAM-GATE` CLOSED            |
| manifest_protocol_version | `3`                                                            |
| analysis_waiver           | `false`                                                        |
| 原计划                    | `research/source-index.md` · `research/original-plan-trace.md` |

### Staged downstream limitations（§16 / Wave C 强制）

1. `BATCH3_STAGED_DOWNSTREAM_GATE.md` — staged-only
2. `R3-B2.75-REQ2-EM` — **DEFERRED**；不得作 live 前提
3. `production_live_pilot_policy.md` — 不解锁生产访问
4. staged market fixture；无 live vendor / production DB writes
5. D-09 — Layer 2–5 不复制 Layer1 全套标准化字段；lineage 仅 contract 必需子集
6. 禁止修改 `snapshot_lineage_contract.yaml`（023A 写权限）

### Failure modes / 回滚

| 场景             | 处理                                                                     |
| ---------------- | ------------------------------------------------------------------------ |
| as_of 未来数据   | `Layer4MarketError`；无部分 snapshot                                     |
| 非 staged 源     | 拒绝 build                                                               |
| scope 偏离       | 停止 Execute；回 Plan                                                    |
| lineage 字段缺失 | fail-fast（对齐 contract）                                               |
| 回滚             | 删除本分支新增 `market_structure.py` + tests/fixtures；无 prod migration |

### 0.1 门控速查

| 项        | 值                                                    |
| --------- | ----------------------------------------------------- |
| 怎么测    | §8 RED→GREEN；`tests/test_layer4_market_structure.py` |
| 怎么验收  | §10 Tier A                                            |
| 什么叫过  | §2 全部 AC + playbook §8.2 + batch3 staged gate 仍绿  |
| prod-path | Tier B：`uv run pytest -q` 全库回归                   |
| 6.pre     | `research/gitnexus-execute-summary.md`                |

### 0.3 Execute 强制必读清单

**规则：** Phase 0 Boot **必须 Read `implement.jsonl` 每一条**；先读 `research/integration-ledger.md`。  
**禁止**在 §8.0 枚举路径清单 — 以 §0.3 + implement.jsonl 为准。

### 0.3a Execute 工程纪律 — Ponytail

**正式 Execute 全程强制**：

1. Boot 起 MUST Read `.cursor/rules/ponytail.mdc`；**每个 §8.x 步开始前**重新对照 ladder。
2. **写任何业务代码前**爬 ladder：YAGNI → 复用 L2/L3 snapshot/lineage → stdlib → 最小 diff。
3. **禁止**为本任务新增抽象层、未请求 helper、新依赖；有意简化用 `ponytail:` 注释标天花板。
4. TDD 顺序不变：RED → karpathy-guidelines → testing-guidelines → ponytail ladder → GREEN。
5. 每步 GREEN 证据须含一行 ponytail self-check。

### 0.3b Execute 工程纪律 — 测试与回归（强制）

1. **TDD 不可跳过**：每个 §8.x 步 MUST 先 RED → Read `karpathy-guidelines` + `testing-guidelines` → 再 GREEN。
2. **每步 GREEN 后** MUST Read `incremental-implementation`；仅跑当前步 RED + 已绿用例；**Tier B 全库 `uv run pytest -q` 仅 §8.7 一次**。
3. **任何代码修复后** MUST 至少跑 `uv run pytest tests/test_layer4_market_structure.py -q`；§8.7 前不得跳过 Tier B。
4. **禁止弱化测试目的**：不得为通过而删除业务语义断言；允许重构测试实现，但 AC 不变。
5. **测试注释（五字段）**：覆盖范围 / 测试对象 / 目的/目标 / 验证点 / 失败含义（对齐 playbook §2.2.1）。
6. **测试 ponytail（§2.2.2）**：`tests/` 增量同样遵守 ponytail；A2/A8 必审。
7. **模型约束（§2.3）**：Wave C 全部 agent 使用 **`composer-2.5`**；禁 `composer-2.5-fast`。

### 0.4 上下文打包（v3）

Execute 以 MASTER inline + ledger pointer 为准。`context_pack.json` 由 router 生成；manifest 以 `implement.jsonl` 为唯一路由。

### 0.5 Execute 开场白

```text
进入 Execute。MUST Read trellis-execute SKILL + ponytail（§0.3a）。Phase 0（§0.3 + ledger）→ §8.x（每步 ponytail ladder）→ §10 → Audit。勿 finish-work。
```

---

## 1. 目标

交付 `MarketStructureBuilder`（及最小 `MarketAdapter` staged 实现）：从 staged fixture 生成 `market_registry` / `market_calendar` / `market_breadth_snapshot` 行与 contract-scoped lineage envelope。

### 1.1 目的

为 Batch 5 下游 Layer 5 集成提供可审计、可测试的 Layer4 市场结构快照骨架；证明 `as_of` 与未来数据边界；推进 `ADV-R3X-LINEAGE-001` 的 **L4 contract 子集**。

### 1.2 前置

- `021` `IndustryChainSnapshotBuilder` merged
- Batch 3 staged gate CLOSED
- Wave C worktree `../quant-monitor-desk-wt-022-layer4`（MAP §2.2）
- **不**依赖 production-live pilot merge

### 1.3 约束

- staged-only；allowed：`backend/app/layer4_markets/**`、`tests/test_layer4_market_structure.py`、`tests/fixtures/layer4_staged_market/**`
- forbidden：`ops/staged_pilot.py`、`mutation_proof.py`、`staged_evidence.py`、registry 三件套修改

### 1.5 停止条件

| #   | 事件                                             | 处理                           |
| --- | ------------------------------------------------ | ------------------------------ |
| 1   | Plan 未 freeze / 用户未批准                      | 禁止 `task.py start`           |
| 2   | 触发 forbidden 路径修改                          | 立即停止；revert               |
| 3   | RED 非预期全库红                                 | 停当前 §8 步                   |
| 4   | 声称 production-live                             | 中止；修正 MASTER/AUDIT        |
| 5   | 尝试 live market fetch 或全市场 DuckDB 扫描      | **自定义停损** — 违反 AC-022-6 |
| 6   | `R3-B2.75-REQ2-EM` 被当作 unblock 依据           | 停止；回协调者                 |
| 7   | Execute 试图关闭 ADV-R3X 全量跨层 DB lineage     | 停止；仅允许 §3.2 L4 子集      |
| 8   | ResourceGuard `RESOURCE_GUARD_PAUSED` 非预期触发 | 停止；汇报 coordinator         |

### 1.6 原计划归并

| 来源                                           | 内容                                     |
| ---------------------------------------------- | ---------------------------------------- |
| `022_implement_layer4_market_structure.md`     | registry + calendar + breadth + snapshot |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` § Batch 5 | Layer4 market structure                  |
| `layer4_market_structure.md`                   | MarketAdapter + 表 + 验收                |
| `layer4_market_contract.yaml`                  | models + quality_rules                   |
| `snapshot_lineage_contract.yaml`               | required_fields + validation_tests       |
| playbook §8.2                                  | 022 PASS 子 AC                           |
| 021 MASTER §3.2                                | lineage defer 边界延续                   |

---

## 2. 预期结果（AC）

| ID       | 预期结果                                                         | 验证链                                                    |
| -------- | ---------------------------------------------------------------- | --------------------------------------------------------- |
| AC-022-1 | `market_registry` 种子行；`market_id` 唯一                       | §8.2; `test_marketRegistry_uniqueMarketIds`               |
| AC-022-2 | `market_calendar` PK 唯一；非交易日规则                          | §8.4; `test_marketCalendar_rejectsDuplicateTradeDate`     |
| AC-022-3 | `market_breadth_snapshot` contract required_fields 齐全          | §8.4; `test_marketBreadth_requiredFieldsPresent`          |
| AC-022-4 | lineage envelope 含 `LINEAGE_REQUIRED_FIELDS`；`layer_id=layer4` | §8.5; `test_marketSnapshot_lineageRequiredFieldsComplete` |
| AC-022-5 | `no_future_data`：as_of 之后观测拒绝                             | §8.6; `test_marketSnapshotRejectsFutureInput`             |
| AC-022-6 | staged fixture only；拒绝 live / 非 staged 源                    | §8.3; `test_marketAdapter_nonStagedSource_rejects`        |
| AC-022-7 | 不写入 Layer5 全量历史字段；不复制 Layer1 标准化 suite           | §8.7; `test_marketSnapshot_noLayer5HistoryFields`         |
| AC-022-8 | Tier A 门禁 + playbook §8.2 PASS                                 | §10                                                       |

### 2.1 Playbook §8.2 子 AC（Agent-2 勾销用）

| 维度           | PASS 条件（摘自 playbook §8.2）                                                                         | MASTER 映射   |
| -------------- | ------------------------------------------------------------------------------------------------------- | ------------- |
| **Plan**       | `validate-plan-freeze` exit 0；MASTER 含 L4 AC；**§3.3 全文已索引**；staged-only + `as_of`              | §SCI + §2     |
| **实现**       | `market_structure.py` 可运行；经 **WriteManager** 的 clean 写路径（若触及 DB）                          | §4 / §8       |
| **契约**       | 行为符合 `layer4_market_contract.yaml`；不复制 Layer5 大表；不输出交易动作语义                          | AC-022-3,7    |
| **Lineage**    | 快照含 §15 字段；测试证明 **no-future-data**                                                            | AC-022-4,5    |
| **测试**       | `test_layer4_market_structure.py` 全绿；五字段 + **§2.2.2**；ResourceGuard / eco 默认未触发全市场扫描   | §5 / §0.3b    |
| **MAP 验证**   | `uv run pytest tests/test_layer4_market_structure.py -q` 绿；`test_batch3_staged_downstream_gate.py` 绿 | §10 Tier A    |
| **任务卡验收** | `uv run pytest -q` 全绿；`ruff check` 相关路径无新增 error                                              | §10 Tier B    |
| **Audit**      | A1–A8 各维报告；A6 无性能面可 SKIP                                                                      | AUDIT.plan.md |
| **边界**       | 未改 `ops/staged_pilot.py`、`mutation_proof.py`、`staged_evidence.py`、registry 三件套                  | §3.3          |

---

## 3. 范围

### 3.1 In scope

- `backend/app/layer4_markets/market_structure.py`
- `backend/app/layer4_markets/lineage.py`（可选；ponytail inline 可合并）
- `backend/app/layer4_markets/models.py`（可选；类型内联可合并）
- `tests/test_layer4_market_structure.py`
- `tests/fixtures/layer4_staged_market/`（最小 staged bundle）

### 3.2 Out of scope · defer · register

| 项                                                                    | 范围边界                                                                                                                                              | 偿还 / 登记                                                    |
| --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **`ADV-R3X-LINEAGE-001`** — L4 **完整** cross-layer DB lineage 持久化 | **022 in-scope：** L4 staged snapshot + contract-scoped pytest + optional `upstream_snapshot_ids`。**Out：** 生产 DuckDB lineage 表写回、全量跨层闭包 | Batch 6 / ops repay；Execute **不得**声称已关闭 ADV-R3X 全量项 |
| **`R3Y-LINEAGE-VR-001`** — 三 registry SSOT 行 + VR pytest 矩阵       | **022 in-scope：** 本表显式边界。**Out：** 三 registry 文件修改                                                                                       | registry hygiene slice；022 Execute **不改**三 registry        |
| 全量 8× MarketAdapter live 实现                                       | registry 种子 + 1× staged adapter（`CN_A`）                                                                                                           | 后续 ops / batch                                               |
| Layer5 instrument 全量历史                                            | contract `does_not_store_layer5_full_history`                                                                                                         | `023`                                                          |
| WriteManager DB sync / clean table 写                                 | 可选 sandbox                                                                                                                                          | defer；非 AC-022-8 必须                                        |
| FastAPI `GET /api/layer4/*`                                           | API 层                                                                                                                                                | Round 4+                                                       |
| CLI `qm sync-layer4`                                                  | ops 入口                                                                                                                                              | Batch 6 repay                                                  |

### 3.3 禁止修改

- `backend/app/ops/staged_pilot.py`、`mutation_proof.py`、`backend/app/storage/staged_evidence.py`
- `backend/app/layer2_sensors/**`、`backend/app/layer3_chains/**`（只读参考；回归不破坏）
- `specs/contracts/snapshot_lineage_contract.yaml`
- `docs/AUDIT_DEFERRED_REGISTRY.md`、`docs/UNRESOLVED_ISSUES_REGISTRY.md`、`docs/RESOLVED_ISSUES_REGISTRY.md`
- production DB / live fetch / registry trio 并发写

---

## 4. 代码地图

| 路径                                                | 操作                                             |
| --------------------------------------------------- | ------------------------------------------------ |
| `backend/app/layer4_markets/market_structure.py`    | 创建 — `MarketStructureBuilder` + staged adapter |
| `backend/app/layer4_markets/lineage.py`             | 创建（可选）— `Layer4LineageBuilder`             |
| `backend/app/layer4_markets/models.py`              | 创建（可选）— registry/calendar/breadth 行类型   |
| `tests/fixtures/layer4_staged_market/manifest.yaml` | 创建 — `source_mode: staged_fixture_only`        |
| `tests/fixtures/layer4_staged_market/*.json`        | 创建 — CN_A 最小 calendar/breadth 行             |
| `tests/test_layer4_market_structure.py`             | 创建 — §5.3 用例                                 |

---

## 5. 测试契约

### 5.0 规范

1. 五字段 docstring（playbook §2.2.1）：覆盖范围 / 测试对象 / 目的/目标 / 验证点 / 失败含义
2. 只 mock 外部 I/O；as_of / lineage / quality 逻辑用真实 fixture 值
3. 每测至少一条业务语义断言
4. 失败路径统一 `pytest.raises(Layer4MarketError)` + message 含规则语义
5. `tests/` 代码遵守 ponytail（§2.2.2）

### 5.1 测试文件路径

| 路径                                    | 目标                                             | 测试目的                | §8 步   |
| --------------------------------------- | ------------------------------------------------ | ----------------------- | ------- |
| `tests/test_layer4_market_structure.py` | `backend/app/layer4_markets/market_structure.py` | staged market + lineage | 8.2–8.7 |

### 5.2 成功/失败语义

| 能力       | 成功怎么测                           | 失败怎么测                       | 场景 |
| ---------- | ------------------------------------ | -------------------------------- | ---- |
| registry   | 种子 market_id 唯一                  | 重复 id → 拒绝                   | S1   |
| calendar   | 合法交易日 breadth 可生成            | 重复 PK / 非交易日 → 拒绝或 flag | S2   |
| breadth    | required_fields 齐全                 | 缺字段 → quality_flag / 拒绝     | S3   |
| lineage    | envelope 含 hashes + layer_id=layer4 | 缺 hash → 拒绝                   | S4   |
| as_of 边界 | 过滤未来观测                         | 未来 as_of_timestamp → 拒绝      | S5   |
| staged 源  | manifest staged → 成功               | 非 staged → 拒绝                 | S6   |
| L5/L1 边界 | 无 layer5 历史字段 / 无 L1 标准化列  | 出现禁止字段 → 拒绝              | S7   |

### 5.3 用例设计

| 测试文件                                | `test_*` 名称                                       | contract / AC | 断言语义                                                  | §8  |
| --------------------------------------- | --------------------------------------------------- | ------------- | --------------------------------------------------------- | --- |
| `tests/test_layer4_market_structure.py` | `test_marketRegistry_uniqueMarketIds`               | AC-022-1      | registry 行 market_id 唯一                                | 8.2 |
| 同上                                    | `test_marketAdapter_nonStagedSource_rejects`        | AC-022-6      | manifest `source_mode != staged_fixture_only` 拒绝        | 8.3 |
| 同上                                    | `test_marketCalendar_rejectsDuplicateTradeDate`     | AC-022-2      | 重复 (market_id, trade_date) 拒绝                         | 8.4 |
| 同上                                    | `test_marketBreadth_requiredFieldsPresent`          | AC-022-3      | breadth required_fields 非空且符合 contract               | 8.4 |
| 同上                                    | `test_marketSnapshot_lineageRequiredFieldsComplete` | AC-022-4      | `LINEAGE_REQUIRED_FIELDS` 逐字段（`rebuild_reason` 可空） | 8.5 |
| 同上                                    | `test_marketSnapshotRejectsFutureInput`             | AC-022-5      | 未来观测 → 拒绝（对齐 contract 测试名）                   | 8.6 |
| 同上                                    | `test_marketSnapshot_noLayer5HistoryFields`         | AC-022-7      | 产出无 Layer5 全量历史语义字段                            | 8.7 |

### 5.4 四层测试

| 层      | 范围                | 命令                                                           | 通过                         |
| ------- | ------------------- | -------------------------------------------------------------- | ---------------------------- |
| L1 单元 | market + lineage    | `uv run pytest tests/test_layer4_market_structure.py -q`       | exit 0                       |
| L2 集成 | 无 DB 写            | N/A 本任务                                                     | —                            |
| L3 管道 | batch3 staged gates | `uv run pytest tests/test_batch3_staged_downstream_gate.py -q` | exit 0                       |
| L4 E2E  | 全量回归            | `uv run pytest -q`                                             | exit 0；**仅 §8.7 执行一次** |

---

## 6. 接口/契约

- **权威 module：** `docs/modules/layer4_market_structure.md`
- **主契约：** `specs/contracts/layer4_market_contract.yaml`
- **权威 lineage：** `specs/contracts/snapshot_lineage_contract.yaml`（只读）
- **上游：** `backend/app/layer3_chains/snapshot_builder.py` — optional `upstream_snapshot_ids`
- **模式参考：** `layer2_sensors/snapshot_builder.py` + `core/snapshot_lineage.py`

### 6.1 Staged market fixture 协议（冻结）

| 项           | 约定                                                              |
| ------------ | ----------------------------------------------------------------- |
| bundle 目录  | `tests/fixtures/layer4_staged_market/`                            |
| mode 落点    | **`manifest.yaml` 根字段 `source_mode: staged_fixture_only`**     |
| 默认市场     | `CN_A`（可扩展 registry 种子至 8 market_id，fixture 仅覆盖 1 个） |
| 校验时机     | `build()` 首步读 manifest；非 staged → `Layer4MarketError`        |
| fixture 体量 | calendar + breadth 各 ≥1 行；bundle < 50KB                        |

### 6.2 Python API（示意）

```python
class MarketStructureBuilder:
    def build(
        self,
        *,
        market_id: str,
        trade_date: date,
        as_of: datetime,
        bundle_dir: Path | None = None,
        upstream_snapshot_ids: tuple[str, ...] = (),
    ) -> MarketStructureBuildResult: ...
```

`MarketStructureBuildResult` 含：`registry_rows`、`calendar_rows`、`breadth_row`、`lineage_envelope`。

---

## 7. Red Flags

| 风险                              | 预防                                        |
| --------------------------------- | ------------------------------------------- |
| live market fetch / 全市场扫描    | AC-022-6 staged manifest + ResourceGuard    |
| 写入 Layer5 全量行情历史          | contract boundaries + AC-022-7              |
| 绕过 as_of                        | AC-022-5                                    |
| 改 lineage contract / 三 registry | §3.3 + §3.2 R3Y boundary                    |
| 声称关闭 ADV-R3X 全量 lineage     | §3.2 显式 defer                             |
| 输出交易动作语义                  | 任务卡 §8 + module doc                      |
| 弱断言假绿                        | GLOBAL_TESTING_POLICY + 五字段              |
| production-live 声称              | §0 + batch3 gate tests                      |
| 越界改 ops/staged                 | MAP forbidden + 停止条件 #2                 |
| 过度工程                          | §0.3a ponytail；复用 L2/L3 snapshot/lineage |
| grill D8 loader contract 缺失     | source-index 纠偏；不阻塞 Plan freeze       |

---

## 8. 实现步骤（RED/GREEN）

### 8.0 Boot gate

| 字段       | 内容                                                                                                                                         |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 按 **§0.3** 读 `implement.jsonl` + `integration-ledger.md`；§0.3a ponytail；创建测试骨架 + `layer4_staged_market` 最小 manifest；基线 pytest |
| RED 命令   | `uv run pytest tests/test_layer4_market_structure.py -q`                                                                                     |
| GREEN 命令 | `uv sync --locked` + `research/execute-evidence/8.0-boot-reads.txt`                                                                          |
| RED 证据   | `research/execute-evidence/8.0-red.txt`                                                                                                      |
| GREEN 证据 | `research/execute-evidence/8.0-green.txt`                                                                                                    |
| 已执行     | [x]                                                                                                                                          |

### 8.1 Models / registry seed

| 字段       | 内容                                                                                          |
| ---------- | --------------------------------------------------------------------------------------------- |
| 做什么     | `market_registry` 种子（8 market_id 元数据）；`MarketStructureBuildResult` 类型               |
| RED 命令   | `uv run pytest tests/test_layer4_market_structure.py::test_marketRegistry_uniqueMarketIds -q` |
| GREEN 命令 | 同上 exit 0                                                                                   |
| RED 证据   | `research/execute-evidence/8.1-red.txt`                                                       |
| GREEN 证据 | `research/execute-evidence/8.1-green.txt`                                                     |
| 已执行     | [x]                                                                                           |

### 8.2 Staged adapter + manifest

| 字段       | 内容                                                                                                 |
| ---------- | ---------------------------------------------------------------------------------------------------- |
| 做什么     | 最小 `StagedCNAMarketAdapter` + `manifest.yaml`；`source_mode` 门禁                                  |
| RED 命令   | `uv run pytest tests/test_layer4_market_structure.py::test_marketAdapter_nonStagedSource_rejects -q` |
| GREEN 命令 | 同上 exit 0                                                                                          |
| RED 证据   | `research/execute-evidence/8.2-red.txt`                                                              |
| GREEN 证据 | `research/execute-evidence/8.2-green.txt`                                                            |
| 已执行     | [x]                                                                                                  |

### 8.3 Calendar + breadth

| 字段       | 内容                                                                                                                                                                                    |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 从 fixture 加载 calendar + breadth；PK 唯一；contract required_fields                                                                                                                   |
| RED 命令   | `uv run pytest tests/test_layer4_market_structure.py::test_marketCalendar_rejectsDuplicateTradeDate tests/test_layer4_market_structure.py::test_marketBreadth_requiredFieldsPresent -q` |
| GREEN 命令 | 同上 exit 0                                                                                                                                                                             |
| RED 证据   | `research/execute-evidence/8.3-red.txt`                                                                                                                                                 |
| GREEN 证据 | `research/execute-evidence/8.3-green.txt`                                                                                                                                               |
| 已执行     | [x]                                                                                                                                                                                     |

### 8.4 Lineage builder

| 字段       | 内容                                                                                                        |
| ---------- | ----------------------------------------------------------------------------------------------------------- |
| 做什么     | `Layer4LineageBuilder` 复用 `core/snapshot_lineage.py`；`layer_id=layer4`；`upstream_snapshot_ids` 可选     |
| RED 命令   | `uv run pytest tests/test_layer4_market_structure.py::test_marketSnapshot_lineageRequiredFieldsComplete -q` |
| GREEN 命令 | 同上 exit 0                                                                                                 |
| RED 证据   | `research/execute-evidence/8.4-red.txt`                                                                     |
| GREEN 证据 | `research/execute-evidence/8.4-green.txt`                                                                   |
| 已执行     | [x]                                                                                                         |

### 8.5 Snapshot build core

| 字段       | 内容                                                                                                        |
| ---------- | ----------------------------------------------------------------------------------------------------------- |
| 做什么     | `MarketStructureBuilder.build()` 组装 registry/calendar/breadth + lineage                                   |
| RED 命令   | `uv run pytest tests/test_layer4_market_structure.py::test_marketSnapshot_lineageRequiredFieldsComplete -q` |
| GREEN 命令 | 同上 exit 0                                                                                                 |
| RED 证据   | `research/execute-evidence/8.5-red.txt`                                                                     |
| GREEN 证据 | `research/execute-evidence/8.5-green.txt`                                                                   |
| 已执行     | [x]                                                                                                         |

### 8.6 as_of / no_future_data

| 字段       | 内容                                                                                            |
| ---------- | ----------------------------------------------------------------------------------------------- |
| 做什么     | 过滤 `as_of_timestamp` 之后观测；对齐 contract `no_future_data`                                 |
| RED 命令   | `uv run pytest tests/test_layer4_market_structure.py::test_marketSnapshotRejectsFutureInput -q` |
| GREEN 命令 | 同上 exit 0                                                                                     |
| RED 证据   | `research/execute-evidence/8.6-red.txt`                                                         |
| GREEN 证据 | `research/execute-evidence/8.6-green.txt`                                                       |
| 已执行     | [x]                                                                                             |

### 8.7 Boundaries + final gates

| 字段       | 内容                                                                                                |
| ---------- | --------------------------------------------------------------------------------------------------- |
| 做什么     | L5/L1 边界断言 + Tier A + batch3 gate + **Tier B 全库 pytest（本任务唯一一次）** + ruff             |
| RED 命令   | `uv run pytest tests/test_layer4_market_structure.py::test_marketSnapshot_noLayer5HistoryFields -q` |
| GREEN 命令 | 见 §10                                                                                              |
| RED 证据   | `research/execute-evidence/8.7-red.txt`                                                             |
| GREEN 证据 | `research/execute-evidence/8.7-green.txt`                                                           |
| 已执行     | [x]                                                                                                 |

---

## 9. 四层测试（汇总）

见 §5.4。

---

## 10. Tier 验收

| Tier | 命令                                                                                 | 通过                            |
| ---- | ------------------------------------------------------------------------------------ | ------------------------------- |
| A    | `uv run pytest tests/test_layer4_market_structure.py -q`                             | exit 0                          |
| A    | `uv run pytest tests/test_batch3_staged_downstream_gate.py -q`                       | exit 0                          |
| A    | `uv sync --locked`                                                                   | exit 0                          |
| B    | `uv run pytest -q`                                                                   | exit 0（§8.7 一次）             |
| B    | `uv run ruff check backend/app/layer4_markets tests/test_layer4_market_structure.py` | 无新增 error 或 MASTER 记录豁免 |

**10.1 交接门槛：** §8 证据齐 · §5.1 文件已建 · AC-022-1..8 有对应用例 · §5.4+§10 B 已跑 · §1.5 未触发 · `validate-execute-handoff` 0

---

## 11. Execute Skill 冻结

| Skill                      | 本任务   | 绑定       | 已读 | 已执行 |
| -------------------------- | -------- | ---------- | ---- | ------ |
| trellis-execute            | 必做     | Boot       | [x]  | [x]    |
| test-driven-development    | 必做     | §8 RED     | [x]  | [x]    |
| incremental-implementation | 必做     | §8 SLICE   | [x]  | [x]    |
| karpathy-guidelines        | 必做     | GREEN      | [x]  | [x]    |
| testing-guidelines         | 必做     | 写测       | [x]  | [x]    |
| gitnexus-impact            | 必做     | 改 symbol  | [x]  | [x]    |
| systematic-debugging       | 条件     | DEBUG      | [ ]  | [ ]    |
| trellis-check              | **不用** | → Audit A1 | —    | —      |

路径见 `execute-skill-paths.yaml`。Audit → `AUDIT.plan.md`。

---

## 12. Source Context Index（SCI）

> **Plan 冻结要求：** playbook §3.1 + §3.3 **每一行**已索引；缺失路径见 `source-index.md` §A 纠偏。  
> **注：** 本节置于 §12，避免 §2 区块解析误收 wiring 路径。

### SCI-A — §3.1 四路共用底座

| 路径                                                          | 遵守什么 / 摘要                                     |
| ------------------------------------------------------------- | --------------------------------------------------- |
| `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`                 | Wave C 派发、PASS、模型、测试铁律                   |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2–§2.6                | worktree、allowed/forbidden、验证命令、gate hygiene |
| `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` §6 | 一分支一核心文件组                                  |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                             | 开放/已关闭 ID；**本分支只读**                      |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                          | 操作面 OPEN 项                                      |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                            | 防重复打开                                          |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`  | ID → 任务/分支映射                                  |
| `docs/ROUND3_HANDOFF.md`                                      | Round 3 入口与 staged-only 语境                     |
| `docs/quality/staged_acceptance_policy.md`                    | 分阶段验收                                          |
| `docs/quality/production_live_pilot_policy.md`                | 不得声称 production-live                            |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`               | Batch 3 下游 staged 门禁                            |
| `docs/quality/ROUND3_TEST_DOCSTRING_HYGIENE_PLAN.md`          | 测试五字段                                          |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`         | docs/specs 非实现路径边界                           |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`          | 语义测试                                            |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`         | eco / ResourceGuard                                 |
| `specs/contracts/runtime_versions.md`                         | 工具链与验证命令权威                                |
| `specs/contracts/write_contract.yaml`                         | 写路径合约                                          |
| `specs/contracts/resource_limits.yaml`                        | 资源上限                                            |
| `specs/contracts/snapshot_lineage_contract.yaml`              | 快照血缘                                            |
| `docs/architecture/module_boundary_matrix.md`                 | 模块边界                                            |
| `MIGRATION_MAP.md`                                            | 实现目录与文档映射                                  |

### SCI-B — §3.3 022 Layer 4 专属

**任务卡 / Prompt**

| 路径                                                                                                | 用途                      |
| --------------------------------------------------------------------------------------------------- | ------------------------- |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md`        | AC、验收命令、lineage §15 |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md`                                       | Layer 2–5 正式任务边界    |
| `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_execution_discipline_addendum.md` | 工程纪律                  |

**`docs/` 设计文档**

| 路径                                             | 用途                                                   |
| ------------------------------------------------ | ------------------------------------------------------ |
| `docs/modules/layer4_market_structure.md`        | **Layer 4 实现级权威**                                 |
| `docs/modules/layer3_industry_shock_anchor.md`   | 上游 Layer 3 接口语境                                  |
| `docs/modules/duckdb_and_parquet.md`             | 存储与只读/写入分层                                    |
| `docs/modules/write_manager.md`                  | clean 写入必经 WriteManager                            |
| `docs/architecture/03_runtime_flows.md`          | 运行链路                                               |
| `docs/architecture/04_data_architecture.md`      | 数据分层                                               |
| `docs/quality/final_package_rules.md`            | 包与产出规则                                           |
| `docs/quality/待修复清单.md`                     | `ADV-R3X-LINEAGE-001` defer 语境（§2）                 |
| `docs/adr/ADR-0004-layer3-shock-anchor-model.md` | Layer 3 模型（接口依赖）                               |
| `docs/quality/PENDING_USER_DECISIONS.md` §D-09   | Layer 2–5 lineage 字段范围（**替代** docs/decisions/） |

**`specs/` 契约**

| 路径                                             | 用途                                 |
| ------------------------------------------------ | ------------------------------------ |
| `specs/contracts/layer4_market_contract.yaml`    | **Layer 4 行为契约（主契约）**       |
| `specs/contracts/snapshot_lineage_contract.yaml` | 快照血缘字段（§3.1 已列）            |
| `specs/contracts/layer3_loader_contract.yaml`    | 上游 loader 口径（只读依赖）         |
| specs/schema/schema.sql（仓库缺失）              | 表 DDL → module §5 + contract models |

**实现邻接**

| 路径                                          | 用途               |
| --------------------------------------------- | ------------------ |
| `backend/app/layer3_chains/`（021 snapshot）  | 上游 snapshot 产出 |
| `backend/app/db/write_manager.py`             | WriteManager 对照  |
| `tests/test_layer3_snapshot_builder.py`       | L3 回归            |
| `tests/test_batch3_staged_downstream_gate.py` | staged gate 回归   |
