# AUDIT 计划 — round3-020-layer3-loader

> 读者：主会话 + A1–A8 · audit.jsonl 第一条 = 本文件

---

## 0. 元信息

| 字段 | 值 |
| ---- | -- |
| 任务 slug | `06-23-round3-020-layer3-loader` |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3-020-audit-prod-equiv` |

## 1. 维度 — Skill 冻结

| 维 | Agent | Skill | 本任务 | 已执行 |
| -- | ----- | ----- | ------ | ------ |
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
| -- | -------- | ----------- | ---- | -------- | ------ |
| A1 | read-only | 对照 `layer3_loader_contract.yaml`、`layer3_industry_shock_anchor.md`、MASTER §2/§3 | local | 无 scope 泄漏 | [ ] |
| A2 | review-only | ponytail-review `backend/app/layer3_chains/` | local | 最小 diff | [ ] |
| A3 | static | `rg` 直写 DB / 改 forbidden 路径 | local | 无 mutation | [ ] |
| A4 | review-only | loader 校验链、错误类型一致 | local | 无阻断质量问题 | [ ] |
| A5 | trace-ac | AC-020-1..6 ↔ §8 evidence | local | 全 AC 可追溯 | [ ] |
| A5 | cli-sandbox | `.audit-sandbox/r3-020` 复跑 `test_layer3_loader.py` | audit-sandbox | 与 Execute 一致 | [ ] |
| A5 | read-only | 抽检 `execute-evidence/8.2-green.txt` 真实性 | local | 非占位 | [ ] |
| A5 | audit-prod-path | 复制树到 `AUDIT_PROD_ROOT`；`uv run pytest tests/test_layer3_loader.py -q`；prod data hash 不变 | audit-prod-path | 无污染 | [ ] |
| A6 | — | **本任务跳过 — loader 无 hot path/SLA；纯配置解析** | — | SKIP | [ ] |
| A7 | cli-sandbox | 确认无 migration/DB 写；sandbox 无 `data/` 污染 | audit-sandbox | 无 prod 写 | [ ] |
| A7 | audit-prod-path | `data/duckdb/` hash 审计前后不变 | audit-prod-path | 无污染 | [ ] |
| A8 | pytest-isolated | 补边界：空 bundle（MASTER §5.3 未列） | audit-sandbox | 新测绿或记入 audit.report | [ ] |
| A8 | audit-prod-path | 复跑 `test_batch3_staged_downstream_gate.py` | audit-prod-path | 全绿 | [ ] |

### 2.2 A6 SKIP

本任务跳过性能审计 — loader 仅解析小型 staged fixture，无 SLA。

## 3. Audit Source Trace

| Item | 原文 | AC | 证据 |
| ---- | ---- | -- | ---- |
| `020` | `020_implement_layer3_industry_chain_loader.md` | AC-020-* | `test_layer3_loader.py` |
| contract | `layer3_loader_contract.yaml` | AC-020-2,4 | loader 断言 |
| staged gate | `BATCH3_STAGED_DOWNSTREAM_GATE.md` | AC-020-5 | batch3 gate tests |
| 019 模式 | `sensor_loader.py` | AC-020-5 | staged_fixture_only |
| lineage | `snapshot_lineage_contract.yaml` | defer | 未改 contract |

## 4. Audit DoD

- [ ] 7.pre `gitnexus-audit-summary.md`
- [ ] A1–A8（A6 SKIP）
- [ ] A9 汇总 PASS / FAIL
