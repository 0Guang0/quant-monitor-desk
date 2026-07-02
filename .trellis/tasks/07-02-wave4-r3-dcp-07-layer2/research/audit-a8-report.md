# Audit A8 — 测试缺口（R3-DCP-07）

> **维：** A8 · test-gap / QA  
> **任务：** `07-02-wave4-r3-dcp-07-layer2`  
> **plan_protocol_version:** 4.1  
> **模板：** `agents/qa-expert.md`  
> **日期：** 2026-07-02  
> **工作目录：** `quant-monitor-desk-wt-dcp07`

---

## 维度证据

### Boot 追溯

| 权威 | 用途 |
|------|------|
| `AUDIT.plan.md` §1–§2 | PASS 门槛 · A8=`uv run pytest -q` |
| `research/to-issues-slices.md` | S00–S02 切片 AC 与建议测试 |
| `research/plan-doubt-review.md` | Red Flags Q1–Q5 |
| `docs/decisions/ADR-032-dcp07-layer2-vix-clean-read.md` | P0 锚点 · no-fallback · replay |
| `EXECUTION_INDEX.md` §2 / §2.1 | AC↔测试 · 复验命令 |
| `.cursor/skills/testing-guidelines/SKILL.md` | 五字段 · 语义断言 · sandbox |

### 独立复验命令

```bash
# A8 全量（AUDIT.plan §2）
mkdir -p .trellis/tasks/07-02-wave4-r3-dcp-07-layer2/.audit-sandbox/pytest
uv run pytest -q --basetemp=".trellis/tasks/07-02-wave4-r3-dcp-07-layer2/.audit-sandbox/pytest"
# exit 1（2026-07-02 独立跑）

# DCP-07 Layer2 子集
uv run pytest tests/test_layer2_clean_reader.py tests/test_layer2_vix_clean_e2e.py tests/test_layer2_sensor_loader.py -q \
  --basetemp=".trellis/tasks/07-02-wave4-r3-dcp-07-layer2/.audit-sandbox/pytest"
# exit 0 · 43 passed
```

**全量失败样例（与本票 Layer2 模块无关）：**

| 测试 | 模块 |
|------|------|
| `test_qmdData_syncMootdx_operatorAuthRequired` | `test_qmd_data_sync_mootdx.py` |
| `test_validateExecuteHandoff_skipsArchivedLegacy` | `test_task_archive_gates.py` |
| `test_tdx02_mockedEquity_writesRawEvidenceWithLineage` | `test_tdx_manual_probe.py` |
| `test_validatePlanFreeze_skipsArchivedLegacy` | `test_trellis_validate_plan.py` |
| `test_datasourceService_usEquityFetch_exposesTradingSessionWindow` | `test_us_trading_calendar.py` |

### Red Flag → 测试映射（§3.8）

| Red Flag / 切片 AC | 覆盖测试 | 判定 |
|--------------------|----------|------|
| Q1 · ADR-032 P0=L2-VIX / VIXCLS | `test_layer2CleanReader_readsVixclsFromAxisObservation` · `test_layer2_vix_clean_e2e_*` | 有测 |
| Q2 · 全 staging→clean pipeline | `audit-repair-ledger-s02.md` #4 阶段外置 Batch 4/5 | explicit defer |
| Q3 · P0-only `production_clean_replay` 白名单 | 正向：`test_layer2CleanReplayRegistry_loadsP0VixPrimaryFred` | **缺负向** |
| Q3 · no EasyXT fallback | `test_layer2CleanReader_emptyMacro_failClosedNoFallback` · `rejectsStagedFixtureSourceUsed` | 有测 |
| Q4 · ACC-LAYER L2 子集（L3–L5 外置） | `test_layer2_vix_clean_e2e` + S02 ledger | 有测 / defer |
| Q5 · replay 默认非 live | e2e 用 `bootstrap_layer1_clean_db` + `source_used=fred` | 有测 |
| S00 · `Layer2CleanObservationReader` | `test_layer2_clean_reader.py`（5 条） | 有测 |
| S01 · clean snapshot + lineage | `test_layer2_vix_clean_e2e.py`（1 条） | 有测 |
| S02 · 全量 pytest 绿 | 见上 · **exit 1** | **未满足** |
| lineage 契约对齐 | `test_layer2Snapshot_lineageIncludesFetchIdsAndHashes`（staged 路径）+ e2e DB 断言 | 有测 |
| row_cap | `test_layer2CleanReader_respectsRowCap` | 有测 |

### 五字段 / 语义断言抽检

| 文件 | test_* 数 | 五字段 docstring | 弱断言 |
|------|-----------|------------------|--------|
| `test_layer2_clean_reader.py` | 5 | 5/5 齐全 | 无（均有业务值断言） |
| `test_layer2_vix_clean_e2e.py` | 1 | 1/1 齐全 | 无（source/lineage/DB 行） |
| `test_layer2_sensor_loader.py` | 多条既有 | 抽检 lineage/VR 负向有目的 | 无 tautology |

### test_catalog 对照

| 模块 | catalog `purpose` | 实际 |
|------|-------------------|------|
| `test_layer2_clean_reader.py` | S00 DCP-07 | 一致 |
| `test_layer2_vix_clean_e2e.py` | 「RED stub placeholder」 | **与实现不符**（已有完整 S01 e2e） |

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A8-P0-001 | P0 | 全量 `uv run pytest -q` 未绿 | AUDIT.plan §1 PASS门槛 · §2 A8 · INDEX §2.1 · S02 ledger #关账 | 独立全量跑测 exit 1；5 条失败均非 Layer2 本票新增模块，但与任务 AC「pytest 全绿」冲突 | 主会话/Repair：逐条修上述 5 失败或确认 worktree 基线漂移后 rebase；本票不得宣称 finish-work 前全绿 | `uv run pytest -q` exit 0 |

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A8-P2-001 | P2 | `production_clean_replay` P0 白名单缺 loader 负向测 | plan-doubt Q3 · `sensor_loader.py` L213–217 | 仅 `test_layer2CleanReplayRegistry_loadsP0VixPrimaryFred` 覆盖正向；非 L2-VIX 资产 `primary_source=fred` 抛 `CrossAssetRegistryLoadError` 无 pytest | 在 `test_layer2_clean_reader.py` 或 `test_layer2_sensor_loader.py` 增 1 条：tmp yaml `mode: production_clean_replay` + 非 P0 资产 `primary_source: fred` → `pytest.raises(..., match=P0-whitelist)` | `uv run pytest tests/test_layer2_clean_reader.py -q` 绿且新测 RED→GREEN |
| A8-P2-002 | P2 | `Layer2CleanObservationReader` 非白名单 asset 缺负向测 | `clean_observation_reader.py` L122–125 · plan-doubt Q3 | reader 对 `asset_id ∉ P0_CLEAN_REPLAY_ASSET_IDS` 抛 `KeyError`；无直接单测 | 增 1 条：构造合法 `CrossAssetRegistryEntry`（如 L2-COPPER）调用 `read_observations` → `pytest.raises(KeyError, match=whitelist)` | `uv run pytest tests/test_layer2_clean_reader.py -q` 绿 |
| A8-P3-001 | P3 | `test_catalog.yaml` e2e purpose 陈旧 | `tests/test_catalog.yaml` L768 · loop catalog | purpose 仍写「Execute S01 RED stub」；与 `test_layer2_vix_clean_e2e.py` 实装不一致，削弱 Audit/loop 追溯 | `uv run python scripts/loop_maintain.py --fix` 或手改 catalog：`purpose`/`verifies` 对齐 ADR-032 + S01 AC | `uv run python scripts/loop_maintain.py` exit 0 |

已对抗搜索：`tests/test_layer2*.py` 全文 · `backend/app/layer2_sensors/{clean_observation_reader,sensor_loader}.py` 守卫分支 · `test_catalog.yaml` layer2 段 · `plan-doubt-review` Q1–Q5 · `integration-audit.md` Execute GAP 表 · 全库 grep `production_clean_replay` / `P0_CLEAN_REPLAY` / `whitelist`（Layer2 域无其他负向测）。

---
