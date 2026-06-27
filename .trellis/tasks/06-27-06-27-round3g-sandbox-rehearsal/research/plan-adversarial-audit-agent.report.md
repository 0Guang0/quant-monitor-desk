# Plan 对抗性审计 — Agent 第二轮（独立视角）

> model: composer-2.5 · 只读审计 · 主会话负责 closure 修复

## 发现列表

| ID   | 优先级 | 类别                 | 描述                                                   | 证据/路径                                                                       | 修复建议                                                             |
| ---- | ------ | -------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| A-01 | P0     | data_health_profiles | cninfo/fred 若仅调用 `market_bar_p0` 则 AC-04 无法验收 | `data_health_profiles/__init__.py` L36–37；`data_health.py` `_PROFILE_CHECKERS` | 按源映射：`market_bar_p0` / `staged_pilot_v3` / `fred_sandbox_pilot` |
| A-02 | P0     | production_mutation  | 生产 DB 路径拒绝无 SSOT                                | `staged_pilot.py` L42；`config.DATA_ROOT`                                       | 复用 `DEFAULT_PRODUCTION_DB` + `build_production_mutation_proof`     |
| A-03 | P1     | FRED caps            | 授权样板 5 series/3y 与 R3G cap 3/120d 冲突            | frozen §9A vs `authorization.yaml`                                              | R3G cap 硬拒绝；样板改为 3/120d                                      |
| A-04 | P1     | TDD                  | 9.6 `-k round3g` 无匹配                                | `test_reference_adoption_guardrails.py`                                         | 具名 test `test_r3g01SandboxCleanWrite_guardrailsClosure`            |
| A-05 | P1     | TDD                  | §1 `-k cap\|auth\|runner\|cli` 测试尚不存在            | EXECUTION_INDEX §1                                                              | RED 改为文件级 + frozen 列具名 test 函数                             |
| A-06 | P1     | SourceConflict       | roadmap 列 SourceConflict 但 Plan 未写                 | roadmap L247                                                                    | 9.4 单源 defer conflict summary（staged_pilot 模式）                 |
| A-07 | P1     | live_fetch           | loader/runner live vs staged 边界模糊                  | frozen §9.2/§9.4                                                                | 默认 `dry_run`/fixture；live 须 `--allow-live-fetch`                 |
| A-08 | P1     | mutation_proof       | roadmap before/after proof 未入 AC                     | `mutation_proof.py`                                                             | 9.4 产出 `production_db_no_mutation_proof.md`                        |
| A-09 | P1     | registry             | baostock production_default 真                         | `source_capabilities.yaml`                                                      | rehearsal_plan 强制 sandbox-only route                               |
| A-10 | P2     | context_pack         | 部分 §3 路径未进 pack                                  | `context_pack.json`                                                             | 重跑 context_router                                                  |
| A-11 | P2     | 活卡漂移             | 活卡仍 `production_default_allowed`                    | 活卡 §4.6                                                                       | Execute 只读 frozen；活卡 Plan 后择机 merge                          |
| A-12 | P2     | report fields        | 缺 duplicate PK / violation counts                     | frozen §4.4 vs contract                                                         | report 嵌套 `data_health_summary`（Plan §9.3）                       |
| A-13 | P2     | playbook             | 文件锁未写 Boot                                        | playbook §4                                                                     | frozen 9.0 列 file-lock                                              |
| A-14 | P2     | staged evidence      | Batch 2.5/3 证据路径未索引                             | staged_pilot v2/v3                                                              | §3 增 evidence SSOT                                                  |
| A-15 | P2     | ingestion            | L1 ingestion 误用风险                                  | `ingestion.py`                                                                  | 9.4 禁止调用 L1 write path                                           |
| A-16 | P2     | tests                | loader/report 文件不存在                               | glob                                                                            | Execute 9.2/9.3 创建（§1 已写 RED）                                  |
| A-17 | P2     | contract             | `status: draft_round3g`                                | contract L2                                                                     | Execute 9.1 可 bump version 若改 schema                              |
| A-18 | P2     | policy               | production_live policy 未绑 AC                         | policy doc                                                                      | AC-14 CLI/policy 对齐测                                              |
| A-19 | P2     | staged_acceptance    | Tier 缺 `uv sync --locked`                             | staged_acceptance_policy                                                        | §2.1 Tier B 补 locked sync                                           |
| A-20 | P3     | 命名                 | frozen 引用错误 test 文件名                            | frozen §4.1                                                                     | 改为 `test_data_health_profiles.py`                                  |
| A-21 | P3     | 命名                 | slug 日期重复                                          | task slug                                                                       | 接受，路径一致                                                       |
| A-22 | P3     | 边界                 | sandbox_clean_write vs staged_pilot                    | 新模块                                                                          | §4 登记边界表                                                        |

## 主会话复验

| ID         | 独立结论                    |
| ---------- | --------------------------- |
| M-01..M-03 | 成立；A-08 补 AC 后闭合     |
| M-04       | 仅 frozen 修复；活卡 → A-11 |
| M-05       | 部分成立 → A-05/A-16        |
| M-06       | 成立                        |

## 总结

**22 项发现**；主会话须在 Execute 前全部 CLOSED（见 `plan-adversarial-audit-closure.md`）。
