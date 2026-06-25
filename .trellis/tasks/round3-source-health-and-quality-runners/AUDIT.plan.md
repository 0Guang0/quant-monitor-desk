# AUDIT 计划 — B3F-SH Source Health & Quality Runners

> 读者：主会话 + A1–A8 · audit.jsonl 第一条 = 本文件

---

## 0. 元信息

| 字段 | 值 |
| ---- | --- |
| 任务 slug | `round3-source-health-and-quality-runners` |
| AUDIT_PROD_ROOT | `.audit-sandbox/b3f-sh-audit-prod/` |

## 1. 维度 — Skill 冻结

| 维 | Agent | Skill | 本任务 | 已执行 |
| --- | --- | --- | --- | --- |
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
| A1 | read-only | 对照 R3F 卡、playbook §2.6、MASTER §2/§3 | local | 无 scope 泄漏；MIG 边界遵守 | [ ] |
| A2 | review-only | ponytail-review writer + orchestrator 改动 | local | 最小 diff | [ ] |
| A3 | static | `rg` production clean write / 无授权 live | local | 无密钥泄露 | [ ] |
| A4 | review-only | ADR + evidence 命名 | local | 无阻断质量问题 | [ ] |
| A5 | trace-ac | AC-SH-01..07 ↔ §9 evidence | local | 切片可追溯 | [ ] |
| A5 | cli-sandbox | `uv run pytest tests/test_source_health_snapshot.py tests/test_b3f_quality_runners.py -q` | audit-sandbox | 与 Execute 一致 | [ ] |
| A5 | audit-prod-path | `uv run pytest -q`；prod data hash 不变 | audit-prod-path | 无污染 | [ ] |
| A6 | — | **跳过 — source health 无 perf hot path** | — | SKIP | [ ] |
| A7 | cli-sandbox | 无 prod migration 写；DH2 无 DDL | audit-sandbox | 无 prod 写 | [ ] |
| A8 | pytest-isolated | FRED 授权门；AkShare false-close | audit-sandbox | 边界测试绿 | [ ] |

### 2.2 A6 SKIP

本任务跳过性能审计 — source health / runner 闭包无独立 perf SLA。

## 3. Audit Source Trace

| Item | 原文 | AC | 证据 |
| ---- | ---- | --- | ---- |
| R3F | `R3F_verified_audit_ops_perf_hygiene.md` | AC-SH-05 | execute-evidence |
| 014 | orchestrator 卡 | AC-SH-02/03 | quality runners tests |
| Playbook | `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.5 | boundary | MASTER §0 |
| FRED auth | `fred_live_authorization_2026-06-25.yaml` | AC-SH-06 | live evidence |
| hardening | `BATCH_3F_HARDENING_RULES.md` | live/validation | policy alignment |

## 4. Audit DoD

- [ ] 7.pre `gitnexus-audit-summary.md`
- [ ] A1–A8（A6 SKIP）
- [ ] A9 汇总 PASS / FAIL
