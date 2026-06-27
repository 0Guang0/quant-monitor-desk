# Spec-Driven Development — R3H-01（Plan 2b）

> 契约收敛摘要 · 非 Execute 正文

## 权威契约

| 契约                                 | 用途                            |
| ------------------------------------ | ------------------------------- |
| `source_capability_contract.yaml`    | fetch port 操作与字段           |
| `source_route_contract.yaml`         | READY/DISABLED 路由             |
| `datasource_service_contract.yaml`   | DataSourceService 边界          |
| `data_quality_rules.yaml`            | DH / 宏观序列规则               |
| `layer5_evidence_contract.yaml`      | §9.7 smoke 字段                 |
| `reference_adoption_guardrails.yaml` | L2 迁 port 护栏                 |
| `sandbox_clean_write_contract.yaml`  | 3G promote 只读参考（不写主库） |

## 本任务新增/变更契约面

1. **`official_macro_evidence_v1`** — 文档化于 `official_macro.py` + 测试；与 `source_capabilities.fred.macro_series.fields` 对齐。
2. **registry** — 六源 `status` 从 `proposed_disabled_source` / `sandbox_candidate` → `READY_WITH_EVIDENCE` 或 ADR 登记。
3. **route** — 每源 READY 正例 + DISABLED 负例（`enabled_by_default: false`）。

## 验收映射（spec → test）

| 契约条款          | 测试锚点                                            |
| ----------------- | --------------------------------------------------- |
| fred fields       | `test_official_macro_adapters -k evidence_contract` |
| route DISABLED    | `test_source_route_planner -k fred`                 |
| guardrails        | `test_reference_adoption_guardrails`                |
| Layer5 provenance | `test_official_macro_adapters -k layer`             |

**Phase 2b complete**
