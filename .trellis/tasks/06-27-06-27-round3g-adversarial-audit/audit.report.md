# R3G-02 Focused Audit Report

**日期：** 2026-06-27 · **分支：** `feature/round3g-adversarial-audit`  
**轨道：** simple · **结论：** `PASS_WITH_FIXES`（须修复全部 P0–P3 后方可合并）

## 审计维度

| 维                  | 焦点                                  | 结论            |
| ------------------- | ------------------------------------- | --------------- |
| A1 契约             | `r3g02_audit` / `block_if` / 报告字段 | FAIL_WITH_FIXES |
| A3 安全 fail-closed | 生产路径、mutation、审计误放行        | FAIL_WITH_FIXES |
| A4 正确性           | 五维审计逻辑 vs 任务卡 §3             | FAIL_WITH_FIXES |
| A7 架构             | ponytail 复用、扫描重复               | PASS_WITH_FIXES |
| A8 测试             | 任务卡 §7 矩阵、真实扫描 vs mock      | FAIL_WITH_FIXES |

## P0 — BLOCKING

| ID             | 项                              | 证据                                                                                                                                             | 修复要求                                                                                                 |
| -------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| R3G2-REP-P0-01 | **零 lineage coverage 仍 PASS** | `baostock` dry_run 报告 `source_fetch_id_coverage=0.0`、`content_hash_coverage=0.0`；`test_r3g02AdversarialAudit_boundedRehearsalPasses` 仍 PASS | §3.3：对 bar 源要求 coverage 阈值（建议 dry_run `<1.0` → WARN，`0.0` → BLOCK）；加测试                   |
| R3G2-REP-P0-02 | **synthetic_admission 未审计**  | `rehearsal_runner` per-source `synthetic_admission=True` + `validation_status=PASSED`；审计未触发 `write_manager_or_db_validation_gate_bypass`   | 报告含 synthetic 时至少 WARN；若 validation_status=PASSED 且 synthetic → BLOCK 或契约对齐的 WARN；加测试 |

## P1 — HIGH

| ID             | 项                           | 证据                                                                                                                             | 修复要求                                                                                                              |
| -------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| R3G2-REP-P1-01 | **§3.1 EasyXT 证据内容未读** | `adversarial_audit.py` 仅查 `data_health_summary` 结构，未读 `validation_report_summary.json` / bars 证据做 OHLC/空数据/异常检查 | 对 `cn_equity_daily_bar` 读 evidence 文件或 DH 报告 JSON，fail-closed 缺项；ponytail：复用 `data_health` profile 输出 |
| R3G2-REP-P1-02 | **guardrail 测试全 mock**    | `test_r3g02AdversarialAudit_runtimeImportScanBlocks` 等 monkeypatch `_scan_runtime_guardrails`                                   | 至少 1 项真实扫描集成测（或向 `tests/fixtures/` 写临时坏文件并扫描）；保留 mock 测边界                                |
| R3G2-REP-P1-03 | **§3.4 provider 元数据不全** | `_audit_provider_metadata` 仅查 catalog/registry 存在与 domain                                                                   | 补查 auth、`production_default_enabled`、enabled-by-default、default cap（读 registry/capabilities YAML）             |
| R3G2-REP-P1-04 | **§3.3 行数/计数未实质校验** | 仅 `required_report_fields` 键存在，不查 `raw_row_count`/`staged_row_count`/`sandbox_clean_row_count` 合理性与 validation 计数   | bar 源 dry_run 允许 0 clean 但须显式 WARN；metadata 源须 staged>0；加断言测试                                         |

## P2 — MEDIUM

| ID             | 项                                  | 证据                                                                                             | 修复要求                                                                         |
| -------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| R3G2-REP-P2-01 | **缺 agent_triggered_write 对抗测** | §7 要求；仅契约 `block_if` 静态测                                                                | 真实或 fixture 触发 `agent_triggered_write_path` 的审计测                        |
| R3G2-REP-P2-02 | **缺 gate_bypass 对抗测**           | 契约 `write_manager_or_db_validation_gate_bypass`；无专门测试                                    | 合成 `production_mutation_allowed=true` / strategy metrics 报告测 BLOCK          |
| R3G2-REP-P2-03 | **audit CLI 无 DATA_ROOT 路径测**   | R3G-01 有 `test_RehearsalCli_dataRootProductionDbPathRejected`；audit 仅 `DEFAULT_PRODUCTION_DB` | 补 `config.DATA_ROOT` 生产 duckdb CLI 拒绝测                                     |
| R3G2-REP-P2-04 | **adhoc DH 重实现未查**             | 任务卡 §3.1 第三条                                                                               | 报告若缺 `data_health_summary.gate_rationale` 且非 R3F profile 路径 → BLOCK/WARN |
| R3G2-REP-P2-05 | **evidence_dir 缺失不 BLOCK**       | `run_adversarial_audit` 在 report 存在时 evidence_dir 不存在仍可能 PASS                          | evidence_dir 非目录 → BLOCK `missing_rehearsal_report` 或新 code                 |
| R3G2-REP-P2-06 | **fred 授权 posture 未审计**        | capabilities 要求 user authorization                                                             | 审计 fred 源是否 `requires_user_authorization` 与报告一致                        |

## P3 — LOW

| ID             | 项                                              | 证据                                                    | 修复要求                                                                |
| -------------- | ----------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------- |
| R3G2-REP-P3-01 | **`__init__.py` 未导出 audit API**              | 仅导出 rehearsal runner                                 | 导出 `run_adversarial_audit` / `AuditResult` 或 ponytail 注释刻意不导出 |
| R3G2-REP-P3-02 | **`AuditResult.serialize` 无效枚举检查**        | `if self.decision not in AuditDecision` 对 StrEnum 恒真 | 删除死代码或改为 contract 校验                                          |
| R3G2-REP-P3-03 | **guardrail 扫描与 contract_gate_support 重复** | `_scan_runtime_guardrails` 镜像测试 helper              | ponytail 注释天花板或提取共享函数（最小）                               |
| R3G2-REP-P3-04 | **`write_audit_decision` 内联 import json**     | `audit_decision.py:96`                                  | 顶层 import                                                             |
| R3G2-REP-P3-05 | **测试 autouse ResourceGuard mock 重复**        | 与 R3G-01 测试相同 fixture 模式                         | 提取共享 fixture 或注释范围                                             |

## 验证门（修复后）

```bash
uv run pytest tests/test_round3g_pre_production_adversarial_audit.py -q
uv run pytest tests/test_reference_adoption_guardrails.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py
```

**合并门：** `audit-repair-closure.md` 全部 R3G2-REP-\* = CLOSED
