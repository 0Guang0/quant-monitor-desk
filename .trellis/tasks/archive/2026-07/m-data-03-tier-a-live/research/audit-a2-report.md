# Audit A2 — Ponytail（M-DATA-03 Plan R2）

## 元信息

| 字段                    | 值                                          |
| ----------------------- | ------------------------------------------- |
| 维度                    | A2 — audit-ponytail                         |
| 任务                    | `.trellis/tasks/m-data-03-tier-a-live`      |
| `plan_protocol_version` | 4.1                                         |
| 模板                    | `agents/audit-a2-ponytail.md`               |
| 审计日期                | 2026-07-03                                  |
| 分支                    | `feature/m-data-03-tier-a-live` vs `master` |

---

## 维度证据

### Boot checklist

- [x] `agents/audit-adversarial-authority.md` · `audit-boot-v4.1.md` · `audit-finding-schema.md` · `AUDIT.plan.md` §2 A2 · `00-EXECUTION-ENTRY.md` · `to-issues-slices.md` · `gitnexus-audit-summary.md` 已读
- [x] `git diff master...HEAD` + `--stat` 已记录
- [x] `EXECUTION_INDEX` §1 触及文件 + `to-issues-slices.md` R2 切片已对照
- [x] DOUBT：≥1 处 ≥20 行可简化（见 §计划外发现）
- [x] 与 A4 交叉：`_extract_sync_status` 多形态解析归 A4；本维不重复开项

### `git diff --stat`（A2 核心生产）

| 区域                                  | 净增（约） | 备注                                |
| ------------------------------------- | ---------- | ----------------------------------- |
| `tier_a_live_acceptance.py`           | +692       | S-R2-ACCEPT 编排 + manifest         |
| `tier_a_live_incremental_dispatch.py` | +634       | S-R2-DISPATCH 金路径                |
| `data_health_profiles/*`              | +745       | S-R2-F0 四族（explicit AC）         |
| `tier_a_live_status.py`               | +37        | R1 A2-P2-004 收敛                   |
| `tests/live_incremental_support.py`   | +101       | 泛型 port bootstrap（partial 采纳） |
| `backend/app/db/`                     | **0**      | 无新 migration 文件                 |

**全分支：** 140 files · +10934 / -125

### 计划内约束核对（AUDIT.plan §2 A2）

| 检查项                        | 裁决                   | 证据                                                                                                     |
| ----------------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------- |
| 无新 migration                | **PASS**               | `git diff master...HEAD -- backend/app/db/` 空；`migrations/` 最高仍为 `015_dcp05_tier_a_clean.sql`      |
| clean 矩阵（ADR-028 DDL）不变 | **PASS**               | 无新 `.sql` migration；`data_quality_rules.yaml` 仅增 `ops_cli_profiles`（F0 规则登记，非 clean 表 DDL） |
| `platform_source_matrix`      | **PASS（计划内变更）** | 仅增三平台 `mootdx` default_enabled；符合 `plan-revision-r2.md` AC#6 / S-R2-DISPATCH                     |

### §3.2 候选删改追溯

| 候选删改（file:line）                                                                 | ponytail 梯级                               | 备注                                                                                           |
| ------------------------------------------------------------------------------------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `alpha_vantage/cninfo/sec_edgar_incremental_support.py` 各 `bootstrap_*_live_e2e_ctx` | **2**（复用 `bootstrap_port_live_e2e_ctx`） | 泛型已存在；三源仍各 ~30 行平行骨架 → finding                                                  |
| `data_health_profiles/__init__.py:344-352` vs `evidence_loader.py:57-65`              | **2**（删重复）                             | `_lineage_from_payload` ≡ `_lineage_from_bundle`                                               |
| `tier_a_live_status.py:11-14` `_BAR/_MACRO_SOURCE_IDS`                                | **6**（删死代码）                           | 全仓零消费，仅 `__all__` 导出                                                                  |
| `_live_sync_runner_for` ~359-563                                                      | —                                           | R1 A2-P1-001 已修：`_macro_live_runner` / `_port_live_runner` 表驱动；属 explicit AC，非 bloat |
| `_prepare_sandbox`                                                                    | —                                           | R1 A2-P1-002 已修：不再 `apply_migrations`                                                     |
| `data_health_profiles/*` 新模块                                                       | —                                           | S-R2-F0 explicit AC；非 YAGNI                                                                  |
| `deribit` `bootstrap_deribit_live_e2e_ctx`                                            | —                                           | 含 live instrument 探测；暂保留专函合理                                                        |

### 对抗搜索声明

已读：`backend/app/ops/tier_a_live_*.py` · `tier_a_live_status.py` · `data_health_profiles/` · `validation/data_quality_validator.py` · `tests/live_incremental_support.py` · `tests/*incremental_support.py` · `tests/test_tier_a_live_*.py` · `tests/test_data_health_tier_a_profiles.py`；对照 R1 `archive/plan-r1-superseded/audit-a2-report.md` 关账项与 `plan-doubt-review.md` Cycle 1。

---

## §维度裁决

**FAIL**

（§计划外发现 ≥1 行非占位）

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

---

## 计划外发现

| ID        | P   | 标题                                | 锚点                                                                                                                                  | 根因                                                                                                                                                                                            | 修复方案                                                                                                                                                                  | 验证                                                                                                                                                                                                  |
| --------- | --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| A2-P3-001 | P3  | port 源 live bootstrap 未收敛至泛型 | `tests/alpha_vantage_incremental_support.py:45-77` · `cninfo_incremental_support.py:53-82` · `sec_edgar_incremental_support.py:49-78` | R2 已新增 `tests/live_incremental_support.py:bootstrap_port_live_e2e_ctx`，但 alpha_vantage/cninfo/sec_edgar 仍各 ~30 行重复 env·ResourceGuard·`bootstrap_acceptance_cm`·port·orch·service 骨架 | 三文件改为薄包装调用 `bootstrap_port_live_e2e_ctx(...)`（传 `source_id`/`port_factory`/`service_builder`/`registry_factory`/`since_reader`）；fred/deribit 可后续单独收敛 | 三 support 文件各减 ≥20 行；`uv run pytest tests/test_alpha_vantage_incremental_e2e.py tests/test_cninfo_incremental_e2e.py tests/test_sec_edgar_incremental_e2e.py -m network -q`（`--run-network`） |
| A2-P3-002 | P3  | F0 profile 重复 lineage helper      | `data_health_profiles/__init__.py:344-352` · `evidence_loader.py:57-65`                                                               | `_lineage_from_payload` 与 `_lineage_from_bundle` 逐字相同；两处维护                                                                                                                            | 保留 `evidence_loader._lineage_from_bundle` 为 SSOT；`__init__` import 复用并删本地定义                                                                                   | `rg '_lineage_from_payload' backend/app/ops/data_health_profiles` 仅 import/调用；`uv run pytest tests/test_data_health_tier_a_profiles.py -q`                                                        |
| A2-P3-003 | P3  | `tier_a_live_status` 死常量导出     | `backend/app/ops/tier_a_live_status.py:11-14,31-34`                                                                                   | `_BAR_SOURCE_IDS` / `_MACRO_SOURCE_IDS` 定义并 `__all__` 导出，全仓无 import 消费                                                                                                               | 删除两常量及 `__all__` 项；若未来需要再按调用点引入                                                                                                                       | `rg '\_BAR_SOURCE_IDS\\                                                                                                                                                                               | \_MACRO_SOURCE_IDS' backend/` 零命中；`uv run pytest tests/test_tier_a_live_dispatch.py tests/test_tier_a_live_harness.py -q` |

已对抗搜索：`backend/app/ops/tier_a_live*.py` · `data_health_profiles/` · `tests/*incremental_support.py` · `tests/test_*_incremental_e2e.py` live 段 · `tests/test_tier_a_live_*.py` · `backend/app/db/migrations/`；R1 八项 finding 中六项已在 R2 消除（死函数、双份常量、重复 migration、不可达分支、dispatch 大块 copy-paste、harness 重复 gate 测）。
