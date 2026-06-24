# Repair/Debt Lite Plan — fix/r3y-staged-registry-privatize (β-2)

## Source of truth

| 项            | 值                                                                 |
| ------------- | ------------------------------------------------------------------ |
| Registry ID   | `R3Y-STAGED-REG-001`                                               |
| Audit         | `R3Y-AUD-03` WARN · `docs/quality/adversarial_audit_report.md`     |
| Map slice     | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2 β-2 row                 |
| base branch   | `master` @ `68b10982`                                              |
| target branch | `fix/r3y-staged-registry-privatize`                                |
| worktree      | `../quant-monitor-desk-wt-fix-r3y-staged-reg`                      |
| owner agent   | fix-agent-r3y-staged-reg                                           |
| Trellis track | `debt-lite`                                                        |

## Authority index (playbook §3.1 + §3.5)

### §3.1 共用底座

| 路径                                                          | 摘要                                       |
| ------------------------------------------------------------- | ------------------------------------------ |
| `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md`                 | Wave C PASS、§8.4、测试五字段、composer-2.5 |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2–§2.6                | β-2 allowed/forbidden、验证命令            |
| `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` §6 | 一分支一核心文件组                         |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                             | R3Y defer 只读                             |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                          | `R3Y-STAGED-REG-001` OPEN                  |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                            | 防重复打开                                 |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`  | ID → β-2 分支                              |
| `docs/ROUND3_HANDOFF.md`                                      | staged-only 语境                           |
| `docs/quality/staged_acceptance_policy.md`                    | 分阶段验收                                 |
| `docs/quality/production_live_pilot_policy.md`                | 不得声称 production-live                   |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`               | Batch 3 下游门禁                           |
| `docs/quality/ROUND3_TEST_DOCSTRING_HYGIENE_PLAN.md`          | 五字段 docstring                           |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`         | docs/specs 非实现路径                      |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`          | 语义测试                                   |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`       | ResourceGuard                              |
| `specs/contracts/runtime_versions.md`                         | 工具链权威                                 |
| `specs/contracts/write_contract.yaml`                         | 写路径与 staging 合约                      |
| `specs/contracts/resource_limits.yaml`                        | 资源上限                                   |
| `specs/contracts/snapshot_lineage_contract.yaml`              | metadata-only 边界                         |
| `docs/architecture/module_boundary_matrix.md`                 | 模块边界                                   |
| `MIGRATION_MAP.md`                                            | 实现目录映射                               |

### §3.5 β-2 专属

| 路径                                                                               | 摘要                                  |
| ---------------------------------------------------------------------------------- | ------------------------------------- |
| `docs/modules/write_manager.md`                                                    | §4 禁止旁路写 file_registry           |
| `docs/modules/local_file_system.md`                                                | raw/staging 与 file_registry 语义     |
| `docs/modules/duckdb_and_parquet.md`                                               | staging vs clean 边界                 |
| `docs/quality/adversarial_audit_report.md`                                         | AUD-03 WARN 来源                      |
| `docs/implementation_tasks/ROUND_1_DATA_FOUNDATION/008_implement_write_manager.md` | WriteManager 任务口径                 |
| `docs/quality/ROUND3_WAVE_B_PENDING_FIX_REGISTRY.md` §2                            | `R3Y-STAGED-REG-001` 台账             |
| `specs/contracts/write_contract.yaml`                                              | metadata-only gate 合约               |
| `specs/contracts/snapshot_lineage_contract.yaml`                                   | lineage metadata-only 策略边界        |

**实现邻接（只读对照）：** `backend/app/db/write_manager.py` · `backend/app/ops/staged_pilot.py` · `tests/test_staged_pilot.py` · `tests/test_write_manager.py`

## Boundary

**Allowed files**

- `backend/app/storage/staged_evidence.py`
- `tests/test_staged_pilot.py`, `tests/test_raw_store.py`（MAP 聚焦 storage/staged 测试）
- `tests/test_r3x_ponytail_pilot_prep_bucket_a.py`（import 对齐；略超 MAP，见对抗性审计 AA-03）
- `.trellis/tasks/fix-r3y-staged-registry-privatize/**`

**Forbidden files**

- `backend/app/ops/**`, `backend/app/layer4_markets/**`
- registry trio（主会话 Wave C 合并后批处理）

**Explicit non-goals**

- 不删除私有 legacy INSERT（测试回归 path sandbox + phase token）
- 不将 Phase 3 micro-fetch 改为 WriteManager（production staged pilot 已走 WriteManager）

## Vertical slices

| Slice | AC                                                                                      | Evidence                          |
| ----- | --------------------------------------------------------------------------------------- | --------------------------------- |
| β2-1  | `register_staged_file_registry_rows` → `_register_staged_file_registry_rows` + `__all__` | `β2-red.txt` / `β2-green.txt`     |
| β2-2  | metadata-only 策略模块注释 + docstring                                                  | `staged_evidence.py` L15–21, L49–54 |
| β2-3  | 公开旁路守卫 + phase 门禁 pytest                                                        | `test_raw_store.py` 新增/更新测   |
| β2-4  | `test_staged_pilot` WriteManager 路径仍绿                                               | merge gate                        |
| β2-5  | bucket_a SC-02 import 对齐                                                              | `test_r3x_ponytail_pilot_prep_bucket_a.py` |

## Merge gate

```bash
uv run pytest tests/test_staged_pilot.py tests/test_raw_store.py -q
uv run pytest -q
```

**Evidence:** `execute-evidence/merge_gate_report.md` · `β2-red.txt` · `β2-green.txt` · `full-pytest-green.txt`

**Registry:** 本分支 PR **不改** registry 三件套；`R3Y-STAGED-REG-001` CLOSED 行由主会话合并后批处理。
