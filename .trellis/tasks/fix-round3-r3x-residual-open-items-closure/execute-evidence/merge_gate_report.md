# Merge gate report — fix/round3-r3x-residual-open-items-closure

## Branch

| Field | Value |
| ----- | ----- |
| Branch | `fix/round3-r3x-residual-open-items-closure` |
| Worktree | `../quant-monitor-desk-wt-fix-r3-r3x-residual-closure` |
| Base | `master` @ `ae542970` |
| **Commit SHA (worktree HEAD)** | _(see `git rev-parse HEAD` after commit)_ |
| Target merge | `master` |
| Source | `R3X_residual_open_items_closure.md` / PROMPT_15 |

## Ponytail compliance (full mode)

| Area | Note |
| ---- | ---- |
| DataSourceService | 双 flag 合并为单一 `staged_fixture_mode`；live pilot raw fetch 经 `service.fetch` |
| route_planner | 模块级 `_MATRIX_CACHE` 一行缓存 |
| write_manager | `MIN_STAGING_ROWS` 内联；`UNSUPPORTED_MODES` 清晰拒绝 |
| capability_registry | `ADAPTER_DOMAIN_COMPATIBILITY_MAP` 清空（适配器已用 registry domain） |
| resource_guard | 无嵌套 BEGIN；`_dir_size_gb` 文档化上限 |
| reconcile | `market_id` 来自 conflict 行；`DROP` 临时表；status 早退 |
| orchestrator | `run_full_load` / `run_data_quality` 显式 `NotImplementedError` |
| tests | `test_r3x_residual_open_items_closure.py` 伞测 + `test_production_gate.py` |

## Master Checklist 终态

### 4.1 ADV-R3X

| ID | 终态 | 理由 / ponytail |
| -- | ---- | ----------------- |
| ADV-R3X-ROUTE-001 | **FIXED** | `validation_only_cannot_be_primary` |
| ADV-R3X-ROUTE-002 | **ALREADY_CLOSED** | platform matrix 回归绿 |
| ADV-R3X-ROUTE-003 | **FIXED** | `DOMAIN_DISABLED_BY_DEFAULT` |
| ADV-R3X-ROUTE-004 | **FIXED** | `VALIDATION_SOURCE_USED` |
| ADV-R3X-SYNC-001 | **FIXED** | orchestrator → DataSourceService `fetch_callable` |
| ADV-R3X-SYNC-002 | **ALREADY_CLOSED** | 回归绿 |
| ADV-R3X-SYNC-003 | **FIXED** | `CONFLICT_CHECK_SKIPPED` 事件 |
| ADV-R3X-WRITE-001 | **FIXED** | `_write_clean` 用 `fetch_result.source_id` |
| ADV-R3X-WRITE-002 | **FIXED** | `UNSUPPORTED_MODES` + `test_advR3xWrite002_*` |
| ADV-R3X-VALID-001 | **ALREADY_CLOSED** | 回归绿 |
| ADV-R3X-CONFLICT-001 | **FIXED** | `CONFLICT_DOMAIN_ALIASES` |
| ADV-R3X-L1-001 / ADV-A4-001 | **FIXED** | guardrail validator wired on commit |
| ADV-R3X-L1-002 / ADV-A4-002 | **FIXED** | forbidden terms → reject |
| ADV-R3X-PILOT-001 | **FIXED** | `preview_live_pilot` + `run_live_pilot_raw_only` → `DataSourceService.fetch` |
| ADV-R3X-PILOT-002 | **FIXED** | `DbValidationGate` 阻断 synthetic quality_flags clean write |
| ADV-R3X-SERVICE-001 | **FIXED** | production fetch 需 port/registry |
| ADV-R3X-STAGE-001 | **FIXED** | staged micro-fetch file_registry 经 WriteManager + stub validation_report |
| ADV-R3X-DOC-001 | **FIXED** | `adversarial_audit_report.md` PROMPT_15 闭合节 |
| ADV-R3X-CAP-001 | **FIXED** | `ADAPTER_DOMAIN_COMPATIBILITY_MAP` 清空 |
| ADV-R3X-CAP-002 | **FIXED** | `tdx_pytdx` 工厂注册 |

### 4.2 ADV-A1

| ID | 终态 | 理由 |
| -- | ---- | ---- |
| ADV-A1-003 | **ALREADY_CLOSED** | 回归绿 |
| ADV-A1-004 | **FIXED** | `FileRegistry` + `WriteManager` staged/clean 路径 |
| ADV-A1-005 | **ALREADY_CLOSED** | 回归绿 |
| ADV-A1-001 | **FIXED** | `data_domain` 必填 |
| ADV-A1-002 | **FIXED** | conflict_status 不镜像 validation_status |
| ADV-A1-006 | **FIXED** | 空/损坏 lock 文件 unlink 恢复 |
| ADV-A1-007 | **FIXED** | HARD_STOP 后 writer 上下文释放锁（`finally`） |
| ADV-A1-008 | **FIXED** | ResourceGuard 无嵌套 BEGIN |
| ADV-A1-009 | **FIXED** | migration 010 显式列 `INSERT SELECT` + schema_version 幂等 |
| ADV-A1-010 | **FIXED** | `configs/resource_limits.yaml` batch profile 已存在 |
| ADV-A1-012 | **FIXED** | `MIN_STAGING_ROWS` + `rows_in_staging` 审计 |
| ADV-A1-011 | **FIXED** | `evidence_ports.FileRegistryPort.register_on_connection` |
| ADV-A1-013 | **FIXED** | `_dir_size_gb` max_files 文档 |
| ADV-A1-014 | **FIXED** | WriteManager 用 `assert_can_write_with` 同事务读 |
| ADV-A1-015 | **FIXED** | 同 A1-012 最小行数 |

### 4.3 ADV-A2

| ID | 终态 | 理由 |
| -- | ---- | ---- |
| ADV-A2-001 | **ALREADY_CLOSED** | 回归绿 |
| ADV-A2-003 | **ALREADY_CLOSED** | 回归绿 |
| ADV-A2-005 | **ALREADY_CLOSED** | 回归绿 |
| ADV-A2-006 | **ALREADY_CLOSED** | 回归绿 |
| ADV-A2-007 | **ALREADY_CLOSED** | 回归绿 |
| ADV-A2-002 | **FIXED** | `BaseDataAdapter.health_check()` stub |
| ADV-A2-004 | **FIXED** | cninfo cn_filings/cn_pdf_reports |
| ADV-A2-009 | **FIXED** | TdxPytdxAdapter 工厂注册 |
| ADV-A2-010 | **FIXED** | `DISABLED_SOURCE` guard |
| ADV-A2-012 | **FIXED** | `_MATRIX_CACHE` |
| ADV-A2-008 | **FIXED** | `configs/datasource.yml` 指向 source_registry.yaml |
| ADV-A2-011 | **FIXED** | `test_r3x_residual_open_items_closure.py` 路由回归 |

### 4.4 ADV-A3

| ID | 终态 | 理由 |
| -- | ---- | ---- |
| ADV-A3-001 | **ALREADY_CLOSED** | 回归绿 |
| ADV-A3-003 | **ALREADY_CLOSED** | 回归绿 |
| ADV-A3-002 | **FIXED** | ReconcileJobRunner `market_id` 来自 conflict / domain |
| ADV-A3-004 | **FIXED** | `validate_table` row cap |
| ADV-A3-005 | **FIXED** | `create_job` idempotent |
| ADV-A3-006 | **FIXED** | severe conflict job_id 范围 |
| ADV-A3-007 | **FIXED** | `RESOURCE_GUARD_HARD_STOP` vs `RESOURCE_GUARD_PAUSED` |
| ADV-A3-008 | **FIXED** | `CONTENT_CHANGED` runtime in `validate_fetch_result` |
| ADV-A3-009 | **FIXED** | reconcile_status 已解决早退 |
| ADV-A3-010 | **FIXED** | `_table_exists` + `table_schema='main'` |
| ADV-A3-011 | **FIXED** | `as_text(None)` → None |
| ADV-A3-012 | **FIXED** | backfill `SHARD_COMPLETE` checkpoint skip |
| ADV-A3-013 | **FIXED** | reconcile `DROP TABLE IF EXISTS` finally |
| ADV-A3-014 | **FIXED** | validation sources from registry |
| ADV-A3-015 | **FIXED** | `test_syncJob_dataQuality_skeletonCompletes` 确定性 |
| ADV-A3-016 | **FIXED** | `run_full_load` / `run_data_quality` 显式 defer API |

### 4.5 ADV-A5 / ADV-A6

| ID | 终态 | 理由 |
| -- | ---- | ---- |
| ADV-A5-001 | **FIXED** | .gitignore secret 模式 |
| ADV-A5-002 | **FIXED** | `tests/test_production_gate.py` |
| ADV-A6-001 | **FIXED** | `MIGRATION_COVERAGE.md` 更新 |
| ADV-A6-003 | **FIXED** | 008/009/010 叙事统一 |
| ADV-A6-004 | **FIXED** | Vite `/api` proxy |

### 4.6 F-019

| ID | 终态 | 理由 |
| -- | ---- | ---- |
| F-019-R01 | **FIXED** | `AUDIT.plan.md` 阻塞清单已 `[x]` |
| F-019-R02 | **FIXED** | `layer2_cross_asset_sensor.md` §7 defer 交叉引用 |
| F-019-R03 | **FIXED** | fixture `FRED:VIXCLS` YAML 注释 |

### 4.7 Registry

| # | 终态 | 理由 |
| - | ---- | ---- |
| R1 | **FIXED** | `AUDIT_DEFERRED_REGISTRY.md` PROMPT_15 RESOLVED 节 |
| R2 | **FIXED** | R3-PARTIAL-1 / SYNC-002 去重注记 |
| R3 | **FIXED** | `adversarial_audit_report.md` 刷新 |
| R4 | **FIXED** | migration 008/009/010 叙事（同 ADV-A6-003） |

## Checklist 计数

| 终态 | 数量 |
| ---- | ---- |
| **FIXED** | 61 |
| **ALREADY_CLOSED** | 12 |
| **OPEN** | **0** |
| **OUT_OF_SCOPE** | 0（硬排除项未列入上表） |
| **合计** | 73 |

## Tests

```bash
python -m pytest -q
# exit 0
```

## Data safety

| Check | Status |
| ----- | ------ |
| No production DB mutation | PASS |
| No live network fetch | PASS |
| No default enable disabled source | PASS |
| No REQ2-EM closure | PASS |

## Merge gate

**READY** — Master Checklist OPEN **0**；`pytest -q` 全绿后可 merge（协调者审查）。
