# Plan Boot — R3G-03 Limited Production Clean Write

> **Phase P0 complete** · 2026-06-27

## 用户授权

主会话用户 **已书面授权进入 R3G-03 有限生产写入 Plan 阶段**。Execute 仍须：活卡 §6 approval YAML、R3G-02 `audit_decision.json`、before/after proof、rollback dry-run 证据齐全后方可真写生产 DB。

## 已读 P0 输入

| #   | 文件                                                                 | 摘要                         |
| --- | -------------------------------------------------------------------- | ---------------------------- |
| 1   | `docs/implementation_tasks/README.md`                                | Round 3G 入口                |
| 2   | `TASK_INPUT_CONTEXT_INDEX.md`                                        | Plan 桥接                    |
| 3   | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                 | Batch 3G 当前下一入口        |
| 4   | `GLOBAL_EXECUTION_RULES.md`                                          | 无 broad fetch、fail-closed  |
| 5   | `GLOBAL_TESTING_POLICY.md`                                           | TDD 五字段                   |
| 6   | `GLOBAL_RESOURCE_LIMITS.md`                                          | ResourceGuard                |
| 7   | `GLOBAL_TASK_TEMPLATE.md`                                            | §9 步骤                      |
| 8   | `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md` | R3G-01→02→03 串行            |
| 9   | `R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md`                           | 本任务活卡（已加固 §9 步骤） |
| 10  | `BATCH_3G_TASK_CARD_MANIFEST.md`                                     | 3G 串行门                    |
| 11  | `BATCH_3G_HARDENING_RULES.md`                                        | 参考项目边界                 |
| 12  | `BATCH_3G_COORDINATOR_PLAYBOOK.md`                                   | 分支/合并                    |
| 13  | `specs/contracts/sandbox_clean_write_contract.yaml`                  | r3g03_limited_entry          |
| 14  | `specs/contracts/reference_adoption_guardrails.yaml`                 | Round3G guardrails           |

## 前置完成态

| 前置                     | 状态                                 | 证据                                                                |
| ------------------------ | ------------------------------------ | ------------------------------------------------------------------- |
| R3G-01 sandbox rehearsal | 已归档                               | `.trellis/tasks/archive/.../06-27-06-27-round3g-sandbox-rehearsal/` |
| R3G-02 adversarial audit | 已合并实现；审计报告 PASS_WITH_FIXES | `backend/app/ops/sandbox_clean_write/adversarial_audit.py`          |
| 契约门禁测试（静态）     | 已有                                 | `tests/test_round3g_limited_production_*.py`                        |
| 运行时 promote 模块      | **未实现**                           | 活卡 §4 建议路径尚不存在                                            |

## 任务边界（一句话）

在 **极窄 caps** 下实现 `qmd data sandbox-clean-write promote`：用户 approval + R3G-02 audit 对齐 → before proof → QMD 门禁链生产写（默认 dry_run）→ after proof → rollback dry-run 证据；**不**扩大候选源、**不** Agent 触发、**不**参考项目 runtime 拷贝。

## 明确不做

- 全市场/全历史/minute bar 生产写
- 无 approval 的默认 live fetch
- TradingAgents / agents-for-openbb 路径
- R3G-02 审计修复项的重新打开（除非阻塞 promote 契约）

## context_pack

`uv run python scripts/context_router.py --task .trellis/tasks/06-27-round3g-limited-production-write` — 已生成。
