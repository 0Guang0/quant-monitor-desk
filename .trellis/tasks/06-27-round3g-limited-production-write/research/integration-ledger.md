# Integration Ledger — R3G-03

> Plan 5c · 垂直切片与 manifest 对照

## 垂直切片（to-issues）

| 切片                 | 交付                                      | 依赖                         |
| -------------------- | ----------------------------------------- | ---------------------------- |
| S1 approval_contract | 解析+校验 approval YAML vs audit_decision | R3G-02 audit_decision 形状   |
| S2 before_proof      | before_proof.json 构建                    | mutation_proof               |
| S3 rollback_plan     | rollback_plan.json + dry_run 识别         | S2                           |
| S4 limited_entry     | 门禁链 runner（默认 dry_run）             | S1–S3, rehearsal_runner 模式 |
| S5 after_proof       | after_proof.json                          | S4                           |
| S6 CLI promote       | data_commands 子命令                      | S1–S5                        |
| S7 tests+guardrails  | 契约→对抗测                               | S6                           |
| S8 merge             | 全库 pytest + loop_maintain               | S7                           |

## 内联 vs manifest

| 来源                              | 处置                     |
| --------------------------------- | ------------------------ |
| 活卡 §6 approval schema           | 并入 frozen §6           |
| 活卡 §7 before/after 字段         | 并入 frozen §7           |
| 活卡 §8 forbidden                 | 并入 frozen §8           |
| sandbox_clean_write_contract.yaml | §3 must-read             |
| rehearsal_runner 编排细节         | §3 must-read（不可精简） |
| BATCH_3G_HARDENING_RULES          | §3 must-read             |

## Execute 不读

`research/plan-boot.md`、`grill-me-session.md`、本 ledger（除非 handoff 争议）
