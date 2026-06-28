# 原计划追溯 — B3V-C02 / VR-DATA-001

> **垂直切片 SSOT：** `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §4（B3V-C02 · B3V-DATA）— 与 `research/vertical-slices.md` / MASTER §8 对齐。

| 任务卡 | Manifest | Playbook | MASTER AC | 验证链 |
|--------|----------|----------|-----------|--------|
| `B02_02_schema_hash_fail_closed.md` | `B3V-C02` | B3V-DATA §3.3 | AC-DATA-01..05 | §8 DATA-01..04 → §9 → §6 |
| `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §4 | `B3V-C02` | Wave 0 INDEX | 同左 | DATA-01..04 竖条 |

## 切片映射

| 任务卡切片 | MASTER §8 ID | Execute | 说明 |
|------------|--------------|---------|------|
| B02-DATA-01 | DATA-01 | 是 | 契约 schema_hash 段 |
| B02-DATA-02 | DATA-02 | 是 | CSV/Parquet 有界推导 |
| B02-DATA-03 | DATA-03 | 是 | ValidationGate fail-closed |
| B02-DATA-04 | DATA-04 | 是 | 损坏文件负向 |
| B02-DATA-05 | — | **否** | Registry 闭合 → 主会话 |

## 引用文档

| 文档 | MASTER 锚点 |
|------|-------------|
| `data_adapter_contract.md` | §2.4, §8 DATA-01 |
| `write_contract.yaml` | §2.4, §8 DATA-03 |
| `data_quality_rules.yaml` SCHEMA_DRIFT | §3 S4 |
| `BATCH_3V_HARDENING_RULES.md` | §1.4, §1.5 |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | §0 VR 路由 |

## 纠偏

- Plan 阶段不实现 registry 闭合；Execute 完成后由主会话更新 `UNRESOLVED_ITEM_TASK_COVERAGE` 与 registry 三件套。
- Playbook §3.3 `adapters/registry.py` **仓库无此文件**；邻接 SSOT 为 `adapters/__init__.py` + `source_registry.py`（已入 MASTER/implement）。
