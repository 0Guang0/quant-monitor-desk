# Adversarial Audit Report — round3-readonly-data-health-v1（Wave C C-20）

> **Auditor:** C-20 对抗性审计 Agent · `composer-2.5`  
> **工作区：** `quant-monitor-desk-wt-r3-data-health`  
> **分支：** `feature/round3-readonly-data-health-v1`  
> **日期：** 2026-06-24  
> **输入：** Repair `audit.report.md`、`audit_matrix.json`、`research/audit-evidence/a1–a8.md`、`agents/audit-adversarial-authority.md`  
> **约束：** 只读审计 + sandbox 复跑；**禁止 commit**

---

## 总判定

| 项                            | 值                                                                                                               |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **对抗性审计判定**            | **PASS_WITH_MERGE_GATE**                                                                                         |
| **Repair 声称 CLOSED 项**     | **14/14 业务阻断复验通过**（首轮 A1/A4/A5 BLOCKING 已闭合）                                                      |
| **OPEN（BLOCKING）**          | **1** — `A5-B04` 实现 + loop 产物未 commit                                                                       |
| **OPEN（NON-BLOCKING）**      | **0**                                                                                                            |
| **DEFERRED**                  | **5**（Batch6 / merge 后 hygiene，与 `audit_matrix.json` 一致）                                                  |
| **主会话可否 §6 + §8.1 提交** | **否** — 须先 commit allowed 文件 + `tests/test_catalog.yaml` + `docs/generated/*`，再跑 `uv run pytest -q` 全绿 |

---

## Repair 重点复验

| Repair 声称                                       | 对抗性复验            | 证据                                                                                                                                                                                                                                                               |
| ------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| v2 evidence 集成不再假 FAIL                       | **CONFIRMED**         | `check_lineage_entry` 回退 `request.source_id` / `default_as_of`（`data_health.py:449-454,491`）；`test_dataHealthLineage_v2ManifestEntry_passes`；`test_dataHealthIntegration_v2Evidence_bundle` 断言 `overall_status in {PASS,WARN}` 且无 `MISSING_SOURCE_USED`  |
| `_checks_from_bundle` 跑 bar + metadata           | **CONFIRMED**         | `data_health.py:661-707` 读 `raw_file_paths`/`relative_paths`，按 domain 调用 `check_daily_bars` / `check_metadata_rows`；`test_dataHealthIntegration_badBarBundle_fails` 经 service 路径 FAIL + `INVALID_OHLC`                                                    |
| fail-closed lineage / evidence sandbox            | **CONFIRMED**         | `SourceNotFoundError` → `DISABLED_SOURCE_USED` FAIL（`:510-518`）；`evidence_dir_within_project` + CLI exit 2（`data_health_cli.py:39-44`）；`test_dataHealthLineage_unknownSource_fails`、`test_dataHealthCli_pathOutsideProject_rejected`                        |
| ponytail：无 dead code、fixture SSOT、~170 行净减 | **CONFIRMED（行为）** | 无 `default_v2_evidence_dir` / `_DEFAULT_V2_EVIDENCE`；复用 `staged_pilot._equity_bar_rows` / `_resolve_evidence_path`；CLI 测用 `tests/fixtures/data_health/good_bundle`；`data_health.py` 现 ~733 行（相对 Repair 前中间态净减由 Repair 自述，未逐行 diff 复核） |
| 23 tests 五字段 + 语义断言                        | **CONFIRMED**         | `--collect-only` → **23**；`覆盖范围` 出现 **23/23**；集成测已收紧 v2 PASS/WARN + 日 K rule_id 曾运行（非 `{PASS,WARN,FAIL}` 恒真集合）                                                                                                                            |

**对抗性注记：** 首轮 `research/audit-evidence/a1.md` / `a4.md` / `a5.md` 仍为 **FAIL** 快照；Repair 后代码与 sandbox 复跑已推翻其 BLOCKING 结论。本报告以 **2026-06-24 工作区实跑** 为准。

---

## Playbook §8.1 逐行 PASS 对照

| §8.1 维度    | PASS？                   | 对抗性证据 / 残留                                                                                                                                                                                                                |
| ------------ | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Plan**     | **条件 PASS**            | `loop_maintain.py --fix` 后 `validate-plan-freeze` exit **0**；`implement.jsonl` 含 `data_health*.py` + `test_ops_data_health.py`。**未 commit** 时 `test_loop_engineering_flow` 会 `git checkout` 还原 catalog → 全量 pytest 红 |
| **实现**     | **PASS**                 | `data_health.py` + `data_health_cli.py`；零 DuckDB/WriteManager/fetch；`production_db_mutated`/`source_fetch_performed` 硬编码 false                                                                                             |
| **业务 AC**  | **PASS**                 | v2 archive evidence 集成绿；`bad_bar_bundle` service 路径 meaningful FAIL                                                                                                                                                        |
| **规则面**   | **PASS**                 | MASTER §5.3b 13 `rule_id` 均有独立 `test_*`；集成路径已接线日 K/metadata                                                                                                                                                         |
| **切片证据** | **PASS（薄）**           | `execute-evidence/8.*` 齐；GREEN 仍为摘要行 → `A5-NB01` **DEFERRED**                                                                                                                                                             |
| **测试**     | **条件 PASS**            | 切片 **23 passed**；五字段 23/23；**Tier B** `uv run pytest -q` 须 **commit catalog** 后绿（见 §6）                                                                                                                              |
| **MAP 验证** | **PASS**                 | 切片 + 邻接（含 `test_source_conflict_validator`、`test_db_validation_gate`、`test_raw_store`）exit **0**                                                                                                                        |
| **Audit**    | **PASS_WITH_MERGE_GATE** | A1–A8 证据已读；本报告；`audit_matrix` 余 **1 OPEN**（提交锚点）                                                                                                                                                                 |
| **边界**     | **PASS**                 | 无 layer4 / `staged_evidence.py` / registry 三件套 diff；gate 未声称 production-live                                                                                                                                             |
| **门禁陈述** | **PASS**                 | `sandbox_clean_write_gate_ready` + `gate_rationale`；v2 closeout `sandbox_clean_write_rehearsal=false` 时 rationale 诚实                                                                                                         |

**§8.1 全行绿：** 主会话 **commit 后** 可满足；当前工作区 **不能** 标全绿。

---

## Playbook §6 主会话清单（预检）

| §6 项                       | 状态                                                                                            |
| --------------------------- | ----------------------------------------------------------------------------------------------- |
| MAP §2.2 Verification 全绿  | **PASS**（切片 + 邻接）                                                                         |
| `uv run pytest -q` 全量     | **FAIL** — catalog 未 commit；`test_loopMaintain_check_passesWhenRepoFresh` 等 5 例红           |
| `loop_maintain.py` check    | **FAIL**（未 commit catalog）；`--fix` 后 **OK**                                                |
| GitNexus `detect_changes()` | **未跑**（禁止 commit；merge 前主会话须跑）                                                     |
| 五字段 + 测试 ponytail      | **PASS**                                                                                        |
| §3.2 权威索引               | **PASS**（`implement.jsonl` 71 行）                                                             |
| composer-2.5 派发           | **PASS**                                                                                        |
| `validate-execute-handoff`  | **FAIL** — `task.json` 仍 `in_progress` + matrix 与 handoff 状态不一致（commit 后由主会话收尾） |
| 分支 worktree 已提交        | **FAIL** — `A5-B04`                                                                             |

---

## pytest 复跑（C-20 sandbox）

| 命令                                                                     | exit  | 摘要                                                                                                                                                                           |
| ------------------------------------------------------------------------ | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `uv run pytest tests/test_ops_data_health.py -q`                         | **0** | **23 passed**                                                                                                                                                                  |
| MAP §2.2 邻接（6 模块）                                                  | **0** | 全绿（1 skipped 为既有）                                                                                                                                                       |
| `uv run pytest -q`（Tier B）                                             | **1** | **5 failed** — 均 `unregistered test module: tests/test_ops_data_health.py`（catalog 未 commit；`test_loopMaintain_fix_writesCatalogAndMaps` 的 `finally: git checkout` 设计） |
| `uv run pytest -q --ignore=tests/test_loop_engineering_flow.py`          | **0** | 业务面全绿（**非** §6 正式口径）                                                                                                                                               |
| `uv run python scripts/loop_maintain.py --fix` 后 `validate-plan-freeze` | **0** | Plan freeze 绿（catalog 在 working tree）                                                                                                                                      |

**catalog 说明：** Repair 曾 `--fix` 登记 `test_ops_data_health.py`，但 loop 元测故意还原 `tests/test_catalog.yaml`。**主会话须将 catalog + generated 与实现一并 commit**，此后 `uv run pytest -q` 方可作为 §6 证据。

---

## OPEN / DEFERRED

| ID         | 状态                 | 对抗性裁决                                                                                                                       |
| ---------- | -------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **A5-B04** | **OPEN（BLOCKING）** | 实现、`tests/`、任务工件、`test_catalog.yaml`、`docs/generated/*` 均未 commit → **主会话 merge 前提交**；对抗性审计不代为 commit |
| A1-02      | DEFERRED             | Batch6 委托 `DataQualityValidator` — 接受                                                                                        |
| A1-03      | DEFERRED             | metadata 字段扩展 — 接受                                                                                                         |
| A1-05      | DEFERRED             | GitNexus 索引刷新 — post-merge                                                                                                   |
| A1-07      | DEFERRED             | `INVALID_OHLC` ↔ 契约 rule_id — Batch6                                                                                           |
| A5-NB01    | DEFERRED             | GREEN 证据补完整 pytest session — hygiene                                                                                        |

**计划外发现（对抗搜索后）**

| ID         | 发现                                | 等级 | 说明                               |
| ---------- | ----------------------------------- | ---- | ---------------------------------- |
| OOB-C20-01 | Tier B 依赖 **committed** catalog   | P1   | 非 data_health 回归；loop 元测契约 |
| OOB-C20-02 | 首轮 `a*.md` 与 Repair 后状态不同步 | P3   | 建议主会话归档或刷新 a1/a4/a5 摘要 |
| OOB-C20-03 | manifest JSON 无 `max_bytes` 上限   | P3   | 继承 A3 P3；staged 信任模型        |

**对抗搜索声明：** 已对照 R3Y 任务卡 §3–§11、playbook §6/§8.1、MAP §2.2、`staged_pilot` v2 manifest、`data_quality_rules.yaml`、Repair 后 `data_health.py` 全文及 23 测；除上表外未发现新的 forbidden 触及或 production-live 声称。

---

## A 维摘要（Repair 后）

| 维  | Repair 矩阵 | 对抗性复验                                                    |
| --- | ----------- | ------------------------------------------------------------- |
| A1  | pass        | **PASS** — evidence 集成已接线日 K/metadata                   |
| A2  | pass        | **PASS** — dead code 已删；fixture SSOT                       |
| A3  | pass        | **PASS** — fail-closed + sandbox 已落地                       |
| A4  | pass        | **PASS** — v2 假 FAIL 已消；STALE_DATA WARN                   |
| A5  | pass        | **PASS_WITH_MERGE_GATE** — 业务 AC 绿；commit/Tier B 待主会话 |
| A6  | skip        | **SKIP** — 维持                                               |
| A7  | pass        | **PASS**                                                      |
| A8  | pass        | **PASS** — 23/23 五字段；集成语义已加强                       |

---

## 主会话最小路径（merge gate）

1. **Commit** allowed：`backend/app/ops/data_health*.py`、`tests/test_ops_data_health.py`、`tests/fixtures/data_health/**`、`.trellis/tasks/round3-readonly-data-health-v1/**`（含本报告）、`tests/test_catalog.yaml`、`docs/generated/*`（`loop_maintain.py --fix` 产物）。
2. `uv run pytest -q` → exit **0**。
3. `validate-execute-handoff` + GitNexus `detect_changes()`。
4. 将 `task.json` 标为 audit 完成 / handoff 就绪。
5. 勾选 playbook **§6** + **§8.1** 全行 → 主会话提交。

---

## 返回摘要（协调者）

| 字段                        | 值                                           |
| --------------------------- | -------------------------------------------- |
| **PASS / FAIL**             | **PASS_WITH_MERGE_GATE**                     |
| **OPEN 数**                 | **1** BLOCKING（`A5-B04`）；DEFERRED **5**   |
| **可否主会话 §6+§8.1 提交** | **否** — 须 commit + 全量 pytest 绿后 **可** |
