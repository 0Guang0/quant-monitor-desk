# Plan 对抗性审计 Closure（P0–P3 全量）

> 主会话核实 agent 报告 + 第一轮 M-\*；全部 **CLOSED**

| ID   | 优先级 | 处置   | 证据                                                   |
| ---- | ------ | ------ | ------------------------------------------------------ |
| M-01 | P2     | CLOSED | mutation_proof §3                                      |
| M-02 | P2     | CLOSED | manifest + README                                      |
| M-03 | P2     | CLOSED | frozen §9.0–9.7                                        |
| M-04 | P3     | CLOSED | frozen `production_default_enabled`                    |
| M-05 | P2     | CLOSED | §1 具名 test 前缀 Rehearsal\*                          |
| M-06 | P3     | CLOSED | slug 接受                                              |
| A-01 | P0     | CLOSED | frozen §9.4 per-source DH 映射                         |
| A-02 | P0     | CLOSED | frozen §9.4/9.5 DEFAULT_PRODUCTION_DB + mutation_proof |
| A-03 | P1     | CLOSED | frozen §9A 3 series/120d；9.1 硬拒绝                   |
| A-04 | P1     | CLOSED | §1 9.6 `-k r3g01SandboxCleanWrite`                     |
| A-05 | P1     | CLOSED | §1 RehearsalPlan/Runner/Cli 具名                       |
| A-06 | P1     | CLOSED | frozen §9.4 conflict summary                           |
| A-07 | P1     | CLOSED | frozen §9.4 dry_run 默认；`--allow-live-fetch`         |
| A-08 | P1     | CLOSED | AC-10b + frozen §9.4                                   |
| A-09 | P1     | CLOSED | frozen §9.1 sandbox route；§3 capabilities             |
| A-10 | P2     | CLOSED | context_router 重跑                                    |
| A-11 | P2     | CLOSED | Execute 只读 frozen；活卡后续 merge                    |
| A-12 | P2     | CLOSED | frozen §9.3 `data_health_summary` 嵌套                 |
| A-13 | P2     | CLOSED | frozen §9.0 file-lock                                  |
| A-14 | P2     | CLOSED | §3 staged evidence 路径                                |
| A-15 | P2     | CLOSED | frozen §9.4 禁止 L1 ingestion                          |
| A-16 | P2     | CLOSED | §1 9.2/9.3 RED 创建测试                                |
| A-17 | P2     | CLOSED | frozen §9.1 注明可 bump contract version               |
| A-18 | P2     | CLOSED | AC-14                                                  |
| A-19 | P2     | CLOSED | §2.1 Tier B `uv sync --locked`                         |
| A-20 | P3     | CLOSED | frozen test 路径更正                                   |
| A-21 | P3     | CLOSED | slug 接受                                              |
| A-22 | P3     | CLOSED | EXECUTION_INDEX §4 边界登记                            |

**Gate：** 无开放 P0/P1/P2/P3 · `validate-plan-freeze` 须 exit 0
