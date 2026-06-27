# R3G-02 五维审计合并修复清单（二轮 repair SSOT）

**日期：** 2026-06-27 · **分支：** `feature/round3g-adversarial-audit`
**来源：** `audit.report.md` + `research/audit-evidence/a1.md` … `a8.md`
**要求：** 全部 CLOSED，不遗留；TDD + ponytail + 五字段 + 全库 pytest；不 commit

## P0（合并去重）

| ID      | 项                                                                 | 来源     |
| ------- | ------------------------------------------------------------------ | -------- |
| M-P0-01 | bar 源 lineage coverage=0.0 → BLOCK；<1.0 → WARN                   | A1/A3/A4 |
| M-P0-02 | `synthetic_admission` + validation PASSED → gate_bypass WARN/BLOCK | A1/A3/A4 |
| M-P0-03 | `rollback_artifact_path` 必须 `is_file()`                          | A4       |

## P1（合并）

| ID      | 项                                                              |
| ------- | --------------------------------------------------------------- |
| M-P1-01 | §3.1 EasyXT/DH 证据内容读取（cn_equity_daily_bar）              |
| M-P1-02 | guardrail：抽共享 scanner 或 parity；≥1 真实扫描集成测          |
| M-P1-03 | §3.4 provider 全元数据（auth、production_default_enabled、cap） |
| M-P1-04 | §3.3 行数/coverage 实质校验                                     |
| M-P1-05 | `evidence_dir` 非目录 → BLOCK                                   |
| M-P1-06 | JQ2PTrade `get_*` API 与契约 SSOT 对齐                          |

## P2（合并）

| ID      | 项                                                                      |
| ------- | ----------------------------------------------------------------------- |
| M-P2-01 | agent_triggered_write 对抗测                                            |
| M-P2-02 | gate_bypass 合成报告测（strategy metrics、production_mutation_allowed） |
| M-P2-03 | audit CLI DATA_ROOT 生产路径拒绝测                                      |
| M-P2-04 | adhoc DH / gate_rationale 检查                                          |
| M-P2-05 | fred 授权 posture 审计                                                  |
| M-P2-06 | loader JQ2PTrade 模式专审或扫描扩展                                     |
| M-P2-07 | 契约 warning_if 或 approximate_calendar 文档                            |

## P3（合并）

| ID      | 项                                                 |
| ------- | -------------------------------------------------- |
| M-P3-01 | `__init__.py` 导出或 ponytail 注释                 |
| M-P3-02 | `AuditResult.serialize` 死代码；顶层 import json   |
| M-P3-03 | `_resolve` 复用 `_resolve_path`                    |
| M-P3-04 | `provider_for_source` / `source_registry` API 复用 |
| M-P3-05 | guardrail 扫描 `ponytail:` 性能天花板注释          |
| M-P3-06 | 测试 fixture/docstring 卫生（A8-07）               |

## 验证

```bash
uv run pytest tests/test_round3g_pre_production_adversarial_audit.py tests/test_reference_adoption_guardrails.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py
```

更新 `research/audit-repair-closure.md` 全部 CLOSED 后 handoff。
