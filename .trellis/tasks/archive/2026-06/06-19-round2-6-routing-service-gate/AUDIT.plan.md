# Audit 计划 — Round2.6 Phase C/D Routing Service Gate

> 读者：主会话 + A1–A8 子 agent  
> 必读：本文 + `audit.jsonl`；A5 另读 MASTER §2；Execute §10 证据只读。

---

## 0. 元信息

| 字段 | 值 |
|---|---|
| 任务 slug | `06-19-round2-6-routing-service-gate` |
| audit.jsonl | 第一条 = 本文件 |

## 1. 维度 — Agent — Skill 冻结清单

| 维度 | Agent ID | 执行者 | Skill（冻结） | 本任务 | GitNexus | @ 指令 | 产出 | 已执行 |
|---|---|---|---|---|---|---|---|---|
| A1 | audit-spec | 子 agent | trellis-check + doubt-driven-development | 必做 | 必用 | 对照 016A/016B/016F、contracts、MASTER §2，查遗漏/越界。 | §3.1 | [ ] |
| A2 | audit-ponytail | 子 agent | ponytail-review + doubt-driven-development | 必做 | 建议 | 审 service/route 实现是否过度抽象或重复 wrapper。 | §3.2 | [ ] |
| A3 | audit-security | 子 agent | security-and-hardening + doubt-driven-development | 必做 | 必用 | 查 qmt/xqshare enablement、silent fallback、path/config exposure。 | §3.3 | [ ] |
| A4 | audit-quality | 子 agent | code-review-and-quality + doubt-driven-development | 必做 | 建议 | 审错误处理、type boundary、payload schema、test clarity。 | §3.4 | [ ] |
| A5 | audit-completion | 子 agent | verification-before-completion + doubt-driven-development | 必做 | 必用 | 逐条 AC-PRE/C/D 追溯 Execute 证据。 | §3.5 | [ ] |
| A6 | audit-perf | 子 agent | performance-profiling + doubt-driven-development | 必做 | 必用 | 复核 production-equivalent smoke metrics 与 ResourceGuard。 | §3.6 | [ ] |
| A7 | audit-ops | 子 agent | doubt-driven-development | 必做 | 必用 | 幂等、清理、日志、deferred registry、Round3 gate。 | §3.7 | [ ] |
| A8 | audit-test-gap | 子 agent | testing-guidelines + doubt-driven-development | 必做 | 必用 | 补查 service-path、disabled source、no pollution 边界。 | §3.8 | [ ] |
| A9 | — | 主会话 | — | 必做 | 已刷新 | 汇总 A1–A8；二阶质疑遗漏。 | §4 | [ ] |

---

## 2. 维度验证矩阵

| 维 | 验证类型 | 命令 / 检查 | 环境 | 隔离策略 | 通过条件 | 扩展权限 | 证据 → | 已执行 |
|---|---|---|---|---|---|---|---|---|
| A1 | read-only | 对照 parent Contract Gate、016A/016B/016F、contracts 与 MASTER §2 | local | 无写 | 无 spec 漏项；无 Round4 内容误入 | 可追加 grep | §3.1 | [ ] |
| A2 | review-only | ponytail-review service/route/capability modules | local | 无写 | 无可删大段、无冗余 abstraction | — | §3.2 | [ ] |
| A3 | static | `rg -n "auto_login|captcha|order_target|order_value|place_order|silent fallback|XQSHARE" backend tests specs docs` | local | 无写 | 无 P0/P1 安全红线 | 可追加 secret grep | §3.3 | [ ] |
| A4 | review-only | 审 `DataSourceService`、`SourceRoutePlanner`、payload schema、tests | local | 无写 | 无阻断质量问题 | — | §3.4 | [ ] |
| A5 | trace-ac | AC-PRE/C1..D4 ↔ §8/§9/§10 ↔ evidence；抽 2 个 green evidence | local | 无写 | 全 AC 可追溯；证据真实 | 必须挑最弱 AC 深挖 | §3.5 | [ ] |
| A5 | cli-sandbox | `.audit-sandbox/r26-audit` 复跑 service tests + smoke subset | audit-sandbox | 独立 data root | 与 Execute 一致 | 可追加 1 行 | §3.5 | [ ] |
| A6 | cli-sandbox | 复跑 `python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r26-audit` | audit-sandbox | 独立 data root，清理 | metrics emitted; ResourceGuard observed | 可追加 time/resource wrapper | §3.6 | [ ] |
| A7 | cli-sandbox | 验证 init/smoke/idempotency + root self-check cleanup + deferred registry | audit-sandbox | 不写生产数据 | 可重复运行；无污染 | — | §3.7 | [ ] |
| A8 | pytest-isolated | `pytest tests/test_source_capabilities.py tests/test_datasource_service.py tests/test_sync_orchestrator.py tests/test_vendor_fetch_e2e.py -q` | audit-sandbox | tmp/data root | service-path and disabled-source boundaries covered | 可追加 2 测 | §3.8 | [ ] |

---

## 3. 工具要求

- 7.pre 主会话刷新 GitNexus/CodeGraph，写 `research/gitnexus-audit-summary.md`。
- A6/A7/A8 涉及写/CLI 必须用 `.audit-sandbox/`。
- Audit 不得用真实生产数据做破坏性复跑。

## 4. 验收汇总

Audit 输出 `audit.report.md`；若存在 §4.3 修复项，进入 REPAIR。

## 5. Audit DoD

- [ ] 7.pre 完成。
- [ ] A1–A8 完成。
- [ ] A9 汇总完成。
- [ ] PASS / PASS_WITH_FIXES / FAIL 结论明确。
