# 修复执行情况与自检报告（补充用户已拍板决策版）

## 1. 执行结论

已在上一轮审计修复版基础上，根据用户上传的 `待用户拍板决策点汇总(1).md` 将 D-01 至 D-12 全部写入对应文档、契约和 implementation task。原 `docs/quality/PENDING_USER_DECISIONS.md` 已从“待拍板”更新为“已拍板决策记录”。

结论：**D-01 至 D-12 已全部关闭，无剩余待用户拍板项。** 执行角色后续不得把这些事项重新作为未决问题。

## 2. 用户决策点写入位置核对

| 决策 | 写入/补充文件 | 状态 |
|---|---|---|
| D-01 | specs/contracts/runtime_versions.md<br>README.md<br>docs/quality/staged_acceptance_policy.md<br>docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md<br>ROUND0 002/003<br>ROUND5 036 | closed |
| D-02 | specs/contracts/api_security_contract.yaml<br>docs/modules/fastapi_backend.md<br>docs/api/fastapi_routes.md<br>ROUND4 024 | closed |
| D-03 | docs/ops/config_secret_policy.md<br>docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md<br>ROUND0 002<br>ROUND5 033 | closed |
| D-04 | docs/modules/notification_and_reports.md<br>docs/ops/privacy_retention_policy.md<br>ROUND4 028 | closed |
| D-05 | docs/ops/privacy_retention_policy.md<br>docs/modules/local_file_system.md<br>ROUND1 009<br>ROUND4 028<br>ROUND5 035 | closed |
| D-06 | docs/ops/migration_recovery_policy.md<br>ROUND1 005 | closed |
| D-07 | docs/quality/final_package_rules.md<br>specs/contracts/release_cleanup_allowlist.yaml<br>ROUND5 035/036 | closed |
| D-08 | docs/modules/frontend_dashboard.md<br>specs/frontend/page_contracts.yaml<br>ROUND4 026/027 | closed |
| D-09 | docs/adr/ADR-0003-layer1-standardization-only.md<br>docs/modules/layer2_cross_asset_sensor.md<br>docs/modules/layer3_industry_shock_anchor.md<br>docs/modules/layer4_market_structure.md<br>docs/modules/layer5_security_evidence.md<br>ROUND3 017-023 | closed |
| D-10 | README.md<br>docs/quality/staged_acceptance_policy.md<br>docs/quality/final_package_rules.md<br>specs/contracts/release_cleanup_allowlist.yaml<br>ROUND5 036 | closed |
| D-11 | specs/datasource_registry/source_registry.yaml<br>docs/modules/data_sources.md<br>docs/modules/qmt_xtdata_adapter.md<br>ROUND2 011/013 | closed |
| D-12 | docs/ops/agent_security_policy.md<br>docs/modules/agent_module.md<br>specs/contracts/agent_contract.yaml<br>ROUND4 025 | closed |

## 3. 本轮关键补充动作

- `docs/quality/PENDING_USER_DECISIONS.md`：改为已拍板决策记录，D-01 至 D-12 全部关闭。
- `specs/contracts/runtime_versions.md`：明确 Python 默认 `uv.lock`，默认命令使用 `uv sync` / `uv run`。
- `specs/contracts/api_security_contract.yaml`：明确 dev 可关闭 token 但仅 loopback；prod 必须 Bearer token，缺失 token 或关闭鉴权必须启动失败。
- `docs/ops/config_secret_policy.md`：明确第一版 `.env.local`，只提交 `.env.example`，必须 gitignore 与 secret scan。
- `docs/ops/privacy_retention_policy.md`：统一 raw/audit/report/notification 默认保留 1 年，并要求 archive/export。
- `docs/ops/migration_recovery_policy.md`：明确破坏性 migration 用备份恢复，非破坏性可无 down SQL。
- `docs/quality/final_package_rules.md` 与 `release_cleanup_allowlist.yaml`：写入 Trellis/Cursor 归档规则和设计包边界。
- `docs/modules/frontend_dashboard.md` 与 `page_contracts.yaml`：明确 UI 实现前必须用户确认，当前布局不得写死。
- Layer 相关 ADR/模块：明确完整标准化字段仅 Layer 1，Layer 2-5 按需局部扩展。
- `source_registry.yaml`、`data_sources.md`、`qmt_xtdata_adapter.md`：明确 QMT 默认禁用。
- `agent_security_policy.md`、`agent_module.md`、`agent_contract.yaml`：明确 Agent 固定来源 + 用户手动导入，禁止自由联网搜索。

## 4. 自检结果

| 检查项 | 结果 |
|---|---:|
| D-01 至 D-12 是否全部写入 PENDING_USER_DECISIONS.md | 是 |
| D-01 至 D-12 映射文件缺失项 | 0 |
| Markdown 相对链接坏链 | 0 |
| implementation task 输入引用缺失 | 0 |
| implementation task 输入重复 | 0 |
| MANIFEST.json 是否重新生成 | 是 |

## 5. 重要说明

- 本包仍是设计稿与执行计划包，不包含实现源码；这符合 D-10 的用户决策。
- 后续 Claude Code / Codex 实现源码后，最终审计应以源码 Git commit、CI 结果、测试输出和锁文件为准。
- 如果后续出现新的不明确选择，必须新增 D-13+，而不是修改已关闭的 D-01 至 D-12。


# 复审结果 P1-P3 修复补充（2026-06-19）

依据：`quant_monitor_复审结果_P0-P3_2026-06-19(1).md`。

## 本轮逐项修复

| ID | 处理结果 | 写入/修改位置 |
|---|---|---|
| P1-01 | 已修：MANIFEST 改为 exclude-self policy，最终清单不记录自身 sha256。 | `MANIFEST.json`、`docs/quality/final_package_rules.md`、`036_create_final_release_manifest.md` |
| P1-02 | 已修：37 份编号 implementation task 的验收命令改为 uv/阶段化验收。 | `docs/implementation_tasks/ROUND_*/*.md`、`GLOBAL_TASK_TEMPLATE.md`、`staged_acceptance_policy.md` |
| P1-03 | 已修：D-05 口径统一为 raw/audit/report/notification 逻辑保留 1 年；hot/cold 只作分层，不能覆盖总口径。 | `028_implement_reports_and_notifications.md`、`docs/ops/logs_health_audit.md` |
| P1-04 | 已修：新增 `FINAL_AUDIT_REPORT.md`，并加入 allowlist、MANIFEST 和最终包规则。 | `FINAL_AUDIT_REPORT.md`、`final_package_rules.md`、`release_cleanup_allowlist.yaml` |
| P2-01 | 已修：分页与查询预算以 `api_security_contract.yaml` 为唯一权威，默认 200、绝对 1000、Agent 最大 1000。 | `api_security_contract.yaml`、`fastapi_backend.md`、`fastapi_routes.md`、`frontend_security_policy.md` |
| P2-02 | 已修：source_registry 增加 disabled domain gating；QMT/Yahoo 默认禁用域返回 `DISABLED_SOURCE`。 | `source_registry.yaml`、`data_sources.md`、Round2 011/013 |
| P2-03 | 已修：第一版本地 Bearer token 明确为单 token=admin；viewer/agent_readonly 延期。 | `api_security_contract.yaml`、FastAPI/API/Frontend 安全文档 |
| P2-04 | 已修：第一版通知渠道硬限定为前端 Notification Center + 可选 email；webhook/desktop/SMS/phone/bot 延期。 | `notification_report_contract.yaml`、`notification_and_reports.md`、Round4 028 |
| P2-05 | 已修：GLOBAL_TESTING_POLICY 增加 deterministic/golden/time-freeze 基线。 | `GLOBAL_TESTING_POLICY.md` |
| P3-01 | 已修：架构文档依赖口径统一为 uv；pip-tools 备用；Poetry 第一版不采用。 | `02_solution_strategy.md` |
| P3-02 | 已修：旧数据源角色名禁止恢复为 source role / default role / fallback role；Layer 1 `SHADOW` 诊断标签作为窄例外保留。 | `data_sources.md`、`common_axis_rules.md`、Layer 1 indicator specs |

## 本轮自检要求

```text
Markdown 相对链接坏链：0
JSON/YAML 解析错误：0
implementation task 输入引用缺失：0
MANIFEST 自身 sha256 记录：禁止
FINAL_AUDIT_REPORT.md：必须存在并进入 allowlist/MANIFEST/zip
```

# 复审修复完成报告与最终自检

依据文件：`quant_monitor_复审结果_P0-P3_2026-06-19(1).md`。

## 1. 修复结论

本轮已按复审结果继续修复 P1-01 至 P3-02，并重新生成 `MANIFEST.json` 与最终 zip。

## 2. 逐项闭环结果

| ID | 状态 | 说明 |
|---|---|---|
| P1-01 | 通过 | MANIFEST 采用 `exclude_self_from_file_hashes`，不记录自身 sha256。 |
| P1-02 | 通过 | 37 份 implementation task 已改为 `uv sync --locked / uv run` 和阶段化验收。 |
| P1-03 | 通过 | D-05 留存口径统一为 raw/audit/report/notification 逻辑保留 1 年。 |
| P1-04 | 通过 | 新增 `FINAL_AUDIT_REPORT.md` 并进入 allowlist/MANIFEST/zip。 |
| P2-01 | 通过 | API 分页与查询预算以 `api_security_contract.yaml` 为唯一机器契约。 |
| P2-02 | 通过 | `source_registry.yaml` 增加默认禁用源与 domain gating。 |
| P2-03 | 通过 | 第一版本地 Bearer token 明确为单 token = admin，viewer/agent_readonly 延期。 |
| P2-04 | 通过 | 第一版通知渠道限定为前端 Notification Center + 可选 email。 |
| P2-05 | 通过 | 全局测试策略补充 deterministic/golden/time-freeze 基线。 |
| P3-01 | 通过 | 架构文档依赖口径已改为 uv；pip-tools 备用；Poetry 第一版不采用。 |
| P3-02 | 通过 | 旧数据源角色名不得恢复为运行时 source role；Layer 1 `SHADOW` 诊断标签明确为非 source role、no takeover。 |

## 3. 机器自检结果

```text
YAML/JSON 解析错误: 0
Markdown 相对链接坏链: 0
implementation task 输入引用缺失: 0
implementation task 输入重复: 0
编号任务数量: 37
仍使用旧统一验收命令任务数: 0
未包含 uv sync --locked 的编号任务数: 0
MANIFEST 是否记录自身 sha256: False
MANIFEST 缺失文件: 0
MANIFEST hash mismatch: 0
FINAL_AUDIT_REPORT.md exists: True
FINAL_AUDIT_REPORT.md allowlisted: True
```

## 4. 说明

本包仍为设计稿与执行计划包，不包含实现源码。后续 Claude Code / Codex 实现完成后的源码、CI、pytest/npm audit 结果，应通过 Git commit 与 CI 结果进行实现级终审。

## 最终对抗性审计修复补充（2026-06-19）

依据：`quant_monitor_最终对抗性审计_NOT_PASS_2026-06-19(1).md`。

| ID | 处理结果 | 写入/修改位置 |
|---|---|---|
| P1-01 | 已修：API / frontend table / Agent tool 查询预算以 `specs/contracts/api_security_contract.yaml` 为唯一机器权威；默认 200、绝对 1000，移除 100/500 与高于全局绝对上限的特殊工具例外旧口径。 | `api_security_contract.yaml`、`resource_limits.yaml`、`ops_health_check_contract.yaml`、`frontend_dashboard.md`、`performance_limits.md`、`ops_and_performance_v1_2.md`、`duckdb_and_parquet.md`、API 示例与 Round4 024/025 |
| P2-01 | 已修：Phase 1 throttle 不再包含 desktop_notification；desktop_notification 继续 D-13+ deferred，不实现发送逻辑或节流逻辑。 | `notification_report_contract.yaml`、`notification_and_reports.md`、Round4 028 |

本轮自检必须额外覆盖：查询预算单一权威测试名存在、resource_limits 与 api_security_contract 一致、无 stale 500 limit、无 active desktop 节流规则。

## 最终审计补修自检（2026-06-19）

依据：`quant_monitor_final_audit_NOT_PASS_2026-06-19(1).md`。

### 修复项

| ID | 状态 | 说明 |
|---|---|---|
| P2-01 | 已修 | 旧 `Shadow` 数据源角色禁令与 Layer 1 `SHADOW` 诊断标签完成概念拆分。旧角色只禁止作为 source role；`*.SHADOW.*` 允许作为明确带诊断/旁证语义的 Layer 1 indicator 条目、`shadow_diagnostics` 分组、`schema_note` 或说明文字，且不得接管主值。 |

### 新增一致性测试名

```text
test_legacySourceRoles_forbiddenAsSourceRoles
test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover
test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles
test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly
```

### 本轮补充自检要求

```text
legacy role broad YAML ban phrase: 0
Layer 1 SHADOW diagnostics missing no_takeover/no_main_score_input/validation_only: 0
source_registry roles using Shadow/Emergency outside legacy_roles_forbidden: 0
SHADOW entries outside shadow_diagnostics missing diagnostic_only/evidence_only/does_not_replace_main_indicator: 0
```

