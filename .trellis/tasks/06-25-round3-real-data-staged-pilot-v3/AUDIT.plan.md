# AUDIT 计划 — B01-C04 staged pilot v3

> 读者：主会话 + A1–A8 · audit.jsonl 第一条 = 本文件

---

## 0. 元信息

| 字段 | 值 |
| ---- | -- |
| 任务 slug | `06-25-round3-real-data-staged-pilot-v3` |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3e-pilot-v3-audit-prod/` |

## 1. 维度 — Skill 冻结

| 维 | Agent | Skill | 本任务 | 已执行 |
| --- | ----- | ----- | ------ | ------ |
| A1 | audit-spec | trellis-check + doubt-driven-development | 必做 | [ ] |
| A2 | audit-ponytail | ponytail-review + doubt-driven-development | 必做 | [ ] |
| A3 | audit-security | security-and-hardening + doubt-driven-development | 必做 | [ ] |
| A4 | audit-quality | code-review-and-quality + doubt-driven-development | 必做 | [ ] |
| A5 | audit-completion | verification-before-completion + doubt-driven-development | 必做 | [ ] |
| A6 | audit-perf | doubt-driven-development | **不用** | [ ] |
| A7 | audit-ops | doubt-driven-development | 必做 | [ ] |
| A8 | audit-test-gap | testing-guidelines + doubt-driven-development | 必做 | [ ] |
| A9 | 主会话 | — | 必做 | [ ] |

## 2. 维度验证矩阵

| 维 | 验证类型 | 命令 / 检查 | 环境 | 通过条件 | 已执行 |
| --- | --- | --- | --- | --- | --- |
| A1 | read-only | 对照 R3E v3 卡、playbook §2.5/§2.6、WL trace、MASTER §2/§3 | local | 无 scope 泄漏 | [ ] |
| A2 | review-only | ponytail-review `staged_pilot.py` v3 新增符号 | local | 最小 diff | [ ] |
| A3 | static | `rg` clean write / hand-picked symbols / PDF bulk | local | 无旁路 | [ ] |
| A4 | review-only | closeout v3 字段、evidence 命名一致性 | local | 无阻断质量问题 | [ ] |
| A5 | trace-ac | AC-SP3-01..06 ↔ §9 evidence | local | 六切片可追溯 | [ ] |
| A5 | cli-sandbox | `.audit-sandbox/r3e-pilot-v3-audit/` 复跑 v3 测试 | audit-sandbox | 与 Execute 一致 | [ ] |
| A5 | read-only | 抽检 `no_mutation_proof_v3.md` hash/count | local | 非空声称 | [ ] |
| A5 | audit-prod-path | 复制树到 `AUDIT_PROD_ROOT`；`uv run pytest tests/test_real_data_staged_pilot_v3.py -q` | audit-prod-path | 无污染 | [ ] |
| A6 | — | **本任务跳过 — pilot 无 hot path/SLA** | — | SKIP | [ ] |
| A7 | cli-sandbox | 无 migration/DB clean write | audit-sandbox | 无 prod 写 | [ ] |
| A7 | audit-prod-path | `data/duckdb/` hash 审计前后不变 | audit-prod-path | 无污染 | [ ] |
| A8 | pytest-isolated | WL 缺失 fail-closed；akshare primary 边界 | audit-sandbox | 测绿或记入 report | [ ] |
| A8 | audit-prod-path | `uv run pytest tests/test_production_live_pilot_policy.py -q` | audit-prod-path | 全绿 | [ ] |

### 2.2 A6 SKIP

本任务跳过性能审计 — 受控小样本 staged pilot，无 SLA。

## 3. Audit Source Trace

| Item | 原文 | AC | 证据 |
| ---- | ---- | -- | ---- |
| R3E | `R3E_real_data_staged_pilot_v3.md` | AC-SP3-* | execute-evidence v3 |
| WL | `R3D_model_input_whitelist.md` | AC-SP3-01 | specs/model_inputs |
| Playbook | `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §8.6 | 验收命令 | pytest 输出 |
| hardening | `BATCH_01_HARDENING_RULES.md` | live/auth | authorization YAML |
| v2 | v2 archive | 对照 | diff v3 |
| policy | `production_live_pilot_policy.md` | staged-only | policy tests |

## 4. Audit DoD

- [ ] 7.pre `gitnexus-audit-summary.md`
- [ ] A1–A8（A6 SKIP）
- [ ] A9 汇总 PASS / FAIL
