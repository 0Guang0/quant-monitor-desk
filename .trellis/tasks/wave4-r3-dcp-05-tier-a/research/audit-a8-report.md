# Audit A8 — 测试缺口（audit-test-gap）

| 字段                  | 值                     |
| --------------------- | ---------------------- |
| 维度                  | A8                     |
| 任务                  | wave4-r3-dcp-05-tier-a |
| plan_protocol_version | 4.1                    |
| 模板                  | `agents/qa-expert.md`  |
| 日期                  | 2026-07-02             |
| 审计员                | A8 subagent            |

---

## 维度证据

### 1. 全量 pytest（AUDIT.plan §2 A8）

| 项             | 结果               |
| -------------- | ------------------ |
| 命令           | `uv run pytest -q` |
| exit code      | **0**              |
| collected      | **2041**           |
| skipped        | **3**              |
| passed（推算） | **2038**           |
| failed         | **0**              |

Skip 明细（`-rs`）：

| 模块                                         | 原因                                                                 |
| -------------------------------------------- | -------------------------------------------------------------------- |
| `tests/test_batch275_live_pilot_gate.py:830` | `need --run-network for live vendor fetch tests`                     |
| `tests/test_fred_sandbox_pilot.py:260`       | `FRED_API_KEY present — CLOSED-SKIP-OPT-IN applies only without key` |
| `tests/test_ops_db_inspector.py:440`         | `symlinks not supported on this platform`                            |

以上 3 条均为环境/平台 opt-in，**非 DCP-05 新增 skip**；仓库内 **无** `@pytest.mark.flaky`。

### 2. 切片 S00–S13 建议测试 vs 实际文件

| Slice   | to-issues 建议测试                                                                             | 实际测试文件                                                                                                                                                                                           | 映射       |
| ------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| **S00** | `test_schema_migration` · `test_tierA_incremental_registry_*` · `test_migration_coverage` 更新 | `tests/test_schema_migration.py`（`015_dcp05_tier_a_clean` 在 `ALL_MIGRATION_VERSIONS`）· `tests/test_tierA_incremental_registry.py`（22 用例）· `tests/test_migration_coverage.py`（**无 015 引用**） | **部分**   |
| **S01** | `test_qmd_data_sync_baostock.py` · optional `--run-network`                                    | `tests/test_qmd_data_sync_baostock.py`（含 `QMD_ALLOW_LIVE_FETCH` / `resolve_baostock_incremental_use_mock`）· `tests/test_baostock_incremental_*.py`                                                  | **是**     |
| **S02** | `test_fred_macro_incremental_*.py`                                                             | `tests/test_fred_macro_incremental_{watermark,port,e2e,cli}.py`                                                                                                                                        | **是**     |
| **S03** | `test_us_treasury_incremental_*`                                                               | `tests/test_us_treasury_incremental_e2e.py`（3）· `tests/test_us_treasury_incremental_watermark.py`（2）                                                                                               | **是**     |
| **S04** | `test_bis_incremental_*`                                                                       | `tests/test_bis_incremental_e2e.py`（4，含 emptyResponse + livePort）                                                                                                                                  | **是**     |
| **S05** | `test_world_bank_incremental_*`                                                                | **仅** `tests/test_world_bank_incremental_e2e.py`（2：replay + idempotent）                                                                                                                            | **缺口**   |
| **S06** | `test_cftc_incremental_*`                                                                      | `tests/test_cftc_incremental_e2e.py`（3，含 emptyResponse + weekly）                                                                                                                                   | **是**     |
| **S07** | `test_cninfo_incremental_*`                                                                    | `tests/test_cninfo_incremental_e2e.py` · `tests/test_cninfo_incremental_watermark.py`                                                                                                                  | **是**     |
| **S08** | `test_mootdx_incremental_*`                                                                    | `tests/test_mootdx_incremental_e2e.py`（4，无 caught-up/empty-response）                                                                                                                               | **部分**   |
| **S09** | `test_sec_edgar_incremental_*`                                                                 | `tests/test_sec_edgar_incremental_e2e.py` · `tests/test_sec_edgar_incremental_watermark.py`                                                                                                            | **是**     |
| **S10** | `test_alpha_vantage_incremental_*`                                                             | `tests/test_alpha_vantage_incremental_e2e.py` · `tests/test_alpha_vantage_incremental_watermark.py`                                                                                                    | **是**     |
| **S11** | `test_deribit_incremental_*`                                                                   | `tests/test_deribit_incremental_e2e.py` · `tests/test_deribit_incremental_watermark.py`                                                                                                                | **是**     |
| **S12** | `test_qmd_data_sync_tier_a_router.py`（11 源 help/route）                                      | `tests/test_qmd_data_sync_tier_a_router.py`（14：11×param dry-run + 3 集成/负向）· `--source-id` help 由 `test_fred_macro_incremental_cli.py::test_fredIncrementalCli_help_showsSourceIdFlag` 覆盖     | **大部分** |
| **S13** | loop_maintain · ops 文档                                                                       | `tests/test_catalog.yaml` 已登记 DCP-05 增量模块 · `tests/test_loop_engineering_flow.py` 覆盖 `loop_maintain.py`                                                                                       | **是**     |

**DCP-05 新增/扩展测试模块（test_catalog 已登记）：**  
`test_tierA_incremental_registry` · `test_qmd_data_sync_tier_a_router` · `test_{bis,cftc,us_treasury,world_bank}_incremental_e2e` · `test_{cninfo,sec_edgar,alpha_vantage,deribit,mootdx}_incremental_{e2e,watermark}` · `test_qmd_data_sync_baostock`（S01 live gate 扩展）。

### 3. 五字段 docstring 抽检（DCP-05 新增）

| 模块                                  | 用例数 | 五字段                           | 门禁                                          |
| ------------------------------------- | ------ | -------------------------------- | --------------------------------------------- |
| `test_qmd_data_sync_tier_a_router.py` | 14     | 全覆盖（人工读 4 条 + 11×param） | `test_docstring_quadruple_coverage.py` **绿** |
| `test_tierA_incremental_registry.py`  | 22     | 全覆盖                           | 同上                                          |
| `test_bis_incremental_e2e.py`         | 4      | 全覆盖                           | 同上                                          |
| `test_mootdx_incremental_e2e.py`      | 4      | 全覆盖                           | 同上                                          |
| `test_world_bank_incremental_e2e.py`  | 2      | 全覆盖                           | 同上                                          |

全库 `uv run python -m pytest tests/test_docstring_quadruple_coverage.py -q` → **exit 0**。

### 4. 对抗性扫描（A8 最低动作）

| 扫描项                      | 结论                                                                                                                                                                                                        |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| plan-doubt-review Red Flags | D1（11/11 clean）有 registry + e2e 网；无单独 pytest Red Flag 表项                                                                                                                                          |
| 负向 / fail-closed          | Tier A router 函数级 unknown source **有**；CLI `main.main` unknown `--source-id` **无**                                                                                                                    |
| 同级 macro 边界对称         | `bis`/`us_treasury`/`cftc`/`fred` 均有 `emptyResponse_whenWatermarkCurrent`；`world_bank` **无**                                                                                                            |
| watermark 单测对称          | `us_treasury`/`fred`/`cninfo`/`sec_edgar`/`deribit`/`alpha_vantage` 有 `*_watermark.py`；`world_bank` 有 `world_bank_incremental_watermark.py` 生产模块但 **无** `test_world_bank_incremental_watermark.py` |
| flaky 标记                  | **0**                                                                                                                                                                                                       |
| purpose drift               | `test_schema_migration.py::test_appliedVersions_afterMigration_containsFoundation` docstring 仍写「001–012 共 12 项」，断言已用含 `015` 的 `ALL_MIGRATION_VERSIONS`                                         |

已对抗搜索：`tests/test_*incremental*.py` · `tests/test_qmd_data_sync_tier_a_router.py` · `tests/test_tierA_incremental_registry.py` · `tests/test_migration_coverage.py` · `tests/test_schema_migration.py` · `to-issues-slices.md` S00–S13 建议测试列 · 全库 `@pytest.mark.flaky` / `skipif` on DCP-05 paths。

---

## §维度裁决

**FAIL**

（§计划内问题 3 条 + §计划外发现 1 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                           | 锚点                                                                                                                                                                  | 根因                                                                                  | 修复方案                                                                                                                                                                                                                            | 验证                                                                                      |
| --------- | --- | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| A8-P2-001 | P2  | S05 world_bank 增量测试薄于同级 macro 源       | `to-issues-slices.md` S05 · `tests/test_world_bank_incremental_e2e.py`（仅 2 用例）· 对比 `tests/test_bis_incremental_e2e.py`                                         | Execute 只落地 happy+idempotent，未对齐 peer 的 watermark 单测与 caught-up/empty 负向 | 新增 `tests/test_world_bank_incremental_watermark.py`（cold start / existing observation）；在 e2e 补 `test_worldBankIncremental_emptyResponse_whenWatermarkCurrent`（仿 `test_bisIncremental_emptyResponse_whenWatermarkCurrent`） | `uv run pytest tests/test_world_bank_incremental_*.py -q` exit 0                          |
| A8-P2-002 | P2  | S00 `test_migration_coverage` 未按切片更新 015 | `to-issues-slices.md` S00 AC「`test_migration_coverage` 更新」· `tests/test_migration_coverage.py`（无 `015`/`dcp05`）                                                | S00 矩阵门禁未绑定 migration 015 与 DCP-05 clean 扩展表                               | 在 `test_migration_coverage.py` 增加断言：`schema_version` 含 `015_dcp05_tier_a_clean`；`us_disclosure_clean`/`crypto_derivative_clean` 在 full migrate 后存在（或扩 `CLEAN_DOMAIN_MIGRATED_TABLES` 并注释 015 来源）               | `uv run pytest tests/test_migration_coverage.py tests/test_schema_migration.py -q` exit 0 |
| A8-P2-003 | P2  | S08 mootdx 缺 watermark-current / 空响应 e2e   | `to-issues-slices.md` S08 · `tests/test_mootdx_incremental_e2e.py` · 对比 `test_cninfo_incremental_e2e.py::test_cninfoIncremental_emptyResponse_whenWatermarkCurrent` | bar 源 e2e 未覆盖「水位已追平 → 无新 bar」运维安全路径                                | 补 `test_mootdxIncremental_emptyResponse_whenWatermarkCurrent`（seed watermark==end，断言 COMPLETED 且行数不变/无新 fetch）                                                                                                         | `uv run pytest tests/test_mootdx_incremental_e2e.py -q` exit 0                            |

---

## 计划外发现

| ID        | P   | 标题                                             | 锚点                                                                                                                                                                         | 根因                                                                                                  | 修复方案                                                                                                                                          | 验证                                                                 |
| --------- | --- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| A8-P2-004 | P2  | Tier A CLI 未知 `--source-id` 未在 main 层回归   | `backend/app/cli/tier_a_sync_router.py` · `tests/test_qmd_data_sync_tier_a_router.py`（仅 `sync_tier_a_by_source_id` 负向）· `test_tierASyncRouter_unknownSource_failClosed` | 负向只测函数 API，未测 `main.main(["data","sync","--source-id","akshare",...])` 的 exit code / stderr | 在 `test_qmd_data_sync_tier_a_router.py` 增 `test_tierASyncRouter_cliMain_unknownSource_exitNonZero`：`rc != 0` 且 stderr/JSON 含 `INVALID_INPUT` | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -q` exit 0  |
| A8-P3-001 | P3  | schema_migration 用例 docstring 与断言版本集漂移 | `tests/test_schema_migration.py::test_appliedVersions_afterMigration_containsFoundation` L91–100                                                                             | 015 加入 `ALL_MIGRATION_VERSIONS` 后未同步 docstring「001–012 共 12 项」                              | 将 docstring 验证点改为「等于 `ALL_MIGRATION_VERSIONS`（含 015_dcp05_tier_a_clean）」                                                             | `uv run pytest tests/test_docstring_quadruple_coverage.py -q` exit 0 |

已对抗搜索：plan-doubt-review · to-issues S00–S13 · DCP-05 incremental 全模块 · tier_a router CLI 边界 · flaky/skip 标记 · 五字段全库门禁。

---

## 摘要

| 项                 | 值                                                                  |
| ------------------ | ------------------------------------------------------------------- |
| §维度裁决          | **FAIL**                                                            |
| findings（非占位） | **5**（计划内 3 · 计划外 2）                                        |
| pytest             | exit **0** · collected **2041** · skipped **3**                     |
| 报告路径           | `.trellis/tasks/wave4-r3-dcp-05-tier-a/research/audit-a8-report.md` |
