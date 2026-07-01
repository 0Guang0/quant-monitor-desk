# Wave 1–3 隔离生产链路验收报告

> **Authority:** Wave 3 闭合后的独立验收 SSOT（不替代 Wave 4 `R3-DCP-06` 五轴 PASS 硬门禁）。  
> **日期:** 2026-07-01  
> **基准 commit:** `master` @ `93b2c82`（Wave 4 prep §2.5 最终关账 + live 验收脚本入库）；prior `8e6b1e91`（P0–P2）· `af56e0d`（台账复验）  
> **隔离验收脚本:** `scripts/wave3_isolated_production_acceptance.py`  
> **连网 live 验收脚本:** `scripts/wave3_live_production_acceptance.py`（入库 @ `93b2c82`；参考 run `20260701T140102Z`）  
> **最终证据:** 隔离 — `.audit-sandbox/wave3-acceptance-<run_id>/acceptance_evidence.json`（本地 gitignore；参考跑 `20260701T115401Z` 11/11 PASS）  
> **连网证据:** `.audit-sandbox/wave3-live-acceptance-<run_id>/live_acceptance_evidence.json`（gitignore；参考 `20260701T140102Z`）  
> **主库污染:** **否** — `canonical_main_db` SHA256/mtime 验收前后一致

---

## 1. 执行摘要

| 项                      | 结论                                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **隔离验收总判**        | **PASS** — 11/11 步骤 exit 0                                                                                           |
| **全量 pytest**         | **PASS** — `uv run pytest -q` exit 0（~200s）                                                                          |
| **Wave 1–3 标记完成项** | **与代码/测试一致**；未发现「标 CLOSED 但链路不通」的 BLOCKING 项                                                      |
| **正式 Round4 PASS**    | **未达成** — 五轴 G12 仍在 Wave 4 `R3-DCP-06`；`PASS_ROUND4_REAL_DATA_READY` 待 Wave 4–5                               |
| **主库安全**            | **满足前提** — 验收全程 `QMD_DATA_ROOT` 指向 `.audit-sandbox/wave3-acceptance-*`；未写入 `data/duckdb/` canonical 路径 |

**一句话：** Wave 1–3 已实现的产品路径（registry、init、增量 sync 脚手架、写后抽检、R3G 排练护栏）在隔离库上可完整跑通；验收期间暴露 2 项卫生/根因问题已修复；Batch 6 与 live-primary 等刻意开放项仍须按路线图进入 Wave 4+，不得误读为「全面生产就绪」。

---

## 2. 验收方法与约束

### 2.1 方法（shipping-and-launch + test-driven-development）

1. 新建 `.audit-sandbox/wave3-acceptance-<run_id>/` 隔离数据根（`QMD_DATA_ROOT`）。
2. 记录本机「配置主库」指纹（当前为 `.audit-sandbox/user-live/duckdb/quant_monitor.duckdb`，非 `PROJECT_ROOT/data/duckdb/`）。
3. 按固定 11 步矩阵顺序执行（见 §3）。
4. 验收结束再次指纹对比；任何 mtime/sha256 变化 → CRITICAL finding。
5. 失败项记入 `findings[]` 并同步 `docs/quality/待修复清单.md`。

### 2.2 刻意未纳入本次 live 执行的范围

| 范围                                 | 原因                                                 | 路由                           |
| ------------------------------------ | ---------------------------------------------------- | ------------------------------ |
| baostock `--no-dry-run` 真实网络拉取 | 需外网 + 配额；验收用 dry-run + watermark/e2e 测覆盖 | Wave 4 `R3-DCP-05` Tier A 扩展 |
| FRED live API（非 mock）             | `B2.5-O-05` live primary 仍 open                     | `R3F-SH-06` / Wave 5           |
| 五轴审计 G1–G12                      | 规划硬门禁在 Wave 4 `R3-DCP-06`                      | Wave 4                         |
| Layer 绑定终态审计                   | Wave 5 `R3H-05` + GATE                               | Wave 5                         |
| Eastmoney / akshare live hist        | `R3-B2.75-REQ2-EM` 等硬约束                          | Batch 6 / `R3F-SH-07`          |

---

## 3. 验收步骤矩阵（20260701T115401Z）

| #   | Step ID                      | 内容                                      | 结果 | 耗时(s) |
| --- | ---------------------------- | ----------------------------------------- | ---- | ------- |
| 1   | `production_gate`            | `scripts/production_gate.py`              | PASS | 0.3     |
| 2   | `init_db`                    | 隔离库 migrations 001–014                 | PASS | 0.8     |
| 3   | `sync_registry`              | `source_registry.yaml` → 25 rows          | PASS | 0.8     |
| 4   | `pytest_full`                | 全量 `pytest -q`                          | PASS | 200.9   |
| 5   | `prod_equiv_smoke`           | `production_equivalent_smoke.py` 服务路径 | PASS | 12.9    |
| 6   | `round3_gate_matrix`         | Round3 门禁/注册表/活卡对齐测             | PASS | 0.7     |
| 7   | `wave3_dcp_tests`            | DCP-01/02/03 增量+CLI+写后抽检            | PASS | 18.5    |
| 8   | `qmd_route_preview`          | `qmd data route-preview` baostock READY   | PASS | 0.5     |
| 9   | `qmd_baostock_sync_dry_run`  | 增量窗口计算、零写入                      | PASS | 0.8     |
| 10  | `qmd_fred_sync_execute_mock` | `fred` `--no-dry-run` + mock 写隔离库     | PASS | 1.3     |
| 11  | `loop_maintain_check`        | 工程循环门禁                              | PASS | 0.5     |

**隔离库写入证据:** `isolated_db` sha256 `86f05c0e…` size 9,973,760 bytes（fred mock 增量 3 rows 后）。

---

## 4. Wave 1–3 完成度对账

对照 `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.7 与 `MODULE_COMPLETION_RATING.md` Pass D。

| 波次 / 模块                  | 规划状态       | 验收结论                                                              | 质量备注                      |
| ---------------------------- | -------------- | --------------------------------------------------------------------- | ----------------------------- |
| Wave 0 + R3H-01～04 + R3H-06 | CLOSED         | **符合** — registry/route/gate 矩阵绿                                 | 文档与测试对齐                |
| Wave 1 R3H-07 / R3H-10       | CLOSED         | **符合** — DataSourceService SSOT、无 bypass                          | C2 @ R4 sandbox               |
| Wave 2 R3H-08A–D             | CLOSED         | **符合** — live fetch 产品路径 + ResourceGuard                        | 非 full-history               |
| Wave 3 R3-DCP-01..03         | CLOSED         | **符合** — baostock watermark、e2e；fred 增量+mock 执行；写后 inspect | DCP-02 隔离库执行已修 guard   |
| R3G 排练 / clean-write       | CLOSED（机制） | **符合** — 生产路径仍拒绝；增量 sync 允许 audit 隔离库                | v3 `allow_isolated_data_root` |
| 五轴 G12                     | Wave 4 硬门禁  | **未验收** — 按规划不属于 Wave 3                                      | 不得提前 PASS                 |
| Batch 6 hygiene              | 刻意 open      | **未闭合** — 见 §6                                                    | 不阻塞 Wave 4 主线            |

**偏离计划：** 无 BLOCKING 偏离。验收前文档（`BATCH_3H README`、`MODULE_COMPLETION_RATING`）曾滞后，已于 2026-07-01 对账修复。

**未真正意义上的完成（预期内）：** live FRED primary、全量 Tier A 增量生产、五轴、R3H-05 layer 终态 — 均在路线图 Wave 4–5，非 Wave 3 承诺范围。

---

## 5. 验收期间发现与处置

### 5.1 已修复（本票关账）

| ID                            | 严重度   | 问题                                              | 根因                                                                | 修复                                                                                     | 验证                                         |
| ----------------------------- | -------- | ------------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------- |
| **ACC-SANDBOX-GUARD-001**     | BLOCKING | 隔离库下 `qmd data sync --no-dry-run` fred 被拒绝 | `assert_sandbox_db_allowed` 将 `DEFAULT_PRODUCTION_DB` 与隔离库混判 | 新增 `allow_isolated_data_root`；`data_commands` 增量路径传 `True`；R3G 排练默认 `False` | R3G 4 测 + fred cli 测 + 验收 step 10        |
| **ACC-MIGRATION-MATRIX-PATH** | HIGH     | `test_migration_coverage` 指向已归档 Trellis 路径 | 僵尸任务归档后硬编码未更新                                          | 路径改至 `.trellis/tasks/archive/2026-07/round3v-layer5-model-schema-reconcile/...`      | pytest + `docs/schema/MIGRATION_COVERAGE.md` |

### 5.2 验收脚本首次运行失败项（已消除）

| ID                             | 原失败步骤         | 现态                                  |
| ------------------------------ | ------------------ | ------------------------------------- |
| ACC-PYTEST_FULL                | sandbox guard 回归 | **已修复** — 全绿                     |
| ACC-QMD_FRED_SYNC_EXECUTE_MOCK | 同上               | **已修复** — mock 写 3 rows COMPLETED |

### 5.3 观察项（NON-BLOCKING，不进 Wave 4 阻塞）

| ID                   | 说明                                                                          | disposition                                                       |
| -------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| ACC-FLAKE-OBS-001    | 曾出现 `test_layer1Ingestion_phase4_taskEvidenceArtifacts` 全量偶发红、单跑绿 | **阶段外置** — Batch 6 `R3F-HYG-05`；本次全量跑未复现             |
| ACC-BAOSTOCK-NO-LIVE | 验收未跑 baostock `--no-dry-run`                                              | **阶段外置** — Wave 4 `R3-DCP-05`                                 |
| ACC-USER-LIVE-PATH   | 本机 `DATA_ROOT` 在 `.audit-sandbox/user-live` 非 canonical `data/`           | **文档化** — 排练护栏仍拒绝该路径；运维需注意与「真生产」路径区分 |

---

## 6. 仍开放的风险 / 缺口（进入 Wave 4 前知情）

> 完整台账：`docs/quality/待修复清单.md` §2–§3、§6。

### 6.1 不阻塞 Wave 4 主线（Batch 6 hygiene · P3 lineage）

> **2026-07-01 更新：** `R3Y-TEST-DEPTH-001` · `R3-B6-021-O-01` / `O-02` 已在 Wave 4 prep P0–P2 关账（见 §7 与 `待修复清单.md` §1）。下列 **P3 lineage 大项**仍 open：

- `ADV-R3X-LINEAGE-001` / `R3Y-LINEAGE-VR-001` — L3/L4 / L2 VR lineage 全量持久化

### 6.2 硬约束（不得误关）

- `B2.5-O-05` — live FRED primary
- `R3-PROMPT14-AKSHARE-VAL-01` — akshare live hist
- `R3-B2.75-REQ2-EM` — Eastmoney hist
- staged-only 全局 — 不得声称 production-live readiness

### 6.3 Wave 4 必须承接

| 规划 ID       | 内容                                  |
| ------------- | ------------------------------------- |
| R3-DCP-05..10 | Tier A 增量扩展、写路径、inspect 深化 |
| **R3-DCP-06** | **五轴全绿 — PASS 硬门禁**            |
| R3H-05 + GATE | Layer 绑定终态（Wave 5）              |

---

## 7. Wave 4 前卫生清理结论

| 类别                   | 动作                                                            | 状态                     |
| ---------------------- | --------------------------------------------------------------- | ------------------------ |
| 验收暴露 BLOCKING/HIGH | sandbox guard + migration 路径                                  | **已修**                 |
| **P0–P2（15 项）**     | registry · ops 文档 · Layer3 · HYG · perf CI · ADR 闭包         | **已修** @ 2026-07-01    |
| **§2.5 阻断（2 项）**  | `LIVE-PILOT-DB-001` · `LIVE-BAOSTOCK-SYNC-SILENT-001`           | **已修** @ `93b2c82`     |
| 僵尸 Trellis 任务      | 11 目录归档 + 证据路径修复                                      | **已完成**               |
| Batch 6 P3 lineage     | `ADV-R3X-LINEAGE-001` / `R3Y-LINEAGE-VR-001`                    | **阶段外置** §2          |
| 可重跑验收             | `uv run python scripts/wave3_isolated_production_acceptance.py` | **随时可复验**           |
| 连网 live 验收（可选） | `uv run python scripts/wave3_live_production_acceptance.py`     | **已入库**；CI 待 DCP-09 |

---

## 8. 建议下一步

1. **开工 Wave 4** — 从 `R3_DCP_TO_ISSUES_INDEX.md` 活卡增补 DCP-05..10（主会话 Plan 门控）。
2. **CI** — `ci_perf_budget_artifact.py` 已接入 `.github/workflows/ci.yml`；可选将 `wave3_isolated_production_acceptance.py` 纳入 nightly。
3. **勿** 用本次隔离验收替代 DCP-06 五轴或 R3H-05-GATE。

---

## 9. 证据索引

| 产物                | 路径                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------- |
| 最终验收 JSON       | `.audit-sandbox/wave3-acceptance-20260701T115401Z/acceptance_evidence.json`           |
| prod-equiv 预算     | `.audit-sandbox/wave3-acceptance-20260701T115401Z/prod_equiv_budget.json`             |
| 早期失败跑（对比）  | `.audit-sandbox/wave3-acceptance-20260701T113150Z/`、`113735Z/`                       |
| 待修复台账          | `docs/quality/待修复清单.md`                                                          |
| 模块评级            | `MODULE_COMPLETION_RATING.md`                                                         |
| 路线图              | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.7–3.7.1                                        |
| 连网 live 验收 JSON | `.audit-sandbox/wave3-live-acceptance-20260701T140102Z/live_acceptance_evidence.json` |
