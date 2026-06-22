# R3X_residual_open_items_closure — 当前阶段可修复项全量闭合

## 1. 任务性质

**零遗漏闭合任务。** 在 PROMPT_11–13 已合入 `master` @ `ae542970` 之后，修复当前 staged-only 阶段**能够修复**的全部对抗性审计、019 审查、registry 协调遗留项——**无论是否为 pilot/production-live 阻塞项**。

本任务不是 production-live 启用任务，不关闭 `R3-B2.75-REQ2-EM`，不做 live 网络 fetch，不写 production DB，不默认启用 disabled source。

## 2. 分支与工作方式

| Field        | Value                                                                                                  |
| ------------ | ------------------------------------------------------------------------------------------------------ |
| Branch       | `fix/round3-r3x-residual-open-items-closure`                                                           |
| Base         | `master` @ `ae542970`（或协调者确认的最新 `master`）                                                   |
| Worktree     | `../quant-monitor-desk-wt-fix-r3-r3x-residual-closure`                                                 |
| Target merge | `master`                                                                                               |
| Source       | PROMPT_11 merge_gate + `docs/quality/adversarial_audit_report.md` + PROMPT_12/13 deferred + 019 review |

**工作方式：** TDD（RED → evidence → GREEN）逐项闭合；**全程 `/ponytail` full**（最短可用 diff、stdlib 优先、禁止未请求抽象、已写代码若过度工程须 refactor down）；`merge_gate_report.md` 必须包含下方 **Master Checklist** 每一行的最终状态（`FIXED` / `ALREADY_CLOSED` / `OUT_OF_SCOPE` + 理由）。

## 3. 硬排除（不得声称修复）

| ID / 主题                                         | 原因                                                                                                            |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `R3-B2.75-REQ2-EM`                                | 用户/协调者硬约束：不得关闭 Eastmoney hist Request 2                                                            |
| production-live readiness                         | 政策门仍 BLOCKED                                                                                                |
| live network / TDX / QMT / xqshare 默认启用       | `R2.6-IMPL-8`                                                                                                   |
| PROMPT_14 完整 staged pilot                       | 需用户显式 live 授权，另开分支                                                                                  |
| `ADV-R3X-LINEAGE-001` L3/L4 完整 snapshot lineage | 属 formal `020`–`022` Batch 4/5；本任务仅允许文档/registry 登记 defer 至对应 batch，**不得**假装已实现 Layer3/4 |
| `R3-REF-OPS-DB-DATA-HEALTH` 完整 CLI              | Batch 6 范围；若仅 doc cross-ref 可修                                                                           |
| Round 4+ API / frontend 大特性                    | 超出 Round 3 staged 阶段                                                                                        |

## 4. Master Checklist（必须 100% 行有终态）

> **已 CLOSED（PROMPT_12/13）：** 执行前验证仍成立；若回归则重新打开并修复。  
> 标记 `→ FIX` 的项必须在本次分支闭合。

### 4.1 ADV-R3X（PROMPT_11 对抗审计）

| ID                          | Sev  | 状态基线   | 要求                                                                                      |
| --------------------------- | ---- | ---------- | ----------------------------------------------------------------------------------------- |
| ADV-R3X-ROUTE-001           | HIGH | OPEN → FIX | `validation_only` 源不得作唯一 READY Primary；route planner 读 registry `validation_only` |
| ADV-R3X-ROUTE-002           | HIGH | CLOSED@12  | 验证 cninfo/yahoo/tdx 在 platform matrix；回归则修                                        |
| ADV-R3X-ROUTE-003           | MED  | OPEN → FIX | enforce `domain_enabled_by_default`                                                       |
| ADV-R3X-ROUTE-004           | MED  | OPEN → FIX | Validation 角色选中时 quality_flags                                                       |
| ADV-R3X-SYNC-001            | HIGH | OPEN → FIX | sync runners 经 DataSourceService，禁止裸 adapter.fetch 旁路                              |
| ADV-R3X-SYNC-002            | HIGH | CLOSED@13  | backfill severe conflict；回归则修                                                        |
| ADV-R3X-SYNC-003            | MED  | OPEN → FIX | `conflict_staging_table=None` 时 fail-closed 或显式 skip 审计                             |
| ADV-R3X-WRITE-001           | HIGH | OPEN → FIX | clean write `source_used` 来自实际 fetch/route，非硬编码 spec.source_id                   |
| ADV-R3X-WRITE-002           | MED  | OPEN → FIX | `write_mode` 合约未实现部分（dup R2-RISK-3）最小实现或 registry 对齐                      |
| ADV-R3X-VALID-001           | HIGH | CLOSED@13  | schema_hash gate；回归则修                                                                |
| ADV-R3X-CONFLICT-001        | HIGH | OPEN → FIX | conflict 阈值域名 alias（`cn_equity_daily_bar` ↔ `market_bar_1d` 等）                     |
| ADV-R3X-L1-001 / ADV-A4-001 | HIGH | OPEN → FIX | wire `AxisEngineeringGuardrailValidator` 到 ingestion commit                              |
| ADV-R3X-L1-002 / ADV-A4-002 | HIGH | OPEN → FIX | 禁止操作词 default 路径 reject 非 replace                                                 |
| ADV-R3X-PILOT-001           | MED  | OPEN → FIX | `live_pilot` 经 DataSourceService 或等价 route audit                                      |
| ADV-R3X-PILOT-002           | MED  | OPEN → FIX | sandbox pilot 合成 validation_report 不得绕过 gate 写 clean                               |
| ADV-R3X-SERVICE-001         | MED  | OPEN → FIX | `file_registry_factory=None` 不得静默落 test adapter                                      |
| ADV-R3X-STAGE-001           | MED  | PARTIAL@13 | 完成 WriteManager 路由或 stub validation report + gate（消除旁路）                        |
| ADV-R3X-DOC-001             | LOW  | OPEN → FIX | 刷新 `adversarial_audit_report.md` Layer2/019 上下文                                      |
| ADV-R3X-CAP-001             | LOW  | OPEN → FIX | 清理 ADAPTER_DOMAIN_COMPATIBILITY_MAP 双轨                                                |
| ADV-R3X-CAP-002             | LOW  | OPEN → FIX | tdx_pytdx runtime assert 测试对齐 qmt_xqshare                                             |

### 4.2 ADV-A1 存储/写入（adversarial report）

| ID         | Sev  | 状态基线   | 要求                                                       |
| ---------- | ---- | ---------- | ---------------------------------------------------------- |
| ADV-A1-003 | HIGH | CLOSED@13  | 回归验证                                                   |
| ADV-A1-004 | HIGH | PARTIAL@13 | 完成 WriteManager 路由或等价 gate（非仅 path containment） |
| ADV-A1-005 | HIGH | CLOSED@13  | 回归验证                                                   |
| ADV-A1-001 | MED  | OPEN → FIX | WriteRequest `data_domain` 必填校验                        |
| ADV-A1-002 | MED  | OPEN → FIX | write_audit conflict_status 不镜像 validation_status       |
| ADV-A1-006 | MED  | OPEN → FIX | 锁文件 crash 恢复                                          |
| ADV-A1-007 | MED  | OPEN → FIX | ResourceGuard HARD_STOP 释放 write locks                   |
| ADV-A1-008 | MED  | OPEN → FIX | ResourceGuard 嵌套事务                                     |
| ADV-A1-009 | MED  | OPEN → FIX | migration 010 INSERT SELECT 重放风险                       |
| ADV-A1-010 | MED  | OPEN → FIX | resource_limits batch profile vs 合约                      |
| ADV-A1-012 | MED  | OPEN → FIX | Verify staging row count 步骤                              |
| ADV-A1-011 | LOW  | OPEN → FIX | evidence_ports protocol 对齐                               |
| ADV-A1-013 | LOW  | OPEN → FIX | \_dir_size_gb 截断文档或修正                               |
| ADV-A1-014 | LOW  | OPEN → FIX | validation gate stale read                                 |
| ADV-A1-015 | LOW  | OPEN → FIX | 最小 staging 行数验证                                      |

### 4.3 ADV-A2 数据源/路由

| ID         | Sev  | 状态基线   | 要求                                                                   |
| ---------- | ---- | ---------- | ---------------------------------------------------------------------- |
| ADV-A2-001 | HIGH | CLOSED@12  | 回归验证                                                               |
| ADV-A2-003 | HIGH | CLOSED@12  | 回归验证                                                               |
| ADV-A2-002 | MED  | OPEN → FIX | health_check 合约+基类 stub 或文档对齐                                 |
| ADV-A2-004 | MED  | OPEN → FIX | cninfo adapter 支持 cn_filings/cn_pdf_reports（fixture/stub，无 live） |
| ADV-A2-005 | MED  | CLOSED@12  | 回归验证                                                               |
| ADV-A2-006 | MED  | CLOSED@12  | 回归验证                                                               |
| ADV-A2-007 | MED  | CLOSED@12  | 回归验证                                                               |
| ADV-A2-009 | MED  | OPEN → FIX | TdxPytdxAdapter 工厂注册（保持 disabled-by-default）                   |
| ADV-A2-010 | MED  | OPEN → FIX | BaseDataAdapter guard 加强                                             |
| ADV-A2-012 | MED  | OPEN → FIX | platform matrix 缓存，避免每次 plan 读盘                               |
| ADV-A2-008 | LOW  | OPEN → FIX | 移除或文档化空 datasource.yml 存根                                     |
| ADV-A2-011 | LOW  | OPEN → FIX | 路由合约测试覆盖补全                                                   |

### 4.4 ADV-A3 同步/校验

| ID         | Sev  | 状态基线   | 要求                                                   |
| ---------- | ---- | ---------- | ------------------------------------------------------ |
| ADV-A3-001 | HIGH | CLOSED@13  | 回归验证                                               |
| ADV-A3-003 | HIGH | CLOSED@13  | 回归验证                                               |
| ADV-A3-002 | MED  | OPEN → FIX | ReconcileJobRunner market_id 非硬编码                  |
| ADV-A3-004 | MED  | OPEN → FIX | validate_table 分页边界                                |
| ADV-A3-005 | MED  | OPEN → FIX | 幂等键执行                                             |
| ADV-A3-006 | MED  | OPEN → FIX | severe conflict 范围 job_id                            |
| ADV-A3-007 | MED  | OPEN → FIX | HARD_STOP vs PAUSE 事件区分                            |
| ADV-A3-008 | MED  | OPEN → FIX | CONTENT_CHANGED runtime 路径                           |
| ADV-A3-009 | LOW  | OPEN → FIX | reconcile_status 检查                                  |
| ADV-A3-010 | LOW  | OPEN → FIX | \_table_exists quote_ident                             |
| ADV-A3-011 | LOW  | OPEN → FIX | as_text None 处理                                      |
| ADV-A3-012 | LOW  | OPEN → FIX | backfill checkpoint（最小）                            |
| ADV-A3-013 | LOW  | OPEN → FIX | reconcile 临时表清理                                   |
| ADV-A3-014 | LOW  | OPEN → FIX | validation sources 非硬编码二元组                      |
| ADV-A3-015 | LOW  | OPEN → FIX | test_sync_jobs 确定性                                  |
| ADV-A3-016 | LOW  | OPEN → FIX | orchestrator run_full_load / run_data_quality 显式 API |

### 4.5 ADV-A5 / ADV-A6 横切

| ID         | Sev | 要求                               |
| ---------- | --- | ---------------------------------- |
| ADV-A5-001 | MED | .gitignore secret 模式             |
| ADV-A5-002 | MED | production_gate.py 测试            |
| ADV-A6-001 | MED | MIGRATION_COVERAGE.md 更新         |
| ADV-A6-003 | MED | MIGRATION_008_PLAN vs 009 叙事统一 |
| ADV-A6-004 | MED | Vite dev proxy `/api/*`            |

### 4.6 019 审查遗留

| ID        | 要求                                                                       |
| --------- | -------------------------------------------------------------------------- |
| F-019-R01 | `.trellis/tasks/06-22-round3-019-layer2-sensor/AUDIT.plan.md` 阻塞清单勾选 |
| F-019-R02 | `layer2_cross_asset_sensor.md` §7 vs MASTER defer 交叉引用                 |
| F-019-R03 | fixture `FRED:VIXCLS` YAML 注释                                            |

### 4.7 Registry / 协调者动作（PROMPT_11 §Registry）

| #   | 要求                                                                       |
| --- | -------------------------------------------------------------------------- |
| R1  | NEW HIGH 写入 `AUDIT_DEFERRED_REGISTRY.md`（已修项标 RESOLVED + evidence） |
| R2  | `R3-PARTIAL-1` 与 ADV-R3X-SYNC-002 去重                                    |
| R3  | `adversarial_audit_report.md` 刷新（与 ADV-R3X-DOC-001 合并）              |
| R4  | migration 008/009 叙事（与 ADV-A6-003 合并）                               |

## 5. 验收

```bash
pytest tests/test_r3x_data_source_routing_blockers.py tests/test_r3x_residual_open_items_closure.py -q
pytest tests/test_source_route_planner.py tests/test_datasource_service.py tests/test_db_validation_gate.py tests/test_write_manager.py tests/test_sync_orchestrator.py -q
pytest tests/test_layer1_axis_loader.py tests/test_layer2_sensor_loader.py -q
pytest tests/test_production_live_pilot_policy.py tests/test_round3_audit_registry_alignment.py -q
python -m pytest -q
python scripts/check_doc_links.py
```

`merge_gate_report.md` 必须附 **Master Checklist 全表截图/表格**，无空白行。

## 6. 禁止

同 PROMPT_12/13：无 live fetch、无 production DB mutation、无 default enable disabled source、不关闭 REQ2-EM、不声称 production-live。
