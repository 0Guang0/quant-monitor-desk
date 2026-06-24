# AUDIT 计划 — B01-FRED FRED Sandbox Pilot

> 读者：主会话 + A1–A8 · audit.jsonl 第一条 = 本文件

---

## 0. 元信息

| 字段 | 值 |
| ---- | --- |
| 任务 slug | `round3-fred-authorized-sandbox-pilot` |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3e-fred-audit-prod/` |

## 1. 维度 — Skill 冻结

| 维 | Agent | Skill | 本任务 | 已执行 |
| --- | --- | --- | --- | --- |
| A1 | audit-spec | trellis-check + doubt-driven-development | 必做 | [x] |
| A2 | audit-ponytail | ponytail-review + doubt-driven-development | 必做 | [x] |
| A3 | audit-security | security-and-hardening + doubt-driven-development | 必做 | [x] |
| A4 | audit-quality | code-review-and-quality + doubt-driven-development | 必做 | [x] |
| A5 | audit-completion | verification-before-completion + doubt-driven-development | 必做 | [x] |
| A6 | audit-perf | doubt-driven-development | **不用** | [x] |
| A7 | audit-ops | doubt-driven-development | 必做 | [x] |
| A8 | audit-test-gap | testing-guidelines + doubt-driven-development | 必做 | [x] |
| A9 | 主会话 | — | 必做 | [x] |

## 2. 维度验证矩阵

| 维 | 验证类型 | 命令 / 检查 | 环境 | 通过条件 | 已执行 |
| --- | --- | --- | --- | --- | --- |
| A1 | read-only | 对照 R3E、BATCH_01 hardening、MASTER §2/§3 | local | 无 scope 泄漏；未改 data_health 主体 | [x] |
| A2 | review-only | ponytail-review `fred_sandbox_pilot.py` `fred_fetch_ports.py` | local | 最小 diff；无新依赖 | [x] |
| A3 | static | `rg` API key / production clean write / FRED default enabled | local | 无密钥泄露 | [x] |
| A4 | review-only | closeout 字段、evidence 命名一致性 | local | 无阻断质量问题 | [x] |
| A5 | trace-ac | AC-FRED-01..07 ↔ §9 evidence | local | 切片可追溯 | [x] |
| A5 | cli-sandbox | 复跑 `test_fred_source_registry.py` + `test_fred_sandbox_pilot.py` | audit-sandbox | 与 Execute 一致 | [x] |
| A5 | audit-prod-path | `uv run pytest -q`；prod data hash 不变 | audit-prod-path | 无污染 | [x] |
| A6 | — | **跳过 — 受控小样本 sandbox pilot** | — | SKIP | [x] |
| A7 | cli-sandbox | 无 migration/DB clean write | audit-sandbox | 无 prod 写 | [x] |
| A8 | pytest-isolated | macro 不能关 B2.5-O-05；缺授权 live 失败 | audit-sandbox | 边界测试绿 | [x] |

### 2.2 A6 SKIP

本任务跳过性能审计 — 受控 FRED 小样本 sandbox pilot。

## 3. Audit Source Trace

| Item | 原文 | AC | 证据 |
| ---- | ---- | --- | ---- |
| R3E | `R3E_fred_authorized_sandbox_pilot.md` | AC-FRED-* | execute-evidence |
| PROMPT_04 | legacy L04 | B2.5-O-05 语义 | staged semantics tests |
| hardening | `BATCH_01_HARDENING_RULES.md` | 授权/registry | authorization.yaml |
| WL | `R3D_model_input_whitelist.md` | P0 series | route/fetch caps |
| policy | `production_live_pilot_policy.md` | sandbox-only | policy alignment |
| registry | `AUDIT_DEFERRED_REGISTRY.md` | B2.5-O-05 | closeout |

## 4. Audit DoD

- [x] 7.pre `gitnexus-audit-summary.md`
- [x] A1–A8（A6 SKIP）
- [x] A9 汇总 PASS / FAIL
