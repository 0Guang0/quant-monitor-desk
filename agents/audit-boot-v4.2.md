# Audit Boot — Plan v4.2（Slim Plan）

> **Leading word — v4.2：** 规格在 **`EXECUTION_PLAN.md`**；机器路由在 **`EXECUTION_INDEX.md` §3**；`frozen/*.md` 为薄指针。  
> **读者：** A9 主会话 · A1–A8 子 agent（派发前 **全文 Read**）。  
> **legacy v4.1：** `agents/audit-boot-v4.1.md`

## 协议

| 字段         | 值                                                                |
| ------------ | ----------------------------------------------------------------- |
| `task.json`  | `meta.plan_protocol_version` 须为 **`"4.2"`**                     |
| Execute 验收 | `EXECUTION_INDEX.md` §1 `[x]` + §2 AC + §2.1 Tier + **代码/测试** |
| 计划 AC SSOT | `EXECUTION_PLAN.md`                                               |

## Boot 读序（按序 · 不得跳）

| #   | 文件                                    | 用途                                |
| --- | --------------------------------------- | ----------------------------------- | ----------------- |
| 1   | `agent-toolchain.md`                    | 工具路由                            |
| 2   | `agents/audit-adversarial-authority.md` | 对抗权威                            |
| 3   | 本文件                                  | Boot checklist                      |
| 4   | `agents/audit-finding-schema.md`        | findings 关账                       |
| 5   | `agents/audit-coverage-model.md`        | 两条链·三类缺口                     |
| 6   | `<task>/task.json`                      | 确认 `plan_protocol_version: "4.2"` |
| 7   | `<task>/AUDIT.plan.md`                  | §0.1 Trace + §1 覆写                |
| 8   | `<task>/audit.jsonl`                    | 全文                                |
| 9   | `<task>/EXECUTION_PLAN.md`              | 计划正文 / AC / 约束                |
| 10  | `<task>/EXECUTION_INDEX.md`             | §5 追溯 · §3 audit/both · §1/§2     |
| 11  | `<task>/frozen/*.md`                    | 审计锚点（薄指针）                  |
| 12  | `<task>/implement.jsonl`                | A5 全读                             |
| 13  | INDEX §3 `audience=audit                | both` 路径                          | manifest 必读原文 |
| 14  | `research/gitnexus-audit-summary.md`    | 7.pre                               |
| 15  | GitNexus                                | ≥1 query/context                    |

### `research/`（v4.2 默认非 SSOT）

仅当 INDEX §3 或 AUDIT Trace 登记时必读。

## v4.2 术语对照

| 旧（v4.1）           | v4.2 Audit 读                             |
| -------------------- | ----------------------------------------- |
| `00-EXECUTION-ENTRY` | `EXECUTION_PLAN.md`                       |
| `EXTERNAL-INDEX` §A  | `EXECUTION_INDEX.md` §3 + implement.jsonl |
| `to-issues-slices`   | `EXECUTION_PLAN` 内切片 + INDEX §1/§2     |

## Boot 完成条件

- [ ] #6–#14 已 Read；INDEX §3 audit/both 行已覆盖
- [ ] `gitnexus-audit-summary.md` 已产出（7.pre）

## A9 合并

同 `audit-boot-v4.1.md` §A9（`audit.report.md` §4.2 · `validate-audit-handoff` exit 0）。
