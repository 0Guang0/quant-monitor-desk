# Audit A3 — Security（R3-DCP-07 Layer2 cross-asset clean read）

> **维：** A3 · **任务：** 07-02-wave4-r3-dcp-07-layer2 · **协议：** v4.1  
> **日期：** 2026-07-02 · **Diff：** worktree 未提交变更（`backend/app/layer2_sensors/*` + 新增 `clean_observation_reader.py` + `tests/test_layer2_*`）  
> **模板：** `agents/security-auditor.md` · **权威：** `agents/audit-adversarial-authority.md` · `reference-adoption-dcp07.md` · ADR-032 · AUDIT.plan §2 A3

---

## 维度证据 §3.3

### 范围与命令

| 动作                                                                               | 证据                                                                                                                                                                                 |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | ------------------------------------- | --------------------------------- |
| `rg 参考项目 backend/app/layer2_sensors/`                                          | **0 命中**                                                                                                                                                                           |
| `rg "import.*参考\|sys\.path.*参考\|unified_data" backend/app/layer2_sensors/`     | **0 命中**                                                                                                                                                                           |
| `rg "https?://\|api[_-]?key\|secret\|token\|password" backend/app/layer2_sensors/` | **0 命中**（变更面）                                                                                                                                                                 |
| `rg "subprocess\|os\.system\|eval(\|exec(" backend/app/layer2_sensors/`            | **0 命中**                                                                                                                                                                           |
| `rg "requests\.                                                                    | httpx\.                                                                                                                                                                              | urllib\. | aiohttp" backend/app/layer2_sensors/` | **0 命中**（无 live HTTP 读路径） |
| `FORBIDDEN_FALLBACK` / `Layer2CleanObservationFallbackForbiddenError`              | `clean_observation_reader.py:13,30-31,51-59,78-80`                                                                                                                                   |
| P0 正源 allowlist                                                                  | `P0_ALLOWED_SOURCE_BY_ASSET` @ `clean_observation_reader.py:17-19`；`_assert_clean_source_used` @ L51-59                                                                             |
| `source_switched` fail-closed                                                      | `clean_observation_reader.py:78-80` → `Layer2CleanObservationFallbackForbiddenError`                                                                                                 |
| fail-closed 空 clean                                                               | `Layer2CleanObservationReadError` @ L141-145                                                                                                                                         |
| SQL 参数化                                                                         | `clean_observation_reader.py:128-140` 全 `?` 绑定；`db_key` 经 `resolve_clean_db_key` 映射后参数化                                                                                   |
| `f"CREATE TABLE {staging} AS SELECT..."`                                           | `sensor_loader.py:168` — `staging` 为 `uuid` 生成表名（仓内既有 WriteManager 模式；非用户输入）                                                                                      |
| tmp_path 隔离                                                                      | `test_layer2_clean_reader.py` / `test_layer2_vix_clean_e2e.py` 均 `bootstrap_layer1_clean_db(tmp_path)`                                                                              |
| GitNexus `query`（repo=quant-monitor-desk）                                        | 2 次：`Layer2CleanObservationReader` / `clean_observation_reader axis_observation fallback` — **新符号未索引**（worktree 变更未 analyze；邻域返回 axis_loader / validation_gate 流） |
| GitNexus `context(Layer2CleanObservationReader)`                                   | **Symbol not found**（索引滞后；以 `file:line` + rg 为准）                                                                                                                           |

### 信任边界核对（AUDIT.plan §2 A3 · ENTRY §2 · reference-adoption-dcp07 §0）

| 威胁面                                       | 核对                                                                                                                      | 结论                                 |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| 参考项目 runtime import                      | `backend/app/layer2_sensors/**` 零 import；`reference_adoption_guardrails.yaml` `no_runtime_reference_project_dependency` | **PASS**                             |
| EasyXT DuckDB 空→在线回退                    | `Layer2CleanObservationReader` 无 `DataSourceService` / 网络 fetch；空表 `Layer2CleanObservationReadError`                | **PASS**                             |
| `FORBIDDEN_FALLBACK_SOURCE_PREFIXES`         | `staged_fixture` / `macro_supplementary` 前缀拒绝 @ `_row_to_observation` L52-55                                          | **PASS**（代码）                     |
| P0 正源 allowlist（L2-VIX=fred）             | `_assert_clean_source_used` 精确匹配 `fred`；`akshare` 等非绑定源 → `Layer2CleanObservationFallbackForbiddenError`        | **PASS**（优于 DCP-06 仅前缀黑名单） |
| `source_switched=True`                       | L78-80 fail-closed                                                                                                        | **PASS**（代码）                     |
| registry `production_clean_replay` 误开 live | mode 白名单 + `fred` 仅 `P0_CLEAN_REPLAY_ASSET_IDS`（L213-217）；plan-doubt-review Q3 已 reconcile                        | **PASS**（P0 竖切）                  |
| clean 读路径写库                             | `clean_observation_reader.py` **无** writer / INSERT                                                                      | **PASS**                             |
| e2e 写路径                                   | `test_layer2_vix_clean_e2e.py` 经 `Layer2SnapshotWriter` + `validation_report_id` + 独立 `tmp_path` WM DB                 | **PASS**（授权测试写）               |
| lineage 溯源标签与真实读路径一致             | clean e2e 读 `axis_observation`/fred，但 lineage `source_dataset_ids` 仍硬编码 `staged:cross_asset_observation:*`         | **FAIL**（见计划外）                 |
| 密钥 / 硬编码 token                          | 变更面无新增                                                                                                              | **PASS**                             |

### DOUBT 三类对抗搜索

| 类                 | 范围                                                                                                                                                                                      | 结论                                                                |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 硬编码 URL 变体    | `backend/app/layer2_sensors/clean_observation_reader.py` · `sensor_loader.py` · `observation.py` · `tests/test_layer2_*` · `tests/fixtures/layer2_cross_asset_registry_clean_replay.yaml` | **无发现**                                                          |
| JWT / API key 模式 | 同上 + `rg` 全 layer2_sensors 包                                                                                                                                                          | **无发现**                                                          |
| SQL 拼接           | `clean_observation_reader.py` 读路径参数化；staging DDL 仅 uuid 表名（pre-existing 模式）                                                                                                 | **无发现**（读路径）；staging f-string 为仓内既定 WriteManager 模式 |

### §3.3 威胁摘要

| 威胁                                                  | 发现                                 | P   | 证据                                                                                     |
| ----------------------------------------------------- | ------------------------------------ | --- | ---------------------------------------------------------------------------------------- |
| 参考项目 runtime 渗入                                 | 无                                   | —   | backend layer2_sensors 0 命中                                                            |
| EasyXT 式 silent fallback（空 clean）                 | 有负向测                             | —   | `test_layer2CleanReader_emptyMacro_failClosedNoFallback`                                 |
| staged_fixture 混入 P0 clean 读                       | 有负向测                             | —   | `test_layer2CleanReader_rejectsStagedFixtureSourceUsed`                                  |
| 非 Tier A 源（akshare 等）混入 P0 clean 读            | 无（allowlist 拒）                   | —   | `P0_ALLOWED_SOURCE_BY_ASSET` + `_assert_clean_source_used`                               |
| `source_switched` / `macro_supplementary` 负向 pytest | **有**（guard 在代码、无 L2 对称测） | P3  | `clean_observation_reader.py:52-55,78-80`；对比 `test_layer1_clean_reader.py` 已有对称测 |
| clean replay lineage 溯源标签仍为 staged              | **有**                               | P2  | `snapshot_builder.py:134` + e2e 未断言 `source_dataset_ids`                              |
| 生产库测试污染                                        | 无                                   | —   | 全 `tmp_path`                                                                            |
| live 源默认开启                                       | 无                                   | —   | 变更面无 qmt/xqshare enable                                                              |

### 正向观察

- 新模块 `Layer2CleanObservationReader` 与 `参考项目/**`、`DataSourceService` 零耦合，符合 `reference-adoption-dcp07.md` §0 铁律与 ENTRY §2「禁止 EasyXT fallback」。
- 相对 DCP-06 初版，Layer2 clean reader 已引入 **P0 正源 allowlist**（`fred`）与 **`source_switched` fail-closed**，读路径 SQL 全参数化，`P0_ROW_CAPS` 有界（120）。
- `assert_observation_source` 在 snapshot 构建阶段阻断 `primary_source=fred` 资产使用 `staged_fixture` 观测（`observation.py:91-100`）。
- Registry loader 对 `production_clean_replay` + `primary_source=fred` 限制为 `L2-VIX` 白名单（`sensor_loader.py:213-217`）。

---

## §维度裁决

**FAIL**

（§计划内占位 + §计划外 2 行非占位 finding）

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

AUDIT.plan §2 A3 要点（无参考项目 runtime · no fallback）在 **P0 L2-VIX 读路径** 静态核对通过：`Layer2CleanObservationReader` fail-closed、无参考 import、无在线旁路。

---

## 计划外发现

| ID        | P   | 标题                                                                                                                       | 锚点                                                                                                       | 根因                                                                                                                                   | 修复方案                                                                                                                                                                                          | 验证                                                                                                                             |
| --------- | --- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| A3-P2-001 | P2  | clean replay e2e 写入 lineage 时 `source_dataset_ids` 仍标 `staged:cross_asset_observation`，与 Tier A fred clean 读不一致 | `snapshot_builder.py:134` · `test_layer2_vix_clean_e2e.py:114-127`（断言 fetch/hash 但未断言 dataset_ids） | `CrossAssetSnapshotBuilder.build_daily_snapshots` 硬编码 staged 标签；DCP-07 复用 builder 未按 `primary_source`/读路径区分溯源         | 按 registry `primary_source` 或调用方传入 `source_dataset_ids`（如 `fred:axis_observation:VIXCLS` 或 `clean:axis_observation:L2-VIX`）；e2e 增加 `lineage.source_dataset_ids` 断言                | `uv run pytest tests/test_layer2_vix_clean_e2e.py -q`；读 DB `axis_snapshot_lineage` 行 `source_dataset_ids` 不含 `staged:` 前缀 |
| A3-P3-001 | P3  | Layer2 clean reader 对 `source_switched` / `macro_supplementary` 有 guard 但无对称负向 pytest                              | `clean_observation_reader.py:52-55,78-80` · `tests/test_layer2_clean_reader.py`（缺对应用例）              | S00 仅测 `staged_fixture` 与空表；未镜像 DCP-06 `test_layer1_clean_reader.py` 对 `source_switched` / `macro_supplementary` 的 RED 证明 | 新增 `test_layer2CleanReader_rejectsSourceSwitched`（UPDATE `source_switched=TRUE`）与 `test_layer2CleanReader_rejectsMacroSupplementaryPrefix`（seed `source_used=macro_supplementary:akshare`） | `uv run pytest tests/test_layer2_clean_reader.py -q`                                                                             |

已对抗搜索：`backend/app/layer2_sensors/clean_observation_reader.py` · `sensor_loader.py` · `observation.py` · `snapshot_builder.py` · `tests/test_layer2_clean_reader.py` · `tests/test_layer2_vix_clean_e2e.py` · `tests/fixtures/layer2_cross_asset_registry_clean_replay.yaml` · `reference-adoption-dcp07.md` · ADR-032 · `plan-doubt-review.md` Q3/Q5 · GitNexus query×2（索引未含新符号，以 rg/file:line 为准）。
