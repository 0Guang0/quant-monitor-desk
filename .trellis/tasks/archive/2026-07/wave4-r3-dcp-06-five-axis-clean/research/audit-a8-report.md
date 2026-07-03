# Audit A8 — 测试缺口 / pytest 全绿 / catalog

> **维：** A8（test gap / pytest full green / catalog）  
> **任务：** `wave4-r3-dcp-06-five-axis-clean`  
> **plan_protocol_version:** 4.1  
> **日期：** 2026-07-02  
> **Boot：** `testing-guidelines` · `agents/audit-finding-schema.md` · `research/to-issues-slices.md`

---

## 维度证据

### 独立命令（A8 必跑）

| 命令                                                                    | exit code | 备注                |
| ----------------------------------------------------------------------- | --------- | ------------------- |
| `uv run pytest -q --basetemp=.audit-sandbox/pytest`                     | **1**     | 2 FAILED（见下）    |
| `uv run python scripts/loop_maintain.py`                                | **0**     | `OK: loop maintain` |
| DCP-06 范围子集（8 模块，见下表）                                       | **0**     | 41 passed           |
| `uv run python -m pytest tests/test_docstring_quadruple_coverage.py -q` | **0**     | 全库五字段门禁绿    |

**全量 pytest 失败摘要：**

| 测试                                                                                   | 失败原因                                                                                         |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `tests/test_qmd_data_sync_baostock.py::test_qmdData_syncBaostock_operatorAuthRequired` | `pytest.raises(CliFailure, match="operator")` — DID NOT RAISE                                    |
| `tests/test_qmd_data_sync_mootdx.py::test_qmdData_syncMootdx_operatorAuthRequired`     | 期望 `operator`；实际 `mootdx incremental sync requires mootdx as routed primary; got 'akshare'` |

> 与 DCP-06 切片无直接代码触点；但 `AUDIT.plan.md` §1 PASS 门槛要求 **pytest 全绿**，故阻塞 A8 PASS。

### 切片 ↔ 测试模块 ↔ catalog（S00–S07）

| 切片    | 测试模块                                           | test\_\* 数 | `test_catalog.yaml` | 五字段 docstring | 范围 pytest |
| ------- | -------------------------------------------------- | ----------- | ------------------- | ---------------- | ----------- |
| **S00** | `tests/test_layer1_clean_reader.py`                | 6           | ✅ `purpose: S00`   | ✅ 6/6           | ✅          |
| **S01** | `tests/test_layer1_environment_clean_e2e.py`       | 1           | ✅ S01              | ✅ 1/1           | ✅          |
| **S02** | `tests/test_layer1_credit_stress_clean_e2e.py`     | 1           | ✅ S02              | ✅ 1/1           | ✅          |
| **S03** | `tests/test_layer1_risk_appetite_clean_e2e.py`     | 1           | ✅ S03              | ✅ 1/1           | ✅          |
| **S04** | `tests/test_layer1_liquidity_clean_e2e.py`         | 1           | ✅ S04              | ✅ 1/1           | ✅          |
| **S05** | `tests/test_layer1_sentiment_clean_e2e.py`         | 1           | ✅ S05              | ✅ 1/1           | ✅          |
| **S06** | `tests/test_layer1_five_axis_panel_clean_smoke.py` | 5           | ✅ S06              | ✅ 5/5           | ✅          |
| **S07** | （Repair；无独立模块）                             | —           | —                   | —                | —           |

**S07 Repair 证据落点：** `test_layer1_five_axis_panel_clean_smoke.py`（LIQ 解读链）、`test_layer1_clean_reader.py`（row_cap）、`test_model_input_whitelist.py::test_layer1_p0_dcp06_cleanReplayProven` — 均已纳入上表模块。

**DCP-06 范围子集命令：**

```text
uv run python -m pytest \
  tests/test_layer1_clean_reader.py \
  tests/test_layer1_environment_clean_e2e.py \
  tests/test_layer1_credit_stress_clean_e2e.py \
  tests/test_layer1_risk_appetite_clean_e2e.py \
  tests/test_layer1_liquidity_clean_e2e.py \
  tests/test_layer1_sentiment_clean_e2e.py \
  tests/test_layer1_five_axis_panel_clean_smoke.py \
  tests/test_model_input_whitelist.py -q --basetemp=.audit-sandbox/pytest
```

### 子任务 AC 核对

| 子任务      | 要求                                 | 证据                                                                                                                                                                                                                                                                                                    | 结论          |
| ----------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| **K2/FR-4** | 五轴 e2e + panel 五字段              | S01–S05 各 1 条垂直 e2e；S06 `test_layer1FiveAxisPanel_cleanSmoke_allP0AxesProduceFeatures` 含 LIQ `AxisInterpretationEngine`；17/17 五字段 OK                                                                                                                                                          | ✅ 范围内满足 |
| **K1/FR-6** | whitelist 测试                       | `test_layer1_p0_dcp06_cleanReplayProven` + `test_dcp06K1_whitelistAlignsP0CleanBindings`；`test_catalog.yaml` 含 `test_model_input_whitelist.py`                                                                                                                                                        | ✅            |
| **A4/FR-5** | row_cap / ResourceGuard / window_cap | `test_layer1CleanReader_macroRespectsWhitelistRowCap`、`test_layer1CleanReader_barHistoryRespectsWhitelistRowCap`；`test_layer1FiveAxisPanel_resourceGuardHardStop_blocksFeatureCompute` + `test_layer1FiveAxisPanel_resourceGuardOnMigratedDb`；`test_layer1FiveAxisPanel_windowLenWithinWhitelistCap` | ✅            |
| **L1**      | panel 集成                           | S06 五轴同库 smoke + `bootstrap_layer1_clean_db(tmp_path)` 隔离                                                                                                                                                                                                                                         | ✅            |

### `clean_observation_reader.py` 对抗性路径矩阵

| 路径 / 分支                                      | 生产行为                                                      | 测试覆盖                                                   | 缺口           |
| ------------------------------------------------ | ------------------------------------------------------------- | ---------------------------------------------------------- | -------------- |
| macro 空库                                       | `CleanObservationReadError`                                   | `test_layer1CleanReader_emptyMacro_failClosedNoFallback`   | —              |
| **bar 空库**                                     | `read_bar_history` → `CleanObservationReadError`              | 无直接用例                                                 | **缺口**       |
| macro `staged_fixture`                           | `CleanObservationFallbackForbiddenError`                      | `test_layer1CleanReader_rejectsStagedFixtureSourceUsed`    | —              |
| **bar `staged_fixture` / `macro_supplementary`** | `read_bar_history` L193–196 拒绝                              | 无                                                         | **缺口**       |
| macro `macro_supplementary` 前缀                 | `_row_to_observation` L96–98 拒绝                             | 无                                                         | **缺口**       |
| macro row_cap 溢出                               | `resolve_read_limit` 钳制                                     | `test_layer1CleanReader_macroRespectsWhitelistRowCap`      | —              |
| **bar row_cap 溢出**                             | `resolve_bar_read_limit` 钳制                                 | `test_layer1CleanReader_barHistoryRespectsWhitelistRowCap` | —              |
| Amihud 全 bar 无效                               | `amihud_observations_from_bars` → `CleanObservationReadError` | 无                                                         | **缺口（低）** |
| 未知 macro spec_id                               | `resolve_macro_db_key` → `KeyError`                           | 无                                                         | **缺口（低）** |

**已读源码：** `backend/app/layer1_axes/clean_observation_reader.py` L16–208 · 对照 `tests/test_layer1_clean_reader.py` 与五轴 e2e。

### checklist（A8）

| 项                                                             | 状态               |
| -------------------------------------------------------------- | ------------------ |
| S00–S06 测试模块存在且 catalog 登记                            | ✅                 |
| K1 whitelist 模块 catalog 登记                                 | ✅                 |
| 任务新增/修改 `test_*` 五字段 docstring                        | ✅（17/17 范围项） |
| `loop_maintain.py` check                                       | ✅                 |
| **`uv run pytest -q` 全绿**                                    | ❌ exit 1          |
| `clean_observation_reader` fail-closed 对称覆盖（macro + bar） | ❌ bar 侧缺口      |

---

## §维度裁决

**FAIL**

**理由：**（1）独立全量 `uv run pytest -q` exit **1**，不满足 `AUDIT.plan.md` §1 PASS 门槛；（2）`clean_observation_reader` bar 路径 fail-closed / forbidden-source 分支无直接 pytest，S00「禁止 silent 换源」对称性未证尽。

---

## 计划内问题

| ID        | P   | 标题                        | 锚点                                                               | 根因                                                                                                      | 修复方案                                                                                                                                                                          | 验证                                                              |
| --------- | --- | --------------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| A8-P0-001 | P0  | 全量 pytest 非绿            | `AUDIT.plan.md` §1 PASS 门槛 · `AUDIT.plan.md` §2 A8               | `test_qmd_data_sync_baostock` / `test_qmd_data_sync_mootdx` operator 双闸断言与当前 CLI 路由/鉴权行为漂移 | 主会话或 R3F-CLI 票：对齐 `sync_baostock_incremental` / `sync_mootdx_incremental` 与测试期望（恢复 operator gate 或更新测试 match 与前置路由 fixture）                            | `uv run pytest -q --basetemp=.audit-sandbox/pytest` exit 0        |
| A8-P2-001 | P2  | bar 空库未 fail-closed 单测 | `to-issues-slices.md` S00 · `clean_observation_reader.py` L186–189 | S00 仅测 macro 空库；`read_bar_history` 空 `security_bar_1d` 无 RED 证据                                  | 在 `test_layer1_clean_reader.py` 增 `test_layer1CleanReader_emptyBar_failClosedNoFallback`：`bootstrap_layer1_clean_db` 后不 seed bar，`pytest.raises(CleanObservationReadError)` | `uv run python -m pytest tests/test_layer1_clean_reader.py -q` 绿 |
| A8-P2-002 | P2  | bar forbidden source 未测   | `clean_observation_reader.py` L16 · L193–196 · ADR-029 no-fallback | `seed_spy_bars(..., source_used="staged_fixture")` 或 `macro_supplementary` 路径无断言                    | 增 `test_layer1CleanReader_rejectsStagedFixtureBarSource`（及可选 `macro_supplementary` 变体）                                                                                    | 同上                                                              |

---

## 计划外发现

| ID        | P   | 标题                                 | 锚点                                         | 根因                                                                              | 修复方案                                                            | 验证                                       |
| --------- | --- | ------------------------------------ | -------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------ |
| A8-P3-001 | P3  | Amihud 全无效 bar 未 fail-closed     | `clean_observation_reader.py` L252–255       | `amihud_observations_from_bars` 过滤后空序列抛 `CleanObservationReadError` 无单测 | 可选：传入 volume≤0 或单 bar 序列，断言 `CleanObservationReadError` | `tests/test_layer1_clean_reader.py -q`     |
| A8-P3-002 | P3  | S07 全绿证据与当前全量 pytest 不一致 | `research/execute-evidence/s07-green.txt` L5 | 证据文件声称全量 exit 0；A8 复跑 exit 1（CLI 双测回归）                           | Repair/主会话更新 evidence 或先修 A8-P0-001 后重跑落盘              | `uv run pytest -q` exit 0 与 evidence 对齐 |

已对抗搜索：`backend/app/layer1_axes/clean_observation_reader.py` 全公开 API · `tests/test_layer1_*clean*.py` · `tests/layer1_clean_e2e_support.py` · `tests/test_catalog.yaml` DCP-06 条目 · 全库 `rg` bar empty / staged_fixture bar 路径。

---

## 附录 — pytest exit code

```text
uv run pytest -q --basetemp=.audit-sandbox/pytest
EXIT_CODE=1
FAILED: test_qmdData_syncBaostock_operatorAuthRequired
FAILED: test_qmdData_syncMootdx_operatorAuthRequired
```

```text
uv run python scripts/loop_maintain.py
EXIT_CODE=0
```
