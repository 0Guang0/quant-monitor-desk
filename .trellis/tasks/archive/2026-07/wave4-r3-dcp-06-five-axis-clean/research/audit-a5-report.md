# Audit A5 — AC 完成度 / L1 台账 / 独立复验

| 字段     | 值                                                          |
| -------- | ----------------------------------------------------------- |
| 维度     | A5（audit-completion）                                      |
| 任务     | `wave4-r3-dcp-06-five-axis-clean`                           |
| 协议     | `plan_protocol_version: 4.1`                                |
| 分支     | `feature/wave4-r3-dcp-06-five-axis-clean`                   |
| 审计日期 | 2026-07-02                                                  |
| 权威     | 代码 + 独立 pytest（不信文档 `[x]` / `s07-green.txt` 自述） |

---

## 维度证据

### 独立复验（必做）

| 命令                                                                                                    | 第 1 次 exit | 第 2 次 exit | 备注                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------- | -----------: | -----------: | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `uv run pytest -q`                                                                                      |        **1** |        **0** | 第 1 次 FAIL：`test_loop_engineering_flow.py::test_taskEvidence_checkScript_passesOnSampleTask`（`missing context_pack.json`）；第 2 次全绿 |
| `uv run pytest tests/test_layer1_five_axis_panel_clean_smoke.py tests/test_model_input_whitelist.py -q` |        **0** |            — | 30 passed                                                                                                                                   |
| `uv run pytest tests/test_layer1_clean_reader.py tests/test_layer1_*_clean_e2e.py -q`                   |        **0** |            — | 11 passed（S00 + S01–S05）                                                                                                                  |

**根因（全量 flake）：** `test_contextRouter_cli_taskFlag_writesContextPack` 在 `finally` 前 `unlink` 归档任务 `context_pack.json`，依赖 `git checkout` 恢复；与 `test_taskEvidence_checkScript_passesOnSampleTask` 同文件、同 `SAMPLE_TASK` 路径，存在**测试顺序污染**（plan 外 loop 工程，非 DCP-06 实现）。

### AC 评分表（1–5 rubric）

| #     | 范围                                                      |    分 | 追溯链（代码 / 测试）                                                                                                                                                                                                                                                                                                                           | 缺口                                                                                                                                                                                                            |
| ----- | --------------------------------------------------------- | ----: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | **Main DCP-06 S00–S06 交付物**                            | **4** | S00：`backend/app/layer1_axes/clean_observation_reader.py` + `tests/test_layer1_clean_reader.py`（6 测）；S01–S05：五模块 `test_layer1_{environment,credit_stress,risk_appetite,liquidity,sentiment}_clean_e2e.py` 各 1 测全绿；S06：`tests/test_layer1_five_axis_panel_clean_smoke.py`（5 测）+ `audit-repair-ledger-s07.md` 13/13 关账        | 活卡 §5 / ENTRY 完成条件要求 `uv run pytest -q` exit 0：**第 1 次独立全量复验 exit 1**（flake）；第 2 次 exit 0。DCP-06 切片本身闭环，全量门禁边界弱                                                            |
| **2** | **K2 / FR-4 五轴 clean→feature→interpretation**           | **5** | 每轴 e2e：`read_macro_clean_observations` / `read_bar_history` + `amihud_observations_from_bars` → `AxisFeatureEngine` → `AxisInterpretationEngine`；panel smoke 断言 4 macro + 1 bar 均 `state_bucket != insufficient_history` 且 `boundary_reminder == "不构成交易动作"`（含 LIQ `liq_interp`，S07 repair #1）                                | —                                                                                                                                                                                                               |
| **3** | **K1 / FR-6 `clean_replay_proven` whitelist**             | **5** | `specs/model_inputs/layer1_source_whitelist.yaml`：DGS10/BAA10Y/VIXCLS/SPY/088691 → `readiness: clean_replay_proven` + `row_cap`/`window_cap`；`docs/quality/model_input_readiness_matrix.md` legend + 5 行；`tests/test_model_input_whitelist.py::test_layer1_p0_dcp06_cleanReplayProven`；panel `test_dcp06K1_whitelistAlignsP0CleanBindings` | —                                                                                                                                                                                                               |
| **4** | **A4 / FR-5 ResourceGuard + caps（smoke 路径）**          | **4** | `P0_ROW_CAPS` / `P0_WINDOW_CAPS` + `resolve_window_cap`（`clean_observation_reader.py`）；`test_layer1CleanReader_macroRespectsWhitelistRowCap` / `barHistoryRespectsWhitelistRowCap`；`test_layer1FiveAxisPanel_resourceGuardOnMigratedDb` 真 `ResourceGuard(con).check()`；`test_layer1FiveAxisPanel_windowLenWithinWhitelistCap`             | `test_layer1FiveAxisPanel_resourceGuardHardStop_blocksFeatureCompute` 仍 **MagicMock** HARD_STOP（S07 ledger #5 以真 check 测补位，未删 mock 路径）；caps **ponytail 硬编码**镜像 YAML（注释写明 Batch 6 升级） |
| **5** | **L1 `ACC-LAYER-E2E-LIVE-001` 子集关账 + L3–L5 阶段外置** | **5** | `待修复清单.md` §4：`ACC-LAYER-E2E-LIVE-001` L1 子集已通、L3–L5 open → DCP-07/08/10 + R3H-05-GATE；`PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.1 五轴清单全 `[x]`、§3.5.2 DCP-06 行「L1 五轴 clean replay 子集」；`R3_DCP_TO_ISSUES_INDEX.md` §6.2 L1 ✅ + L3–L5 阶段外置；`audit-repair-ledger-s07.md` #11–12 **阶段外置** 已绑任务 ID            | L3–L5 全链 **刻意 open**（符合 ENTRY「不在范围」），非本票 AC 缺口                                                                                                                                              |

### S00–S06 切片 ↔ 证据对照

| 切片    | 实现锚点                                                            | 测试 / 证据                                                  |
| ------- | ------------------------------------------------------------------- | ------------------------------------------------------------ |
| S00     | `clean_observation_reader.py`；`FORBIDDEN_FALLBACK_SOURCE_PREFIXES` | `test_layer1_clean_reader.py`（6）                           |
| S01 ENV | macro read DGS10                                                    | `test_layer1_environment_clean_e2e.py`                       |
| S02 CRD | BAA10Y                                                              | `test_layer1_credit_stress_clean_e2e.py`                     |
| S03 RA  | VIXCLS                                                              | `test_layer1_risk_appetite_clean_e2e.py`                     |
| S04 LIQ | Amihud from SPY bars（ADR-029 ponytail）                            | `test_layer1_liquidity_clean_e2e.py`                         |
| S05 SEN | COT 088691                                                          | `test_layer1_sentiment_clean_e2e.py`                         |
| S06     | panel + K1 + A4 + 台账                                              | `test_layer1_five_axis_panel_clean_smoke.py` + registry 三处 |

### S07 Repair ledger 独立核对

`research/audit-repair-ledger-s07.md` 13 项：11 **已修复**、2 **阶段外置**（#11 L3–L5、#12 tiingo）。代码/测试抽查与 ledger 声明一致；**不得**因 `s07-green.txt` 声称全绿而跳过复跑（本报告已独立复验）。

### 文档 vs 代码偏差

| 文档声称                                                                 | 独立复验                           |
| ------------------------------------------------------------------------ | ---------------------------------- |
| 活卡 `R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md` §5：`uv run pytest -q` exit 0 | 第 1 次 **exit 1**；第 2 次 exit 0 |
| `execute-evidence/s07-green.txt`：Full suite exit 0                      | 与本审计第 2 次一致；第 1 次不一致 |

---

## §维度裁决

**FAIL**

**理由：** §计划外发现 含 ≥1 行非占位 finding（全量 pytest 顺序依赖 flake，阻塞「一次复验即绿」的 ENTRY/活卡硬门禁语义）。DCP-06 五轴功能 AC（表 #2–#5）追溯链完整且定向 pytest 全绿；表 #1 因全量 flake 扣至 4 分。

---

## 计划内问题

| ID        | P   | 标题                                    | 锚点                                                                 | 根因                                                                                 | 修复方案                                                                                                                                                   | 验证                                |
| --------- | --- | --------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| A5-P2-001 | P2  | 活卡/ENTRY 全量 pytest 一次复验未稳定绿 | `R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md` §5；`00-EXECUTION-ENTRY.md` §3 | 完成条件绑定 `uv run pytest -q` exit 0；独立第 1 次跑测 FAIL（虽非 DCP-06 切片根因） | Repair 或 loop 维护：修复 `test_loop_engineering_flow.py` 对 `SAMPLE_TASK/context_pack.json` 的隔离（见计划外 #A5-P2-002）；复验全绿后再勾活卡 §5 最后一项 | `uv run pytest -q` 连续 2 次 exit 0 |

---

## 计划外发现

| ID        | P   | 标题                               | 锚点                                                       | 根因                                                                                                                                                            | 修复方案                                                                                                     | 验证                                                                                                              |
| --------- | --- | ---------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| A5-P2-002 | P2  | loop 测试污染归档任务 context_pack | `tests/test_loop_engineering_flow.py` L171–206 vs L402–415 | `test_contextRouter_cli_taskFlag_writesContextPack` unlink pack 后 `git checkout` 恢复；并行/顺序下 `test_taskEvidence_checkScript_passesOnSampleTask` 可见缺失 | 改为 `tmp_path` 副本任务目录，或 `monkeypatch` + 不触碰归档树；禁止 mutating `archive/.../context_pack.json` | `uv run pytest tests/test_loop_engineering_flow.py -q` 连续 2 次 exit 0；全量 `uv run pytest -q` 连续 2 次 exit 0 |

已对抗搜索：`tests/test_loop_engineering_flow.py` · `scripts/check_task_evidence.py` · DCP-06 `test_layer1_*` 全模块 · `待修复清单.md` §4 · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.1/§3.5.2 · `R3_DCP_TO_ISSUES_INDEX.md` §6.2 · `layer1_source_whitelist.yaml` · `audit-repair-ledger-s07.md`。

---

## pytest exit codes（摘要）

```
uv run pytest -q                          → run1: 1  run2: 0
uv run pytest tests/test_layer1_five_axis_panel_clean_smoke.py \
            tests/test_model_input_whitelist.py -q  → 0
uv run pytest tests/test_layer1_clean_reader.py \
            tests/test_layer1_*_clean_e2e.py -q     → 0
```
