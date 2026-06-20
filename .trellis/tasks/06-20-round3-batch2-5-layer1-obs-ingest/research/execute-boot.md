# Execute Boot — 06-20-round3-batch2-5-layer1-obs-ingest

> **§8.0 Boot CLOSED · §8.1 Phase 0 CLOSED · PH-A0 PASS**  
> 下一会话：**跳过 Boot 与 Phase 0**，直接从 **§8.2 Phase 1** 开始（见 `research/execute-handoff.md`）。

## AC 摘要（来自 MASTER §2）

| AC                      | 状态                                             |
| ----------------------- | ------------------------------------------------ |
| AC-PRE                  | PASS — Batch 1/2 + R2.6 archived；基线 pytest 绿 |
| AC-P0-1..4              | **PASS** — §8.1 已交付                           |
| AC-P1..P4               | **NEXT** — §8.2 起                               |
| AC-GATE / HANDOFF / REG | **DEFERRED** — §8.6                              |

## §8 执行顺序

1. [x] §8.0 Boot — manifest、GitNexus、基线 pytest（2026-06-20）
2. [x] §8.1 Phase 0 — gate 测试 + `phase0_*` 证据 → **PH-A0 PASS**（对抗审计修补后）
3. [x] §8.2 Phase 1 inventory — **DONE** · PH-A1 PASS
4. [ ] §8.3 Phase 2 route dry-run — **下一会话入口**
5. [ ] §8.4–8.6 — 后续会话

## Red Flags（来自 MASTER §7）

- Layer1 直调 adapter → AC-P0-4 静态测试 **已绿**
- schema.sql 滞后 silent → **DEFERRED B2.5-O-02**（已分类）
- 跨阶段批量实现 → 禁止；§8.2 已闭合，下一会话仅 §8.3

## §10 验收命令清单

**§8.0 GREEN（已完成）：**

```bash
uv sync --locked
uv run pytest -q --co -q
```

**§8.1 GREEN（已完成）：**

```bash
uv run pytest tests/test_schema_migration.py tests/test_schema_contract.py tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py tests/test_data_cli_contract.py tests/test_ops_db_inspector.py tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py tests/test_sync_orchestrator.py tests/test_sync_jobs.py tests/test_vendor_fetch_e2e.py tests/test_layer1_ingestion_gates.py tests/test_write_manager.py tests/test_audit_remediation.py -q
```

**每步 GREEN 后全量（§8.2 起恢复）：**

```bash
uv run pytest -q
```

## Boot reads

- `implement.jsonl` 78/78 条已读（见 `execute-evidence/8.0-boot-reads.txt`）
- `integration-ledger.md` v3 已读
- E11a 只读对照：`sync/pipeline.py`、`orchestrator.py`、`runners.py`

## Phase 0 complete

**签字：** §8.0 + §8.1 于 2026-06-20 完成；PH-A0 PASS。  
**下一会话：** `research/execute-handoff.md` → §8.2 Phase 1 read-only inventory。
