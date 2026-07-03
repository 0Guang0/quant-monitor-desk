# Audit A3 — Security（R3-DCP-06 Layer1 five-axis clean read）

> **维：** A3 · **任务：** wave4-r3-dcp-06-five-axis-clean · **协议：** v4.1  
> **日期：** 2026-07-02 · **Diff：** `git diff master..HEAD`（S00–S07 + K1/K2/A4/L1 repair）  
> **模板：** `agents/security-auditor.md` · **权威：** `agents/audit-adversarial-authority.md` · `reference-adoption-dcp06.md` · ADR-029

---

## 维度证据 §3.3

### 范围与命令

| 动作                                                                | 证据                                                                                                                                                        |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `rg 参考项目 backend/app/layer1_axes/`                              | **0 命中**                                                                                                                                                  |
| `rg 参考项目` 于 DCP-06 新增/变更测与 `clean_observation_reader.py` | **0 命中**                                                                                                                                                  |
| `rg "import.*参考\|sys\.path.*参考" backend/`                       | **0 命中**                                                                                                                                                  |
| `FORBIDDEN_FALLBACK` / `CleanObservationFallbackForbiddenError`     | `clean_observation_reader.py:16-17,74-99,193-196`                                                                                                           |
| fail-closed 空 clean                                                | `CleanObservationReadError` @ macro L137-140 · bar L186-189 · Amihud L252-255                                                                               |
| tmp_path 隔离                                                       | 全部新增 `test_layer1_*_clean_e2e*` / `test_layer1_clean_reader.py` / panel smoke 均 `bootstrap_layer1_clean_db(tmp_path)` → `tmp_path/layer1_clean.duckdb` |
| SQL 注入面                                                          | `read_macro_clean_observations` / `read_bar_history` 谓词 `?` 绑定；`spec_indicator_id` 经 `P0_MACRO_DB_KEYS` 映射后参数化                                  |
| GitNexus `impact(read_macro_clean_observations)`                    | **符号未索引**（索引 stale；见 `research/gitnexus-summary.md`）                                                                                             |
| GitNexus `query`「Layer1 clean observation reader fallback」        | 未命中 clean reader 流；返回 axis_loader / ingestion 邻域（索引滞后）                                                                                       |
| 静态链：clean reader → DataSourceService / ingestion                | **无 import**；并行读路径与 `Layer1ObservationIngestionService` 解耦（ADR-029 · plan-doubt-review Q3）                                                      |

### 信任边界核对（AUDIT.plan §2 · ENTRY §2 · reference-adoption-dcp06 §0）

| 威胁面                                         | 核对                                                                                                                                 | 结论                         |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------- |
| 参考项目 runtime import                        | `backend/**` 零 import；`reference_adoption_guardrails.yaml` `no_runtime_reference_project_dependency`                               | **PASS**                     |
| EasyXT DuckDB 空→在线回退                      | clean reader 无 `DataSourceService`；空表 `CleanObservationReadError`                                                                | **PASS**（读路径无在线旁路） |
| `FORBIDDEN_FALLBACK_SOURCE_PREFIXES`           | `staged_fixture` / `macro_supplementary` **前缀**拒绝 @ `_row_to_observation` + `read_bar_history`                                   | **部分 FAIL**（见 P1）       |
| macro_supplementary / akshare 替代 FRED        | ingestion 可写 `source_used=akshare`（`test_layer1Observation_stagedFixture_qualityFlagPersisted`）；clean reader **未拒** `akshare` | **FAIL**                     |
| Tier A 正源 allowlist（ADR-029）               | P0 绑定表有 `fred`/`cftc_cot`/`alpha_vantage`；reader **未校验** `source_used` 与绑定一致                                            | **FAIL**                     |
| `source_switched=True`（silent_fallback 信号） | 行原样透传；`feature_engine` 仅加 flag 仍可算特征                                                                                    | **FAIL**（fail-closed 缺口） |
| 测试写生产库                                   | 新增 e2e 均 `tmp_path`；无默认 `quant_monitor.duckdb` 写                                                                             | **PASS**                     |
| 密钥 / 硬编码 token                            | DCP-06 变更面无新增 outbound 密钥                                                                                                    | **PASS**                     |

### DOUBT 三类对抗搜索

| 类                       | 范围                                                                            | 结论                                    |
| ------------------------ | ------------------------------------------------------------------------------- | --------------------------------------- |
| 参考树 runtime 渗入      | `backend/app/layer1_axes/clean_observation_reader.py` · 五轴 e2e · K1/A4 修文件 | 无 import / sys.path                    |
| fallback / 旁路 mutation | clean reader · `ingestion.py`（只读对照）· `layer1_clean_e2e_support.py`        | **akshare** 与 **source_switched** 缺口 |
| SQL / 无界 I/O           | reader SQL · `P0_ROW_CAPS`/`P0_WINDOW_CAPS`                                     | SQL 参数化；cap 有界（A4 已测）         |

### §3.3 威胁摘要

| 威胁                                   | 发现              | P   | 证据                                                    |
| -------------------------------------- | ----------------- | --- | ------------------------------------------------------- |
| 参考项目 runtime 渗入                  | 无                | —   | backend 0 命中                                          |
| staged_fixture 前缀混入 clean 读       | 有负向测（macro） | —   | `test_layer1CleanReader_rejectsStagedFixtureSourceUsed` |
| akshare / 非 Tier A 源混入 P0 clean 读 | **有**            | P1  | reader 仅前缀黑名单；ingestion 写 `source_used=akshare` |
| source_switched 行进入 clean 读        | **有**            | P2  | `read_macro_clean_observations` L161 透传               |
| Amihud 构造绕过 forbidden guard        | **有**            | P3  | `amihud_observations_from_bars` 直建 `AxisObservation`  |
| bar 路径 staged_fixture 负向测缺失     | **有**            | P3  | `read_bar_history` 有 guard，无对称 pytest              |
| 生产库测试污染                         | 无                | —   | 全 `tmp_path`                                           |

### 正向观察

- 新模块 `clean_observation_reader.py` 与 `DataSourceService` / `参考项目/**` 零耦合，符合 reference-adoption-dcp06 §0 铁律。
- 空 `axis_observation` / `security_bar_1d` **fail-closed**（`CleanObservationReadError`），不返回空列表、不触发在线 fetch。
- `staged_fixture` 前缀在 macro 路径有 **RED 负向测**；SQL 全参数化。
- K1 repair：`layer1_source_whitelist.yaml` P0 五行 `clean_replay_proven` + cap；`test_layer1_p0_dcp06_cleanReplayProven` 与 panel K1 对齐测存在。
- S07 repair：`test_layer1FiveAxisPanel_resourceGuardOnMigratedDb` 真 `ResourceGuard(con).check()`（A4 范围，但降低五轴路径资源旁路风险）。

---

## §维度裁决

**FAIL**

（§计划内 2 行 + §计划外 2 行非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                                                                              | 锚点                                                                                                                                                  | 根因                                                                                                                                                                                                                                               | 修复方案                                                                                                                                                                                                    | 验证                                                                                                                                                        |
| --------- | --- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A3-P1-001 | P1  | clean macro 读仅拒 `staged_fixture`/`macro_supplementary` 前缀，**接受 `akshare` 等非 Tier A 源** | `backend/app/layer1_axes/clean_observation_reader.py:96-99,153-164` · `tests/test_layer1_clean_reader.py:57-75` · ADR-029 tier_a_source 表            | `FORBIDDEN_FALLBACK_SOURCE_PREFIXES` 为前缀黑名单；ingestion staged 路径持久化 `source_used=akshare`（`test_layer1Observation_stagedFixture_qualityFlagPersisted` L1529-1550），与 macro_supplementary 实际 source_id 不一致；无 P0 正源 allowlist | 在 `_row_to_observation` 增加 **P0 正源 allowlist**（macro：`fred`/`cftc_cot` 按 `P0_MACRO_DB_KEYS`；bar：`alpha_vantage`）或扩展 forbidden 含 `akshare`；不匹配 → `CleanObservationFallbackForbiddenError` | 新增 `test_layer1CleanReader_rejectsAkshareSourceUsed`（seed DGS10 + `source_used=akshare` → raises）；`uv run pytest tests/test_layer1_clean_reader.py -q` |
| A3-P2-001 | P2  | `source_switched=True` 的 clean 行未 fail-closed                                                  | `clean_observation_reader.py:127-162` · `reference_adoption_guardrails.yaml` `silent_fallback` · `to-issues-slices.md` S00「禁止 EasyXT 式 fallback」 | reader 透传 `source_switched`；`feature_engine` 仅加 `SOURCE_SWITCHED` flag 仍产出特征，违背 clean 读边界 fail-closed                                                                                                                              | macro/bar 读路径：`source_switched is True` → `CleanObservationFallbackForbiddenError`（或专用 `CleanObservationSwitchedSourceError`）                                                                      | 新增负向测：seed 行 `source_switched=True` + `source_used=fred` → pytest.raises；`uv run pytest tests/test_layer1_clean_reader.py -q`                       |

---

## 计划外发现

| ID        | P   | 标题                                                           | 锚点                                                                        | 根因                                                                                                                                         | 修复方案                                                                                                                                                     | 验证                                                                                                                                                               |
| --------- | --- | -------------------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A3-P3-001 | P3  | `amihud_observations_from_bars` 构造观测时跳过 forbidden guard | `clean_observation_reader.py:242-249`                                       | 直建 `AxisObservation`，未复用 `_row_to_observation`；若调用方绕过 `read_bar_history` 传入 `source_used=staged_fixture` 字典，可渗入流动性轴 | 提取共享 `_assert_clean_source_used(source_used)` 并在 Amihud 分支调用；或强制仅接受经 `read_bar_history` 的 bar 类型                                        | 负向：`amihud_observations_from_bars([{"trade_date":...,"source_used":"staged_fixture",...}], ...)` → raises；`uv run pytest tests/test_layer1_clean_reader.py -q` |
| A3-P3-002 | P3  | bar clean 读 `staged_fixture` 拒绝无对称 pytest                | `clean_observation_reader.py:192-196` · `tests/test_layer1_clean_reader.py` | macro 有 `test_layer1CleanReader_rejectsStagedFixtureSourceUsed`；bar 路径 guard 已实现但无 RED 证明，回归可静默删除 guard                   | 新增 `test_layer1CleanReader_rejectsStagedFixtureBarSource`：`seed_spy_bars(..., source_used="staged_fixture")` 或 UPDATE bar 行 → `read_bar_history` raises | `uv run pytest tests/test_layer1_clean_reader.py::test_layer1CleanReader_rejectsStagedFixtureBarSource -q`                                                         |

已对抗搜索：`backend/app/layer1_axes/clean_observation_reader.py` · `tests/layer1_clean_e2e_support.py` · `tests/test_layer1_clean_reader.py` · `tests/test_layer1_five_axis_panel_clean_smoke.py` · 五轴 `test_layer1_*_clean_e2e.py` · `tests/test_model_input_whitelist.py`（K1）· `specs/model_inputs/layer1_source_whitelist.yaml` · `tests/test_layer1_observation_ingestion.py`（akshare staged 对照）· `reference-adoption-dcp06.md` · ADR-029 · GitNexus impact/query（索引 stale）。
