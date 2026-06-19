# Audit 计划 — Round2.6 Phase B Contract Gate

> 读者：主会话 + A1–A8 子 agent  
> 必读：本文 + `audit.jsonl`；A5 另读 MASTER §2；Execute §10 证据只读。

---

## 0. 元信息

| 字段 | 值 |
|---|---|
| 任务 slug | `06-19-round2-6-contract-gate` |
| audit.jsonl | 第一条 = 本文件 |
| 验证词典 | `.trellis/spec/guides/audit-skill-registry.md` |

## 1. 维度 — Agent — Skill 冻结清单

| 维度 | Agent ID | 执行者 | Skill（冻结） | 本任务 | GitNexus | @ 指令 | 产出 | 已执行 |
|---|---|---|---|---|---|---|---|---|
| A1 | audit-spec | 子 agent | trellis-check + doubt-driven-development | 必做 | 必用 | 对照 016A-016F、contracts、MASTER §2，查 scope 漏洞/扩大。 | §3.1 | [x] |
| A2 | audit-ponytail | 子 agent | ponytail-review + doubt-driven-development | 必做 | 建议 | 只审测试/脚本是否过度工程；不得要求生产 service。 | §3.2 | [x] |
| A3 | audit-security | 子 agent | security-and-hardening + doubt-driven-development | 必做 | 必用 | 查 qmt/xqshare enablement、auto-login、secret、silent fallback 风险。 | §3.3 | [x] |
| A4 | audit-quality | 子 agent | code-review-and-quality + doubt-driven-development | 必做 | 建议 | 审 contract tests 是否有业务断言、错误信息、可维护性。 | §3.4 | [x] |
| A5 | audit-completion | 子 agent | verification-before-completion + doubt-driven-development | 必做 | 必用 | 逐条 AC-B1..B10 追溯 Execute 证据。 | §3.5 | [x] |
| A6 | audit-perf | 子 agent | — | 不用 | — | 本任务无 hot path；只做 tests/checker，不做 runtime perf。 | §3.6 SKIP | [x] |
| A7 | audit-ops | 子 agent | doubt-driven-development | 必做 | 必用 | 审 `.audit-sandbox`、no pollution、docs/check failures 是否可观测。 | §3.7 | [x] |
| A8 | audit-test-gap | 子 agent | testing-guidelines + doubt-driven-development | 必做 | 必用 | 查 Red Flags 边界测试是否漏：domain mismatch、disabled source、direct factory。 | §3.8 | [x] |
| A9 | — | 主会话 | — | 必做 | 已刷新 | 汇总 A1–A8，二阶质疑遗漏。 | §4 | [x] |

---

## 2. 维度验证矩阵（Plan 冻结 · Audit 执行 · 非 MASTER §10）

| 维 | 验证类型 | 命令 / 检查 | 环境 | 隔离策略 | 通过条件 | 扩展权限 | 证据 → | 已执行 |
|---|---|---|---|---|---|---|---|---|
| A1 | read-only | 对照 `research/original-plan-trace.md`、016A-016F、`specs/contracts/*`、`docs/AUDIT_DEFERRED_REGISTRY.md` 与 MASTER §2 | local | 无写 | 无遗漏 AC；无 Round4 内容误塞为 pre-Round3 阻塞 | 可追加 grep docs/specs | §3.1 | [x] |
| A2 | review-only | ponytail-review 新 tests/checker：能否删掉重复 parser、是否过度 wrapper | local | 无写 | 无必删 bloat；若有列 §4.3 | — | §3.2 | [x] |
| A3 | static | `rg -n "auto_login|captcha|order_target|order_value|place_order|XQSHARE_REMOTE_HOST" backend tests specs docs` | local | 无写 | 无启用/交易/自动登录路径；xqshare 仅 contract/docs | 可追加 secret grep | §3.3 | [x] |
| A4 | review-only | 审新增测试是否符合 `GLOBAL_TESTING_POLICY.md`：业务断言、命名、mock 边界 | local | 无写 | 无只 assert exists/not null 的测试 | — | §3.4 | [x] |
| A5 | trace-ac | 逐条 AC-B1..B10 ↔ §8/§9/§10 ↔ execute-evidence；抽 2 个 green evidence | local | 无写 | 每条 AC 可追溯；证据真实 | 必须挑最弱 1 条深挖 | §3.5 | [x] |
| A5 | cli-sandbox | 在 `.audit-sandbox/contract-gate-audit` 复跑 `pytest tests/test_source_capabilities.py tests/test_module_boundaries.py -q` | audit-sandbox | 独立 basetemp | 与 Execute 声称一致 | 可追加 1 行 | §3.5 | [x] |
| A6 | — | SKIP — 本任务不实现 hot runtime path；性能属于 Task 2 Phase D | — | — | N/A | — | §3.6 | [x] |
| A7 | cli-sandbox | 复查 `python scripts/check_module_boundaries.py` 与 `.audit-sandbox` 清理策略 | audit-sandbox | 不写生产数据 | checker 可重复运行；无临时污染 | — | §3.7 | [x] |
| A8 | pytest-isolated | 追加/复跑边界选择器：`pytest tests/test_source_capabilities.py tests/test_datasource_service.py tests/test_platform_source_matrix.py -q` | audit-sandbox | tmp path | domain/direct factory/qmt disabled 边界均覆盖 | 可追加 2 个测试 | §3.8 | [x] |

---

## 3. 工具要求

- 7.pre 主会话：刷新 GitNexus/CodeGraph，写 `research/gitnexus-audit-summary.md`。
- A1–A8 必须读 `research/gitnexus-audit-summary.md`。
- 写库/CLI 类复跑必须使用 `.audit-sandbox/`，不得写真实生产数据。

## 4. 验收汇总

Audit 汇总 Execute §10 证据、§2 本维结果，输出 `audit.report.md`。若存在 §4.3 修复项，进入 `REPAIR.plan.md`。

## 5. Audit DoD

- [x] 7.pre 完成。
- [x] A1–A8 完成。
- [x] A9 汇总完成。
- [x] PASS / PASS_WITH_FIXES / FAIL 结论明确。
