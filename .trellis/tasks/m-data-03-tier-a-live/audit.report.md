# Audit Report — m-data-03-tier-a-live（Plan R2 · 合规重派 A1–A8）

> Findings SSOT：`agents/audit-finding-schema.md` · 各维 `research/audit-a{n}-report.md` · Ledger：`research/audit-repair-ledger.md`

## 1. 元信息

| 字段                     | 值                                                                    |
| ------------------------ | --------------------------------------------------------------------- |
| 任务                     | M-DATA-03 Plan R2 — 11 源 R4 真网完整验收                             |
| 分支                     | `feature/m-data-03-tier-a-live`                                       |
| 协议                     | `plan_protocol_version: 4.1`                                          |
| 派发                     | 2026-07-03 合规重派（8 维独立 agent · `composer-2.5`）                |
| GitNexus 7.pre           | `research/gitnexus-audit-summary.md`                                  |
| Execute handoff          | `validate-execute-handoff` 已通过                                     |
| pytest（A5/A8 独立复验） | `uv run pytest -q` exit **0**（Repair 关账）                          |
| tier-a 专项 pytest       | exit **0**                                                            |
| 11/11 live 证据          | `research/archive/non-plan/execute/r2-tier-a-live-accept-evidence.md` |

---

## 2. 维度裁决汇总

| 维  | 报告                          | 裁决     | findings |
| --- | ----------------------------- | -------- | -------- |
| A1  | `research/audit-a1-report.md` | **fail** | 1        |
| A2  | `research/audit-a2-report.md` | **fail** | 3        |
| A3  | `research/audit-a3-report.md` | **pass** | 0        |
| A4  | `research/audit-a4-report.md` | **fail** | 5        |
| A5  | `research/audit-a5-report.md` | **fail** | 2        |
| A6  | `research/audit-a6-report.md` | **skip** | 0        |
| A7  | `research/audit-a7-report.md` | **pass** | 0        |
| A8  | `research/audit-a8-report.md` | **fail** | 3        |

**合计：** 14 findings（去重根因后 12 项修复）· 3 维 pass · 1 维 skip · 4 维 fail

---

## 4. 风险与结论（A9）

### 4.1 Findings 合并

| ID        | P   | 维度     | 标题                                    | 锚点                                                                                     | 根因                                                                                                                      | 修复方案                                                             | 验证                                          |
| --------- | --- | -------- | --------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | --------------------------------------------- |
| A5-P1-001 | P1  | A5/A1/A8 | D-05 gate 仍查 R1 证据路径              | `validate_audit_handoff.py` L255–264 · `test_validateRepairClose_mData03SpotChecks_pass` | R2 证据迁至 `archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`；gate 硬编码 `l4-tier-a-live-accept-evidence.md` | 更新 D-05 读 `evidence_index.json` 或 R2 路径；断言 `11/11`/`exit 0` | `uv run pytest -q` exit 0                     |
| A4-P1-001 | P1  | A4       | `--report` 缺 zero-clean/raw 守卫       | `tier_a_live_acceptance.py` `_process_source_for_report` vs `run_source_live_acceptance` | gate 逻辑未复用；CLI 与 report 双轨                                                                                       | 提取共享 gate；`_process_source_for_report` 复用                     | `test_reportRun_plannedWithZeroCleanFails` 绿 |
| A4-P2-001 | P2  | A4       | 双 acceptance pipeline 分叉             | `run_acceptance` vs `run_acceptance_report`                                              | 独立编排、gate 顺序不一致                                                                                                 | 单一 pipeline 函数两入口包装                                         | 现有 tier-a 测仍绿                            |
| A4-P2-002 | P2  | A4       | FAIL_EXTERNAL / adr_ref 未接入          | `classify_source_report_failure` · contract exit_codes                                   | 仅 PASS/FAIL_FIXABLE；`adr_ref` 恒 None                                                                                   | 按 contract 映射或修订契约+测                                        | 对应单测绿                                    |
| A4-P2-003 | P2  | A4       | manifest fetch 子结构无契约测           | `test_live_tier_a_evidence_contract.py`                                                  | 仅顶层字段；fetch 七字段缺位无 RED                                                                                        | 补 parametrize fetch 字段测                                          | contract 测绿                                 |
| A8-P2-001 | P2  | A8       | tier-a-live workflow 无 manifest pytest | `.github/workflows/tier-a-live.yml`                                                      | 无 `test_tier_a_live_ci_manifest.py` 对照 nightly                                                                         | 新增 manifest 测                                                     | pytest 绿                                     |
| A1-P2-001 | P2  | A1       | R2 证据路径未下沉 D-05（同 A5-P1-001）  | 同上                                                                                     | 同 A5-P1-001                                                                                                              | 同 A5-P1-001                                                         | 同 A5-P1-001                                  |
| A5-P2-001 | P2  | A5       | 旧 ledger 自述 pytest 全绿              | `audit-repair-ledger.md`                                                                 | 无效单 agent Audit 产物                                                                                                   | Repair 关账时按实据更新                                              | ledger 与 pytest 一致                         |
| A8-P1-001 | P1  | A8       | 全量 pytest 非绿（同 A5-P1-001）        | 同上                                                                                     | 同 A5-P1-001                                                                                                              | 同 A5-P1-001                                                         | 同 A5-P1-001                                  |
| A8-P3-001 | P3  | A8       | FAIL_EXTERNAL+ADR exit 0 无 prove-it    | contract L237–239                                                                        | 实现与契约未对齐                                                                                                          | 实现或修订契约+测                                                    | pytest 绿                                     |
| A2-P3-001 | P3  | A2       | port bootstrap 未收敛泛型               | `alpha_vantage/cninfo/sec_edgar_incremental_support.py`                                  | 未复用 `bootstrap_port_live_e2e_ctx`                                                                                      | 薄包装调用泛型                                                       | e2e 测绿                                      |
| A2-P3-002 | P3  | A2       | F0 lineage helper 重复                  | `data_health_profiles/__init__.py` · `evidence_loader.py`                                | 两处相同 helper                                                                                                           | SSOT 一处 import                                                     | `test_data_health_tier_a_profiles.py` 绿      |
| A2-P3-003 | P3  | A2       | `tier_a_live_status` 死常量             | `tier_a_live_status.py`                                                                  | 无消费方                                                                                                                  | 删除                                                                 | rg 零命中                                     |
| A4-P3-001 | P3  | A4       | fetch.schema_hash 占位无 ponytail       | `tier_a_live_acceptance.py` ~447                                                         | `sha256(source_id)` 占位                                                                                                  | `ponytail:` 注释或真实 hash                                          | Read/单测                                     |

### 4.2 结论

- [x] **PASS** — Repair 关账 14/14 已修复；`validate-repair-close` exit 0

### 4.3 修复项

全部见 `research/audit-repair-ledger.md`（disposition = **已修复**）。

### 4.4 阶段外置

| ID                             | 源                                 | disposition            | 登记                                                                         |
| ------------------------------ | ---------------------------------- | ---------------------- | ---------------------------------------------------------------------------- |
| `M-DATA-03-STOOQ-EXTERNAL-001` | stooq                              | **路径二已接受**       | ADR-034 §Tier B · `待修复清单.md` §8 · `tier-b-network-path2-evidence.md` §3 |
| `M-DATA-03-TIERB-CN-HIST-001`  | akshare / eastmoney / sina_finance | **条件路径二（开放）** | `待修复清单.md` §8 · `tier-b-network-path2-evidence.md` §4 · ROADMAP §3.1.1  |

---

## 5. Repair 复验（2026-07-03 关账）

| 项                             | 结果                                                        | 证据                                          |
| ------------------------------ | ----------------------------------------------------------- | --------------------------------------------- |
| §4.3 全部关闭                  | **已修复**（14/14）                                         | `research/audit-repair-ledger.md`             |
| `uv run pytest -q` exit 0      | **pass**                                                    | Repair 全量 pytest                            |
| `validate-repair-close` exit 0 | **pass**                                                    | D-05 R2 `evidence_index.json` accept_evidence |
| 根因修复                       | D-05 R2 路径 · 共享 pipeline · external+ADR · ponytail 清理 | 见 ledger 登记位置列                          |

**总裁决：PASS**
