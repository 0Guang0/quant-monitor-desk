# Audit A8 — Test Gap（M-DATA-03 Plan R2）

## 元信息

| 字段                    | 值                                                       |
| ----------------------- | -------------------------------------------------------- |
| 维度                    | A8 — qa-expert / test-gap                                |
| 任务                    | `.trellis/tasks/m-data-03-tier-a-live`                   |
| `plan_protocol_version` | 4.1                                                      |
| 模板                    | `agents/qa-expert.md` · `agents/audit-finding-schema.md` |
| 审计日期                | 2026-07-03                                               |
| 分支                    | `feature/m-data-03-tier-a-live`                          |

## 维度证据 §3.8

### 独立复验命令

| 命令                                                                                                                                                                                                                                                              | exit code | 备注                                                            |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | --------------------------------------------------------------- |
| `uv run pytest -q`                                                                                                                                                                                                                                                | **1**     | 1 failed · ~326s · 2026-07-03 Audit A8 独立跑                   |
| `uv run pytest tests/test_tier_a_live_acceptance_report.py tests/test_tier_a_live_b2_acceptance.py tests/test_tier_a_live_dispatch.py tests/test_tier_a_live_harness.py tests/test_live_tier_a_evidence_contract.py tests/test_data_health_tier_a_profiles.py -q` | **0**     | 101 passed · 2 skipped（network mark · canonical main DB 缺席） |

**失败用例：**

```text
FAILED tests/test_validate_audit_handoff.py::test_validateRepairClose_mData03SpotChecks_pass
AssertionError: ['D-05 spot-check: missing research/l4-tier-a-live-accept-evidence.md'] == []
```

### Checklist（AUDIT.plan §2 A8 · to-issues-slices 建议测试）

| #   | 检查项                                                                   | 裁决         | 证据                                                                                         |
| --- | ------------------------------------------------------------------------ | ------------ | -------------------------------------------------------------------------------------------- |
| 1   | `plan-revision-r2.md` §2#8：`uv run pytest -q` exit 0                    | **FAIL**     | 全量 pytest exit **1**（上表）                                                               |
| 2   | contract `required_tests` 三模块                                         | PASS         | `live_tier_a_evidence_v1.yaml` L270–273 · `test_catalog.yaml` 登记                           |
| 3   | S-R2-EVIDENCE：`test_live_tier_a_evidence_contract.py`                   | PASS         | 11 bindings · failure_class mapping                                                          |
| 4   | S-R2-ACCEPT：`test_tier_a_live_acceptance_report.py`                     | PASS         | 11 manifest · E2 非 FAIL · failure artifact                                                  |
| 5   | S-R2-B2：`test_tier_a_live_b2_acceptance.py`                             | PASS         | `test_reportRun_setsB2ValidationStatusForElevenSources`                                      |
| 6   | S-R2-F0：`test_data_health_tier_a_profiles.py`                           | PASS         | 四族 profile · `test_runF0DataHealth_failsWhenNoRawEvidence`                                 |
| 7   | S-R2-DISPATCH：`test_tier_a_live_dispatch.py`                            | PASS         | 去重 · mootdx · F0 fail 阻断                                                                 |
| 8   | harness / env gate：`test_tier_a_live_harness.py`                        | PASS         | 隔离根 · KEY 校验 · exit 2/1                                                                 |
| 9   | 五字段 docstring（tier-a 模块）                                          | PASS         | spot-check `test_tier_a_live_*.py` · `test_live_tier_a_evidence_contract.py`                 |
| 10  | failure artifact 写出                                                    | PASS         | `test_reportRun_writesFailureArtifactOnFixableFail` · contract `filename_pattern` 一致       |
| 11  | CI workflow 存在 + artifact 路径                                         | PASS（文件） | `.github/workflows/tier-a-live.yml` L46–54 glob 对齐 `tier_a_live_acceptance_failure_*.json` |
| 12  | CI workflow **pytest 清单测**（对照 `test_nightly_ci_manifest.py` 模式） | **FAIL**     | 全仓 `tests/` 无 `tier-a-live.yml` 引用                                                      |
| 13  | D-05 Repair 关账 spot-check 与 R2 证据路径一致                           | **FAIL**     | gate 仍查 R1 `research/l4-tier-a-live-accept-evidence.md`                                    |

### GitNexus

| 操作                                                                                 | 结果                                                                                |
| ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| `query(tier_a_live_acceptance CI workflow failure artifact)` repo=quant-monitor-desk | 邻域命中 live_pilot / production_gate；未直接索引 tier-a CI 测                      |
| 处置                                                                                 | 以 **pytest 跑测 + Read workflow/yaml** 为准（与 `gitnexus-audit-summary.md` 一致） |

### S-R2-CI workflow 静态核对（非 pytest）

| AC 子项                   | tier-a-live.yml                                                                              | 符合 |
| ------------------------- | -------------------------------------------------------------------------------------------- | ---- |
| nightly `--quick`         | L4–5 `schedule` + L42–43 `schedule \|\| inputs.quick` → `--quick`                            | 是   |
| `workflow_dispatch`       | L6–11 + `quick` input default false                                                          | 是   |
| 失败上传 failure artifact | L46–54 `if: failure()` · glob `tier_a_live_acceptance_failure_*.json` + `tier-a-report.json` | 是   |
| isolated `data_root`      | L38 `DATA_ROOT=".audit-sandbox/m-data-03/${RUN_ID}"`                                         | 是   |

## §维度裁决

**FAIL**

## 计划内问题

| ID        | P   | 标题                           | 锚点                                                                                                                                   | 根因                                                                                                                                                                                                                                                                    | 修复方案                                                                                                                                                                             | 验证                                                                                                                                       |
| --------- | --- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| A8-P1-001 | P1  | 全量 pytest 非绿，违反 R2 AC#8 | `plan-revision-r2.md` §2#8 · `AUDIT.plan.md` §2 A8 · `test_validate_audit_handoff.py::test_validateRepairClose_mData03SpotChecks_pass` | `validate_audit_handoff._spot_check_m_data_03_repair_close`（L255–264）仍要求 R1 路径 `research/l4-tier-a-live-accept-evidence.md`；R2 证据已迁至 `research/archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`；`audit-repair-ledger.md` 存在使 D-05 gate 激活 | 更新 `.trellis/scripts/common/validate_audit_handoff.py` D-05 锚点为 R2 证据路径及内容校验（`exit 0` / `11` 源等）；同步 `test_validateRepairClose_mData03SpotChecks_pass` docstring | `uv run pytest -q` exit 0；`uv run pytest tests/test_validate_audit_handoff.py::test_validateRepairClose_mData03SpotChecks_pass -q` exit 0 |

## 计划外发现

| ID        | P   | 标题                                                  | 锚点                                                                                                                                   | 根因                                                                                                                                                                | 修复方案                                                                                                                                                                                                                                            | 验证                                                            |
| --------- | --- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| A8-P2-001 | P2  | tier-a-live CI workflow 无 manifest pytest            | `live_tier_a_evidence_v1.yaml` `failure_artifact.ci_upload` · `to-issues-slices.md` S-R2-CI · 对照 `tests/test_nightly_ci_manifest.py` | R2 新增 `.github/workflows/tier-a-live.yml` 但无等价清单测；`workflow_dispatch` / schedule `--quick` / artifact glob 漂移无法被 CI 内 pytest 捕获                   | 新增 `tests/test_tier_a_live_ci_manifest.py`（或扩展现有 manifest 测）：断言 `workflow_dispatch`、`schedule`、`--quick` 条件、`upload-artifact` path 含 `tier_a_live_acceptance_failure_*.json` 与 `tier-a-report.json`；`loop_maintain --fix` 登记 | `uv run pytest tests/test_tier_a_live_ci_manifest.py -q` exit 0 |
| A8-P3-001 | P3  | contract `exit_codes` FAIL_EXTERNAL+ADR 分支无 pytest | `live_tier_a_evidence_v1.yaml` L237–239 · `tier_a_live_acceptance.py` `run_acceptance_report` L653–660                                 | 契约声明 exit 0 当「全 FAIL_EXTERNAL 且 merged ADR」；实现凡 `failed_external>0` 即 exit 1；`classify_source_report_failure` 未产出 `FAIL_EXTERNAL`；无 prove-it 测 | 若保留契约语义：实现 ADR merge 判定并补 `test_reportRun_exit0WhenAllExternalWithAdr`；若 R2 口径为 11/11 无 ADR 例外：修订契约 exit_codes 并补回归测证明当前 fail-closed 行为                                                                       | 选定方案后对应 pytest 绿 + contract/ADR 一致                    |

已对抗搜索：`tests/test_tier_a_live_*.py` · `tests/test_live_tier_a_evidence_contract.py` · `tests/test_data_health_tier_a_profiles.py` · `tests/test_nightly_ci_manifest.py` · `tests/test_validate_audit_handoff.py` · `.github/workflows/tier-a-live.yml` · `rg tier-a-live\.yml tests/` · `rg FAIL_EXTERNAL tests/` · GitNexus query · 全量 + tier-a 子集 pytest 独立复跑。
