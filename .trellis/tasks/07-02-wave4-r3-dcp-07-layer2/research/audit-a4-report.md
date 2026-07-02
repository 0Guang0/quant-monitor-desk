# Audit A4 Report — L2-VIX Clean E2E Assertability / Code Quality

## 元信息

| 字段                  | 值                                      |
| --------------------- | --------------------------------------- |
| 维                    | A4                                      |
| 任务                  | 07-02-wave4-r3-dcp-07-layer2            |
| plan_protocol_version | 4.1                                     |
| 模板                  | `agents/code-reviewer.md`               |
| 日期                  | 2026-07-02                              |
| 审计员                | A4 subagent（独立复验）                 |
| 工作目录              | `quant-monitor-desk-wt-dcp07`           |

---

## 维度证据

### 范围与权威

| 来源                                    | 用途                                                         |
| --------------------------------------- | ------------------------------------------------------------ |
| `AUDIT.plan.md` §2 A4                   | L2 clean e2e 可断言                                          |
| `research/to-issues-slices.md` S00–S01  | reader 契约 + VIX snapshot/lineage AC                        |
| `research/00-EXECUTION-ENTRY.md` §2     | ADR-032 · no EasyXT fallback · replay 隔离                   |
| `docs/decisions/ADR-032-dcp07-layer2-vix-clean-read.md` | P0 锚点 L2-VIX / VIXCLS / axis_observation      |
| `agents/audit-adversarial-authority.md` | 计划未写的 fail-closed 分支、脆弱断言                        |
| DCP-06 `test_layer1_clean_reader.py`    | Layer1 对称 guard 测试先例（source_switched / macro_supplementary / as_of_end） |

### 审查 diff 范围

| 类别     | 路径 |
| -------- | ---- |
| 新增     | `backend/app/layer2_sensors/clean_observation_reader.py` |
| 新增     | `tests/test_layer2_clean_reader.py` · `tests/test_layer2_vix_clean_e2e.py` |
| 新增     | `tests/fixtures/layer2_cross_asset_registry_clean_replay.yaml` |
| 修改     | `sensor_loader.py` · `observation.py` · `snapshot_builder.py` · `__init__.py` |

### 独立 pytest（A4 核心范围）

```text
uv run pytest \
  tests/test_layer2_clean_reader.py \
  tests/test_layer2_vix_clean_e2e.py \
  tests/test_layer2_sensor_loader.py \
  -q
```

| 项        | 结果  |
| --------- | ----- |
| exit code | **0** |
| collected | 43    |
| passed    | 43    |
| failed    | 0     |

（`test_layer2_clean_reader.py` 5 · `test_layer2_vix_clean_e2e.py` 1 · `test_layer2_sensor_loader.py` 37）

### §3.4 多轴审查表

| 轴           | 发现摘要                                                                                         | 证据                                                                 |
| ------------ | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| 正确性       | L2-VIX clean 主路径可读、可建 snapshot、lineage fetch/hash 与 VR 一致；主 AC 成立                | `test_layer2_vix_clean_e2e.py:69-155` · 43/43 pytest 绿              |
| 可读性       | 新增 6 个 `test_*` 均含五字段中文 docstring；reader 模块 ponytail 注释清晰                       | `test_layer2_clean_reader.py` · `test_layer2_vix_clean_e2e.py`       |
| 架构         | clean reader 与 staged 路径并行；registry `production_clean_replay` 仅 P0 白名单                 | ADR-032 · `sensor_loader.py:78-88,213-217`                           |
| 安全（局部） | reader 层 staged_fixture 拒绝有测；`source_switched` / `macro_supplementary` / 非 fred 源无对称测 | `clean_observation_reader.py:13,51-80` · `test_layer2_clean_reader.py:71-90` |
| 错误处理     | 空库 fail-closed（`Layer2CleanObservationReadError`）；fallback guard 实现完整但覆盖不均           | `test_layer2CleanReader_emptyMacro_failClosedNoFallback`             |
| 测试质量     | S01 e2e 断言强度足够（source、lineage、DB 行、quality_flags）；S00 guard 分支薄于 Layer1 先例     | 见 §计划内问题                                                       |
| 可维护性     | `P0_CLEAN_REPLAY_ASSET_IDS` 双文件镜像；loader 负向 fred 白名单无测                              | `sensor_loader.py:27` · `clean_observation_reader.py:15`           |

### S01 AC 对照（to-issues）

| AC 项                                         | 状态 | 证据 |
| --------------------------------------------- | ---- | ---- |
| 非 `staged_fixture_only` registry mode        | ✓    | `layer2_cross_asset_registry_clean_replay.yaml:2` · `test_layer2CleanReplayRegistry_loadsP0VixPrimaryFred` |
| `source_fetch_id` + `content_hash` 可断言     | ✓    | `test_layer2_vix_clean_e2e.py:126-127,153-154` |
| 对齐 `test_layer2Snapshot_lineageIncludesFetchIdsAndHashes` 契约 | ✓ | DB `axis_snapshot_lineage` JSON 与 VR 一致 |
| replay tmp_path 隔离                          | ✓    | `bootstrap_layer1_clean_db(tmp_path)` |

### DOUBT 对抗搜索声明

已搜索：`clean_observation_reader.py` 全部分支、`observation.py::assert_observation_source`、`sensor_loader.py` P0 白名单、`test_layer2_clean_reader.py` / `test_layer2_vix_clean_e2e.py` 全测、对照 `test_layer1_clean_reader.py` 对称 guard 用例、`test_layer2_sensor_loader.py` registry 负向测。重点：no-fallback 分支测试对称性、builder 层 fred 绑定、registry fred 白名单负向、as_of_end 过滤、常量漂移。

---

## §维度裁决

**FAIL**

（§计划内 + §计划外 findings 表均含非占位行 → 按 `audit-finding-schema.md` 强制 FAIL）

**pytest exit code（A4 范围）：0**

---

## 计划内问题

| ID        | P   | 标题                                                       | 锚点                                                                                      | 根因                                                                                                                                                          | 修复方案                                                                                                                                                                                                 | 验证                                                                                                      |
| --------- | --- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| A4-P2-001 | P2  | `source_switched=True` clean 行无 Layer2 reader 单测       | `clean_observation_reader.py:78-80`；`test_layer2_clean_reader.py`（缺对称用例）          | `_row_to_observation` 已拒绝 `source_switched`，但 Layer1 先例 `test_layer1CleanReader_rejectsSourceSwitchedRow` 未在 L2 复现；回归可 silent 移除守卫        | 种子 VIXCLS fred 行后 `UPDATE axis_observation SET source_switched=TRUE` → `pytest.raises(Layer2CleanObservationFallbackForbiddenError)`                                                                 | `uv run pytest tests/test_layer2_clean_reader.py -q` exit 0                                               |
| A4-P2-002 | P2  | `macro_supplementary` 前缀 forbidden guard 无 L2 单测      | `clean_observation_reader.py:13,51-54`；`test_layer2_clean_reader.py`                     | `FORBIDDEN_FALLBACK_SOURCE_PREFIXES` 含 `macro_supplementary`，仅 `staged_fixture` 有拒绝测；B2.5-O-05 对齐缺口                                              | 种子 `source_used='macro_supplementary:akshare'` → `pytest.raises(Layer2CleanObservationFallbackForbiddenError)`                                                                                         | `uv run pytest tests/test_layer2_clean_reader.py -q` exit 0                                               |
| A4-P2-003 | P2  | 非 fred `source_used` 在 P0 路径无拒绝单测                 | `clean_observation_reader.py:56-58`                                                       | `_assert_clean_source_used` 要求 `source_used==fred`，但无 `akshare` 等错误源负向测；与 S00「no EasyXT fallback」AC 不对称                                    | 种子 VIXCLS `source_used='akshare'` → `pytest.raises(Layer2CleanObservationFallbackForbiddenError)`                                                                                                    | `uv run pytest tests/test_layer2_clean_reader.py -q` exit 0                                               |
| A4-P2-004 | P2  | `assert_observation_source` fred 绑定无 builder 层单测    | `observation.py:85-100`；`snapshot_builder.py:89`                                       | S00 扩展 snapshot builder 调用 `assert_observation_source` 校验 `primary_source=fred`，但无直接测证明 staged_fixture/错误源在 builder 入口被拒                  | 构造 `CrossAssetRegistryEntry(primary_source='fred')` + `CrossAssetObservation(source='staged_fixture')` → `pytest.raises(CrossAssetObservationError)`；可选补 `source='akshare'` 负向                     | `uv run pytest tests/test_layer2_sensor_loader.py -k observation_source -q` exit 0（新测落盘同文件或独立模块） |
| A4-P2-005 | P2  | `production_clean_replay` 下非 L2-VIX 资产 `fred` 白名单无负向测 | `sensor_loader.py:213-217`；`test_layer2_clean_reader.py`                           | loader 已实现「仅 L2-VIX 可 primary_source=fred」，但无 YAML 负向测；plan-doubt-review Q3 可执行 AC 未闭合                                                    | tmp_path YAML：`mode: production_clean_replay` + 非 L2-VIX 资产 `primary_source: fred` → `pytest.raises(CrossAssetRegistryLoadError, match='P0-whitelist')`                                                | `uv run pytest tests/test_layer2_clean_reader.py -q` exit 0                                               |

---

## 计划外发现

| ID        | P   | 标题                                              | 锚点                                           | 根因                                                                                    | 修复方案                                                                                                | 验证                                                                   |
| --------- | --- | ------------------------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| A4-P3-001 | P3  | `as_of_end` publish_timestamp 过滤无 L2 单测      | `clean_observation_reader.py:135-137`          | SQL 含 `publish_timestamp <= ?`，但无「未来 publish 行」负向测；DCP-06 A4 已在 L1 补同类测 | 种子 40 行 + 1 行 `publish_timestamp > AS_OF`；断言读结果 `len==40` 且末行非未来值                       | `uv run pytest tests/test_layer2_clean_reader.py -q` exit 0            |
| A4-P3-002 | P3  | P0 白名单常量在 loader/reader 双份镜像            | `sensor_loader.py:27` · `clean_observation_reader.py:15-19` | `P0_CLEAN_REPLAY_ASSET_IDS` / allowlist 两处手写；一方更新另一方可漂移                    | 单处 SSOT（reader import loader 常量，或共享 `layer2_clean_constants.py`）；加断言两边一致              | `uv run pytest tests/test_layer2_clean_reader.py -q` exit 0            |
| A4-P3-003 | P3  | registry 负向测 docstring 仍写「仅 staged_fixture_only」 | `test_layer2_sensor_loader.py:328-333,1014-1018` | `CrossAssetRegistryLoader` 已支持 `production_clean_replay`，测试目的/验证点文案过时，误导后续审计 | 更新五字段 docstring 为「拒绝 production_live；允许 staged_fixture_only 与 production_clean_replay」      | `uv run pytest tests/test_layer2_sensor_loader.py -q` exit 0           |
| A4-P3-004 | P3  | `P0_ROW_CAPS` 120 与 Layer1 VIXCLS cap 无程序化对账 | `clean_observation_reader.py:21-23`；`test_layer2_clean_reader.py:114-116` | cap 手写镜像 Layer1 `RA.R1.VIXCLS_30D_IMPLIED_VOL: 120`；row_cap 测试仅断言常量自洽，非跨层 SSOT | 在 reader 测中 `assert resolve_read_limit('L2-VIX') == resolve_read_limit('RA.R1.VIXCLS_30D_IMPLIED_VOL')`（import L1 helper）或文档化 ponytail 对账注释 + 显式相等断言 | `uv run pytest tests/test_layer2_clean_reader.py::test_layer2CleanReader_respectsRowCap -q` exit 0 |

已对抗搜索：`clean_observation_reader` fail-closed 全分支、Layer1 对称 guard 用例、builder `assert_observation_source`、registry P0 fred 白名单负向、as_of_end 时间窗、常量双份镜像、stale docstring。

---

## 做得好的地方

- **S01 主路径扎实**：`test_layer2_vix_clean_e2e` 从 `axis_observation` 读入 → builder → WM 写入 → DB lineage 与 VR 三方对账，满足 ADR-032 与活卡 lineage AC。
- **S00 核心契约覆盖**：空库 fail-closed、staged_fixture 拒绝、row_cap、registry `production_clean_replay` 正向加载均有独立证明。
- **五字段 docstring**：新增 6 个 `test_*` 符合 `testing-guidelines` §9.1。
- **ponytail 边界清晰**：reader 模块注释标明 macro index OHLC 折叠与升级路径；fetch_time clamp 有注释。
- **并行路径不破坏 staged**：默认 `STAGED_REGISTRY_FIXTURE` 与既有 37 个 loader 测仍全绿。

---

## Verification Story

A4 独立复验命令：

```bash
cd quant-monitor-desk-wt-dcp07
uv run pytest tests/test_layer2_clean_reader.py tests/test_layer2_vix_clean_e2e.py tests/test_layer2_sensor_loader.py -q
```

预期：exit 0（当前已满足）；Repair 须在上表各「验证」列扩展/新增测后仍 exit 0。
