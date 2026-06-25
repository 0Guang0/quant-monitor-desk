# FINAL_AUDIT_REPORT

本文件是 `quant_monitor_implementation_docs_v1` 设计稿与执行计划包的文档级最终审计记录。

## 审计性质

- 本包是 docs/specs/tasks 设计包，不包含实现源码。
- 源码实现、pytest/npm/CI 结果应由后续 Git commit 与 CI 结果进行实现级终审。
- 本文件用于记录本设计包对复审结果 `quant_monitor_复审结果_P0-P3_2026-06-19(1).md` 的修复闭环。

## 本轮修复范围

- P1-01：MANIFEST 自身 hash 策略改为 exclude-self，可验证。
- P1-02：37 份 implementation task 验收命令改为 uv/阶段化验收。
- P1-03：D-05 留存口径统一为 raw/audit/report/notification 逻辑保留 1 年。
- P1-04：FINAL_AUDIT_REPORT.md 加入最终包、allowlist 与 MANIFEST。
- P2-01：API 分页与查询预算统一以 `api_security_contract.yaml` 为权威。
- P2-02：source_registry 增加默认禁用源与数据域 gating。
- P2-03：第一版 token-role 明确为单本地 token = admin；viewer/agent_readonly 暂缓。
- P2-04：第一版通知渠道限定为前端 Notification Center + 可选 email。
- P2-05：全局测试策略补充 deterministic/golden/time-freeze 基线。
- P3-01：依赖口径统一为 uv；pip-tools 仅备用；Poetry 第一版不采用。
- P3-02：旧数据源角色名禁止恢复为 source role / default role / fallback role；Layer 1 `SHADOW` 仅允许作为诊断/旁证标签。

## 验收状态

本文件包打包前执行文档级自检：

```text
Markdown 相对链接坏链：应为 0
YAML/JSON 解析错误：应为 0
implementation task 输入引用缺失：应为 0
MANIFEST 自身 hash：不记录自身 sha256，采用 exclude-self policy
FINAL_AUDIT_REPORT.md：必须进入 allowlist、MANIFEST、最终 zip
```


## 再次复审修复补充（2026-06-19）

本轮依据 `quant_monitor_再次复审结果_NOT_PASS_2026-06-19(1).md` 修复以下残留项：

- P1-01：移除 Round4 前端任务验收命令中的 会吞掉失败结果的 shell 容错短路写法，API contract 测试失败不再被吞掉；若测试文件尚未创建，任务必须先创建最小 contract smoke test。
- P1-02：Round4 024 第一版 API 鉴权口径统一为“单本地 Bearer token = admin”；`viewer` / `agent_readonly` 仅作为 Phase 2 deferred role。
- P2-01：所有 `cd frontend && npm ci` 的任务验收命令均加入 `npm audit --audit-level=high`。
- P2-02：`docs/quality/staged_acceptance_policy.md` 主表同步为 `uv sync --locked` / `uv run` 阶段化验收口径。

## 最终对抗性审计修复补充（2026-06-19）

本轮依据 `quant_monitor_最终对抗性审计_NOT_PASS_2026-06-19(1).md` 修复以下新增残留项：

- P1-01：API / frontend table / Agent tool 查询预算统一以 `specs/contracts/api_security_contract.yaml` 为唯一机器权威；默认 page_size / Agent rows = 200，绝对上限 = 1000；移除或改写 100/500 与高于全局绝对上限的特殊工具例外旧口径。
- P2-01：通知模块 Phase 1 throttle 仅覆盖 dashboard notification / local audit / console summary / 显式配置后的 email；desktop_notification 继续延期到 D-13+，不得实现发送逻辑或该延期渠道的节流逻辑。

新增/强化测试名：`test_apiSecurityContract_isSingleAuthorityForQueryBudget`、`test_resourceLimitsApiLimits_matchApiSecurityContract`、`test_frontendPageContracts_doNotUseStale500Limit`、`test_phase1NotificationThrottle_excludesDesktop`、`test_notificationModule_containsNoActiveDesktopThrottleInPhase1`。

## 最终审计补修（2026-06-19）

本轮依据 `quant_monitor_final_audit_NOT_PASS_2026-06-19(1).md` 修复跨文档一致性缺口：旧 `Shadow` 数据源角色名的禁止规则与 Layer 1 YAML indicator specs 中 `SHADOW` 诊断标签并非同一概念。

修复后口径：

- 旧 `Shadow` / `Emergency` 作为**数据源角色**时禁止恢复，不能进入 source role、default role、fallback role、API role、DB role、frontend source-role 展示字段或运行时代码枚举。
- Layer 1 `*.SHADOW.*`、`layer: Shadow`、`dest_tag: SHADOW` 仅表示诊断/旁证标签，不表示数据源角色；允许出现在明确带诊断/旁证语义的 Layer 1 indicator 条目、`shadow_diagnostics` 分组、`schema_note` 或说明文档中，不得接管 clean 主值，也不得进入 source_registry role。
- 对不在 `shadow_diagnostics` 分组下的 `*.SHADOW.*` 条目，必须显式写明 `diagnostic_only` / `evidence_only` / `does_not_replace_main_indicator` 或同等约束。
- `source_registry.yaml` 中 `legacy_roles_forbidden` 仅作为禁止清单保留，不代表允许恢复旧角色。
- 新增一致性测试名：`test_legacySourceRoles_forbiddenAsSourceRoles`、`test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover`、`test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles`、`test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly`。

