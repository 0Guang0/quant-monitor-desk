# Audit A5 — AC 完成度 / ACC-LAYER L2 子集 / 独立复验

| 字段     | 值                                                          |
| -------- | ----------------------------------------------------------- |
| 维度     | A5（audit-completion）                                      |
| 任务     | `07-02-wave4-r3-dcp-07-layer2`                              |
| 协议     | `plan_protocol_version: 4.1`                                |
| 分支     | `feature/wave4-r3-dcp-07-layer2`（worktree 含未提交实现）   |
| 审计日期 | 2026-07-02                                                  |
| 权威     | 代码 + 独立 pytest（不信文档 `[x]` / ledger 自述）          |

---

## 维度证据

### A5 checklist

| 项 | 结论 |
|----|------|
| 每条 AC → 代码/测试追溯链 + 评分 | 见下表；L2 子集 5 分；全量 pytest 门禁 4 分 |
| 独立复跑与实现一致 | DCP-07 定向测一致；**全量 `pytest -q` 两次结果不一致** |
| diff 无 silent 扩大 scope | 仅 `L2-VIX` P0 白名单 + `production_clean_replay` mode；无 L3–L5 实现 |
| prod-path（registry §2.1） | **不适用** — AUDIT.plan §1 未冻结 audit-prod-path；ENTRY 为 tmp_path replay |

### 独立复验（INDEX §2.1 · 最弱 2 行）

优先选与本票 AC 直接相关、且覆盖 lineage 契约的行。

| 原 §2.1 行 | 独立复跑命令 | 第 1 次 exit | 第 2 次 exit | 与代码行为一致 |
|------------|--------------|-------------:|-------------:|----------------|
| L2-VIX clean e2e（S01 主证据） | `uv run pytest tests/test_layer2_vix_clean_e2e.py -q` | **0** | **0**（含于 S00+S01 联跑） | ✅ `axis_observation`→snapshot+lineage 非 staged_fixture |
| 全量门禁 | `uv run pytest -q` | **0** | **1** | ⚠️ DCP-07 切片测绿；第 2 次 FAIL 来自 loop 工程测污染 |

**补充定向复验：**

| 命令 | exit | 备注 |
|------|-----:|------|
| `uv run pytest tests/test_layer2_sensor_loader.py -q` | **0** | 37 passed；含 `test_layer2Snapshot_lineageIncludesFetchIdsAndHashes` 契约 |
| `uv run pytest tests/test_layer2_clean_reader.py tests/test_layer2_vix_clean_e2e.py -q` | **0** | S00（5）+ S01（1）= 6 passed |

**第 2 次全量 FAIL 根因（plan 外 loop 工程）：**

```
FAILED tests/test_loop_engineering_flow.py::test_loopMaintain_check_passesWhenRepoFresh
FAILED tests/test_loop_engineering_flow.py::test_verificationMatrix_acLinksResolveToExistingTests
```

- `loop_maintain.py` 报 `verification_matrix: ... references test not in test_catalog: tests/test_x.py`（来自 `.audit-sandbox/pytest/**/MASTER.plan.md` 夹具）
- 同次还报 `active_master_tasks`：任务目录 `.audit-sandbox/pytest/**` 残留 `MASTER.plan.md`
- **非** DCP-07 实现逻辑错误；与 DCP-06 A5 同类「全量 pytest 顺序/夹具污染」模式

### GitNexus 追溯

| 动作 | 结果 |
|------|------|
| `query("Layer2 clean observation VIXCLS axis_observation e2e")` | 返回 Layer1 ingestion / axis_observation 相关流；**未索引** DCP-07 新符号 |
| `context("Layer2CleanObservationReader")` | **Symbol not found** — 索引滞后于 worktree 未提交新文件 |
| `detect_changes(scope=compare, base_ref=master)` | `changed_symbols: []`（新文件未入库）；`risk_level: low` |

**审计注记：** GitNexus 必用已执行；新符号 `Layer2CleanObservationReader` / `test_layer2_vix_clean_e2e` 须 `node .gitnexus/run.cjs analyze` 刷新后方可 impact。人工追溯链见下表补足。

### ACC-LAYER-E2E-LIVE-001 · L2 子集关账核对

| 登记点 | L2 子集 | L3–L5 阶段外置 |
|--------|---------|----------------|
| `AUDIT.plan.md` §3 | **关（部分）** L2 子集 | 阶段外置 L3–L5 全链 · L2 余量 · `B2.5-O-05` |
| `待修复清单.md` §4 | L2 ✅ `test_layer2_vix_clean_e2e` @ `feature/wave4-r3-dcp-07-layer2` | open → **Wave 4** DCP-08/10 + **Wave 5** R3H-05-GATE |
| `待修复清单.md` §8 | L1+L2 已通 | L3–L5 production_live 全链 open |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 | DCP-07 行 L2 ✅ | L3–L5 → DCP-08/10 + R3H-05-GATE |
| `R3_DCP_TO_ISSUES_INDEX.md` §6.4 | L2 子集 [x] | L3–L5 全链 [ ] 阶段外置 |
| `audit-repair-ledger-s02.md` | #1 **已修复** | #3 **阶段外置** DCP-08/10 + R3H-05-GATE；#4–#6 余量/B2.5-O-05 **阶段外置** |
| `MODULE_COMPLETION_RATING.md` G2 行 | **R3→R4** + clean replay e2e 证据 | L3–L5 → DCP-08/10；R3H-05-GATE |

**L3–L5 未假全关：** 台账三处 + S02 ledger #3 均显式 open 并绑任务 ID；**无**「ACC-LAYER 全链 PASS」自述。

### AC 评分表（1–5 rubric）

| # | 范围 | 分 | 追溯链（任务 → 代码/测试） | 缺口 |
|---|------|---:|----------------------------|------|
| **1** | **S00 `Layer2CleanObservationReader`** | **5** | 活卡 §5 P0 clean → `to-issues` S00 → `backend/app/layer2_sensors/clean_observation_reader.py` → `tests/test_layer2_clean_reader.py`（5 测：读入/fail-closed/拒 staged/row_cap/registry mode） | — |
| **2** | **S01 L2-VIX clean e2e** | **5** | ADR-032 → `tests/test_layer2_vix_clean_e2e.py`：`seed_macro_series(VIXCLS,fred)` → `Layer2CleanObservationReader` → `CrossAssetSnapshotBuilder` → `Layer2SnapshotWriter`；`source_used==fred`；lineage fetch_id/hash 与 DB 一致 | — |
| **3** | **lineage 契约对齐** | **5** | 活卡 §5 lineage 项 → S01 断言 `lineage.source_fetch_ids` / `source_content_hashes` + `axis_snapshot_lineage` DB 行；语义对齐 `test_layer2Snapshot_lineageIncludesFetchIdsAndHashes`（WM 写入 JSON 列） | clean e2e 未重复断言 `rule_version`/`parameter_hash`（S01 AC 未要求） |
| **4** | **`ACC-LAYER-E2E-LIVE-001` L2 子集关账** | **5** | S02 AC → `audit-repair-ledger-s02.md` #1 **已修复**；registry 四路登记；`test_layer2_vix_clean_e2e` 独立绿 | 活卡 `R3_DCP_07_LAYER2_CROSS_ASSET.md` §5 勾选仍为 `[ ]`（文档滞后，非功能缺口） |
| **5** | **L3–L5 + 余量阶段外置** | **5** | S02 ledger #3–#6；`DEBT.plan`；ADR-032 §Consequences；`00-EXECUTION-ENTRY.md` §1「不在范围」 | L3–L5 **刻意 open**（符合 AUDIT.plan §3） |
| **6** | **ENTRY/活卡 `uv run pytest -q` 硬门禁** | **4** | 独立第 1 次全绿；第 2 次 exit 1（loop 工程测） | 一次复验即绿未稳定 |

### S00–S02 切片 ↔ 证据对照

| 切片 | 实现锚点 | 测试 / 台账 |
|------|----------|-------------|
| S00 | `clean_observation_reader.py`；`sensor_loader.py` `production_clean_replay` + `P0_CLEAN_REPLAY_ASSET_IDS` | `test_layer2_clean_reader.py`（5） |
| S01 | 同上 + `CrossAssetSnapshotBuilder` / `Layer2SnapshotWriter` | `test_layer2_vix_clean_e2e.py`（1） |
| S02 | registry 三件套 + G2 评级行 | `audit-repair-ledger-s02.md`；`MODULE_COMPLETION_RATING.md` G2 |

### diff 范围核对（vs `master`）

| 类别 | 文件 | 范围判定 |
|------|------|----------|
| 新增 | `clean_observation_reader.py` | 单 P0 `L2-VIX`；`FORBIDDEN_FALLBACK_SOURCE_PREFIXES` |
| 新增 | `test_layer2_clean_reader.py`、`test_layer2_vix_clean_e2e.py` | 仅 DCP-07 AC |
| 新增 | `tests/fixtures/layer2_cross_asset_registry_clean_replay.yaml` | P0 replay registry |
| 修改 | `sensor_loader.py` | `production_clean_replay` mode；fred primary 限 `L2-VIX` |
| 修改 | `待修复清单.md`、`ROADMAP`、`R3_DCP_TO_ISSUES_INDEX.md`、`MODULE_COMPLETION_RATING.md` | S02 台账 |
| 未触及 | L3 loader / L4 market / L5 evidence | 符合「不在范围」 |

**无 silent 扩大：** `P0_CLEAN_REPLAY_ASSET_IDS = frozenset({"L2-VIX"})` 双处（reader + loader）一致；未新增 migration。

### 文档 vs 代码偏差

| 文档声称 | 独立复验 |
|----------|----------|
| `EXECUTION_INDEX.md` §2.1 `uv run pytest -q` exit 0 | 第 1 次 **0**；第 2 次 **1** |
| `audit-repair-ledger-s02.md` 全量 pytest exit 0 | 与第 1 次一致；第 2 次不一致 |
| 活卡 §5 末项 `uv run pytest -q` | 同上 |
| `EXECUTION_INDEX.md` §1 `[x]` S00–S02 | 定向测绿；全量门禁见上 |

---

## §维度裁决

**FAIL**

**理由：** §计划外发现含 ≥1 行非占位 finding（全量 `pytest -q` 第 2 次独立复验 exit 1，loop 工程夹具污染）。**L2 子集 AC（表 #4–#5）追溯链完整且定向 pytest 全绿**；表 #6 因全量不稳定扣至 4 分。

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
|----|---|------|------|------|----------|------|
| A5-P2-001 | P2 | ENTRY/活卡全量 pytest 一次复验未稳定绿 | `00-EXECUTION-ENTRY.md` §3；`R3_DCP_07_LAYER2_CROSS_ASSET.md` §5 | 完成条件绑定 `uv run pytest -q` exit 0；独立第 2 次 FAIL（根因见计划外 A5-P2-002） | Repair：隔离 loop 测对 `.audit-sandbox` 的 MASTER.plan 夹具；或 Execute 收尾前清理 sandbox；连续 2 次全绿后再勾活卡 §5 | `uv run pytest -q` 连续 2 次 exit 0 |

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
|----|---|------|------|------|----------|------|
| A5-P2-002 | P2 | loop 工程测污染任务 `.audit-sandbox` | `tests/test_loop_engineering_flow.py`；`test_task_archive_gates.py` `tests/test_x.py` 夹具 | 全量 pytest 运行中生成 `07-02-wave4-r3-dcp-07-layer2/.audit-sandbox/pytest/**/MASTER.plan.md`，触发 `loop_maintain` / `check_matrix` FAIL | 改 sandbox 至 `tmp_path`；或 `loop_maintain` 忽略 `.audit-sandbox`；禁止在活跃任务目录落 MASTER.plan 夹具 | `uv run pytest tests/test_loop_engineering_flow.py -q` 连续 2 次 exit 0；全量连续 2 次 exit 0 |
| A5-P3-001 | P3 | GitNexus 索引滞后新符号 | `Layer2CleanObservationReader` context not found | worktree 新文件未 commit / 未 re-analyze | merge 前 `node .gitnexus/run.cjs analyze`；改 symbol 前 `impact()` | `context("Layer2CleanObservationReader")` 返回定义与 callers |

已对抗搜索：`clean_observation_reader.py` · `test_layer2_vix_clean_e2e.py` · `test_layer2_clean_reader.py` · `sensor_loader.py` `production_clean_replay` · `待修复清单.md` §4/§8 · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 · `R3_DCP_TO_ISSUES_INDEX.md` §6.4 · `audit-repair-ledger-s02.md` · `MODULE_COMPLETION_RATING.md` G2 · `ADR-032` · `tests/test_loop_engineering_flow.py` · GitNexus query/context/detect_changes。

---

## pytest exit codes（摘要）

```
uv run pytest tests/test_layer2_vix_clean_e2e.py -q           → 0
uv run pytest tests/test_layer2_sensor_loader.py -q           → 0
uv run pytest tests/test_layer2_clean_reader.py \
            tests/test_layer2_vix_clean_e2e.py -q             → 0
uv run pytest -q                                            → run1: 0  run2: 1
```
