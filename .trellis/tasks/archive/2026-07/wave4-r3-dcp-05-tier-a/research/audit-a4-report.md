# Audit A4 — 代码质量 / e2e clean 断言

| 字段                  | 值                             |
| --------------------- | ------------------------------ |
| 维度                  | A4（audit-quality）            |
| 任务                  | wave4-r3-dcp-05-tier-a         |
| 分支                  | feature/wave4-r3-dcp-05-tier-a |
| plan_protocol_version | 4.1                            |
| 日期                  | 2026-07-02                     |
| 模板                  | `agents/code-reviewer.md`      |

---

## 维度证据

### A4 对抗动作（`audit-adversarial-authority.md`）

- 已对照 ENTRY/`to-issues-slices.md` AC、ADR-028 clean 矩阵、`AUDIT.plan` §2 A4 要点。
- 已 Glob `tests/test_*incremental*` / `test_*e2e*`，逐源阅读 replay e2e 断言。
- 已 `git diff master...HEAD -- backend/app/ops backend/app/sync`（+ CLI 路由触点）。
- 验证基于代码/测试阅读；本维未独立 `pytest` 复跑（A5 职责）。

### 11 源 e2e 覆盖矩阵

| source_id     | e2e 模块                                | clean 表                  | 断言 fixture 字段   | 幂等 e2e | EMPTY_RESPONSE e2e |
| ------------- | --------------------------------------- | ------------------------- | ------------------- | -------- | ------------------ |
| baostock      | `test_baostock_incremental_e2e.py`      | `security_bar_1d`         | ✓ close=1405        | ✓        | —                  |
| mootdx        | `test_mootdx_incremental_e2e.py`        | `security_bar_1d`         | ✓ close+source_used | ✓        | —                  |
| fred          | `test_fred_macro_incremental_e2e.py`    | `axis_observation`        | ✗ COUNT≥1           | ✓        | ✓                  |
| us_treasury   | `test_us_treasury_incremental_e2e.py`   | `axis_observation`        | ✗ COUNT≥1           | ✓        | ✓                  |
| bis           | `test_bis_incremental_e2e.py`           | `axis_observation`        | ✗ COUNT≥1           | ✓        | ✓                  |
| world_bank    | `test_world_bank_incremental_e2e.py`    | `axis_observation`        | ✗ COUNT≥1           | ✓        | **✗**              |
| cftc_cot      | `test_cftc_incremental_e2e.py`          | `axis_observation`        | ✗ COUNT≥1           | **✗**    | ✓                  |
| cninfo        | `test_cninfo_incremental_e2e.py`        | `cn_announcement_clean`   | ✓ announcement_id   | ✓        | ✓                  |
| sec_edgar     | `test_sec_edgar_incremental_e2e.py`     | `us_disclosure_clean`     | ✓ accession_number  | ✓        | ✓                  |
| alpha_vantage | `test_alpha_vantage_incremental_e2e.py` | `security_bar_1d`         | ✓ close=186.2       | ✓        | ✓                  |
| deribit       | `test_deribit_incremental_e2e.py`       | `crypto_derivative_clean` | ✓ mark_iv=0.52      | ✓        | ✓                  |

**结论：** 11/11 均有 replay e2e 且均查询 **clean 表**（非 staging 表名）；无 staging-only 实现路径（ops 均 `orch.run_incremental(..., clean_table=target.target_table)`）。但 macro 五源断言偏弱，cftc/world_bank 与同族测试不齐。

### staging vs clean 断言

- 全部 `test_*incremental_e2e.py` **无**对 `stg_*` 表的负向断言（未证明「非 staging 终点」）。
- 实现上 staging 为管线中间态（`macro_incremental_common.py` L256–271 写 `stg_axis_observation_smoke` 后 `run_incremental` promote）；clean 行数增加可间接证明 promote，但无法检出「clean 有数据 + staging 残留脏行」类退化。

### git diff 摘要（`backend/app/ops` + `backend/app/sync`）

- 新增 20 文件，+3064 行：各源 `*_incremental_run.py` / `*_watermark.py`、`macro_incremental_common.py`（共享 macro 金路径）、`incremental_source_registry.py`、`clean_write_targets.py` 扩展 ADR-028 域。
- CLI：`tier_a_sync_router.py`（S12）+ `data_commands.sync_plan` 委派 `--source-id`。

### 五轴审查（关键文件）

| 轴         | 评估                   | 要点                                                                                                                                                                                                        |
| ---------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **正确性** | 良（实现）/ 中（测试） | `run_macro_incremental` / 各 `run_*_incremental` 均 `resolve_clean_write_target` → `clean_table`；registry 与 `TIER_A_SOURCES` 漂移 guard（`incremental_source_registry.py` L34–38）。测试缺口见 findings。 |
| **可读性** | 良                     | `macro_incremental_common` 抽取 macro 重复；源模块命名与 fred 先例一致；`tier_a_sync_router` 按 source 分派清晰。                                                                                           |
| **架构**   | 良（偏 ponytail）      | 金路径统一 `DataSyncOrchestrator.run_incremental`；staging adapter 仅 fetch 阶段。S12 live 路由仅 3/11（见计划外）。                                                                                        |
| **安全**   | 可接受                 | dry-run 默认；非 dry-run 对未接线源 `USER_AUTH_REQUIRED`（`tier_a_sync_router.py` L233–240）。无密钥进 diff。                                                                                               |
| **性能**   | 可接受                 | per-instrument 串行 loop（macro/common L455–499）；Tier A 规模可接受；无 unbounded I/O 新热点。                                                                                                             |

### §3.4 轴表

| 轴     | 发现                                       | 证据                                                                        |
| ------ | ------------------------------------------ | --------------------------------------------------------------------------- |
| 正确性 | macro e2e 脆弱 COUNT 断言；cftc 缺幂等 e2e | `test_cftc_incremental_e2e.py`；`test_fred_macro_incremental_e2e.py` L42–44 |
| 可读性 | —                                          | —                                                                           |
| 架构   | S12 live 路由 3/11                         | `tier_a_sync_router.py` L212–240                                            |
| 安全   | dry-run 非 READY 不 fail-closed            | `tier_a_sync_router.py` L75–80                                              |
| 性能   | —                                          | —                                                                           |

### 做得好的地方

- 11 源均有独立 replay e2e，bar/metadata/crypto 类测试断言具体 fixture 字段（close、announcement_id、mark_iv 等）。
- `test_tierA_incremental_registry.py` + `test_qmd_data_sync_tier_a_router.py` 将 ADR-028 canonical domain / clean_table 与 CLI dry-run 审计 JSON 绑定。
- `macro_incremental_common.run_macro_incremental` 单一金路径，避免四份 macro ops 复制粘贴。

---

## §维度裁决

**FAIL**

（§计划内 + §计划外 共 5 条非占位 finding）

---

## 计划内问题

| ID       | P   | 标题                             | 锚点                                                                                                                                                                                                                | 根因                                                                    | 修复方案                                                                                                                                                    | 验证                                                                                                                                                                                                                |
| -------- | --- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A4-P2-01 | P2  | cftc 缺幂等 replay e2e           | `tests/test_cftc_incremental_e2e.py`（无 idempotent 用例）；`to-issues-slices.md` S06 AC「idempotent repeat run」                                                                                                   | S06 切片未对齐 fred/bis/us_treasury 同族测试模板                        | 新增 `test_cftcIncremental_idempotent_secondRun_rowCountStable`：两次 `run_cftc_incremental` 后 `axis_observation` WHERE `indicator_id='088691'` COUNT 相等 | `uv run pytest tests/test_cftc_incremental_e2e.py -q`                                                                                                                                                               |
| A4-P2-02 | P2  | world_bank 缺 EMPTY_RESPONSE e2e | `tests/test_world_bank_incremental_e2e.py`（仅 2 个用例）；peer `test_bis_incremental_e2e.py` L88–113                                                                                                               | S05 未移植「水位已最新 → EMPTY_RESPONSE、行数不变」负向路径             | 新增 `test_worldBankIncremental_emptyResponse_whenWatermarkCurrent`：seed `axis_observation` 至 today 后跑 incremental，断言 `EMPTY_RESPONSE` 且 COUNT 不变 | `uv run pytest tests/test_world_bank_incremental_e2e.py -q`                                                                                                                                                         |
| A4-P2-03 | P2  | macro 五源 e2e 仅 COUNT≥1        | `test_fred_macro_incremental_e2e.py` L42–44；`test_us_treasury_incremental_e2e.py` L61–65；`test_bis_incremental_e2e.py` L61–65；`test_world_bank_incremental_e2e.py` L76–81；`test_cftc_incremental_e2e.py` L59–63 | 未像 bar 源断言 fixture `raw_value`/`source_used`，错误映射或假零可过测 | 各 e2e 主用例增加 `SELECT raw_value, source_used FROM axis_observation WHERE indicator_id=?` 与 mock fixture 已知值对齐（fred \_fixture 4.25 等）           | `uv run pytest tests/test_fred_macro_incremental_e2e.py tests/test_us_treasury_incremental_e2e.py tests/test_bis_incremental_e2e.py tests/test_world_bank_incremental_e2e.py tests/test_cftc_incremental_e2e.py -q` |

---

## 计划外发现

| ID       | P   | 标题                            | 锚点                                                                          | 根因                                                                                   | 修复方案                                                                                                                                                                                                 | 验证                                                         |
| -------- | --- | ------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| A4-P2-04 | P2  | 无 staging 终点负向断言         | 全部 `tests/test_*incremental_e2e.py`；ADR-028 L35「Staging-only … Rejected」 | e2e 只查 clean 表有行，未断言 promote 后 staging 无残留或未作为持久化边界              | 在代表性 e2e（至少 macro + bar + disclosure 各一）增加 `assert con.execute("SELECT COUNT(*) FROM <staging_table>").fetchone()[0] == 0` 或文档化 staging 清理由 orchestrator 保证并加 orchestrator 级单测 | 选定测试文件 `uv run pytest -q`                              |
| A4-P3-01 | P3  | dry-run 容忍 route_status≠READY | `backend/app/cli/tier_a_sync_router.py` L75–80                                | ponytail 注释允许降级 message 而非 fail-closed，运维 JSON 可能显示可审计但路由未 READY | S13 registry reconcile 后改为 `route_status != "READY"` 时 `raise error_for_route_status`；或 payload 增加 `"actionable": false` 字段并在文档说明                                                        | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -q` |

已对抗搜索：`tests/test_*incremental*`、`tests/test_*e2e*`、`backend/app/ops/*_incremental_*`、`backend/app/cli/tier_a_sync_router.py`、`backend/app/sync/incremental_source_registry.py`、`docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md`。

---

## Verification Story

| 项               | 结果                                          |
| ---------------- | --------------------------------------------- |
| 测试 reviewed    | 是 — 11 源 e2e + S00 registry + S12 router    |
| Build verified   | 否 — A4 只读，未跑 pytest                     |
| Security checked | 是 — CLI 默认 dry-run；无密钥；live 路径 gate |
