# Round 2 Batch A — 需求与可验证规格

> 复杂任务薄索引 · 全文见 `MASTER.plan.md` §1–3、§2 AC 表

## Goal（brainstorm · trellis-brainstorm）

建立 Round 2 第一批可运行底座：源注册 + Adapter 契约 + fetch 审计日志；为 Batch B–D 提供稳定模块边界。

## 已确认事实（仓库/用户 · 非用户问答）

- Round 0/1 已完成；基线 **93** tests
- 路径：`backend/app/datasources/`（architecture 07 + DECISIONS）
- 四批次 Execute；本批 = 011+012
- `StubValidationGate` 本批不替换

## Requirements

1. migration **004**（`004_ingestion_sources.sql`）：`source_registry` + `fetch_log`（003 = `resource_guard_metrics`）
2. YAML 加载 + Primary/Validation/FallbackPolicy；拒绝 Shadow/Emergency
3. FetchRequest/FetchResult 符合 `data_adapter_contract.md`
4. 失败 fetch 也必须写 `fetch_log`
5. BaseDataAdapter 不写 clean 表

## Acceptance Criteria（spec-driven-development · 见 MASTER §2）

- [ ] AC-1..AC-8 全部可追溯至 §8 测试与 §10 命令

## Out of scope

- Vendor adapter 实现、Orchestrator、Validator、Polars、真实联网

## 批准

Plan **v1.3**：双 agent 对抗审计 remediation 完成 → `research/adversarial-audit-remediation.md`。**待用户确认** → Execute §8。
