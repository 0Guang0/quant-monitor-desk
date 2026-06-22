# MASTER 计划 — Round 3 Batch 3 `019` Layer 2 Cross-Asset Sensor

> **Execute 入口** — staged-only downstream；**不得**声称 production-live readiness。

---

## 0. 元信息

| 字段 | 值 |
| ---- | -- |
| 任务 slug | `06-22-round3-019-layer2-sensor` |
| 分支 | `feature/round3-019-layer2-sensor` |
| 前置 gate | `R3-B3-STAGED-DOWNSTREAM-GATE` **CLOSED** |
| 目标合并 | `integration/round3` |

### Staged downstream limitations（§16 强制）

1. `BATCH3_STAGED_DOWNSTREAM_GATE.md` — staged-only
2. `final_registry_update.md` — ingestion staged，非 production-live
3. `018A_layer1_observation_ingestion_bridge.md` §13 — 无连续生产数据假设
4. `UNRESOLVED_ISSUES_REGISTRY.md` — `R3-B2.75-01` DEFERRED；`PILOT_FAIL_SOURCE`；`R3-B2.75-REQ2-EM`
5. `production_live_pilot_policy.md` — Batch 2.75 不解锁生产访问
6. `B2.5-O-05` DEFERRED — 不关闭 FRED primary
7. 仅 fixture-backed；无 live FRED / production DB / vendor writes
8. `tdx_pytdx` 禁止作 Layer2 生产源
9. D-09 — 不复制 Layer1 标准化字段

### Failure modes / 回滚

| 场景 | 处理 |
| ---- | ---- |
| ResourceGuard HARD_STOP | 中止 snapshot/observation 批处理；无部分写入 |
| validation_report 缺失 | WriteManager 拒绝；无 clean 写入 |
| mixed trade_date 批次 | fail-fast `CrossAssetObservationError` |
| roll_event=false | `Layer2RollEventWriter` 拒绝（禁止 silent switch） |
| 回滚 | 删除 sandbox DB；无 production migration 可逆 |

### 023A lineage 对接

- Layer2 lineage 写入共享表 `axis_snapshot_lineage`（`layer_id=layer2`）
- **不**修改 `snapshot_lineage_contract.yaml`（023A 写权限）
- `layer2_snapshot_lineage` 私有表已弃用

---

## 1. 目标

交付 registry / observation / daily snapshot / double_count_guard / roll event / lineage；staged-only。

## 2. 非目标（defer）

- Layer3/4/5、FastAPI、live fetch、production migration
- 模块 §7 staging→DQ→conflict 全流水线
- `cross_asset_signal_snapshot` / divergence

## 3. AC 摘要

| AC | 验证 |
| -- | ---- |
| AC-019-1 | registry loader + sandbox sync |
| AC-019-2 | double_count_guard |
| AC-019-3 | no_future_data（trade_time/as_of/fetch） |
| AC-019-4 | lineage + deterministic hash |
| AC-019-5 | roll event 持久化 |
| AC-019-6 | ResourceGuard |
| AC-019-7 | snapshot WriteManager |
| AC-019-8 | observation WriteManager |

## 4. 实现目录

- `backend/app/layer2_sensors/`
- `tests/test_layer2_sensor_loader.py`
- `tests/fixtures/layer2_cross_asset_registry_fixture.yaml`

## 5. 验收命令

```bash
uv run pytest tests/test_layer2_sensor_loader.py -q
uv run pytest tests/test_batch3_staged_downstream_gate.py -q
uv run pytest tests/test_batch25_production_data_gate.py -q
uv run pytest tests/test_production_live_pilot_policy.py -q
uv run pytest tests/test_round3_audit_registry_alignment.py -q
uv run pytest tests/test_unresolved_item_task_coverage.py -q
uv run python -m compileall backend/app/layer2_sensors tests
uv run ruff check backend/app/layer2_sensors tests/test_layer2_sensor_loader.py
```

---

## 8. 实现步骤（RED/GREEN）

### 8.0 Boot gate

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | implement.jsonl 全读；execute-boot；基线 pytest |
| 已执行 | [x] |
| RED 证据 | `research/execute-evidence/8.0-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.0-boot-reads.txt`, `8.0-green.txt` |

### 8.1 Registry loader

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | `CrossAssetRegistryLoader` + contract 枚举 + registry writer |
| 已执行 | [x] |
| RED 证据 | `research/execute-evidence/8.1-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.1-green.txt` |

### 8.2 double_count_guard

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | axis input display-only；for_model 阻断 |
| 已执行 | [x] |
| RED 证据 | `research/execute-evidence/8.2-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.2-green.txt` |

### 8.3 no_future_data

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | trade_time / as_of / fetch / trade_date 边界 |
| 已执行 | [x] |
| RED 证据 | `research/execute-evidence/8.3-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.3-green.txt` |

### 8.4 lineage

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | `axis_snapshot_lineage`；deterministic parameter_hash |
| 已执行 | [x] |
| RED 证据 | `research/execute-evidence/8.4-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.4-green.txt` |

### 8.5 roll event

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | `cross_asset_roll_event` + writer + snapshot 集成 |
| 已执行 | [x] |
| RED 证据 | `research/execute-evidence/8.5-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.5-green.txt` |

### 8.6 ResourceGuard

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | snapshot + observation 批处理前 guard |
| 已执行 | [x] |
| RED 证据 | `research/execute-evidence/8.6-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.6-green.txt` |

### 8.7 snapshot WriteManager

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | daily snapshot + lineage 经 WriteManager |
| 已执行 | [x] |
| RED 证据 | `research/execute-evidence/8.7-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.7-green.txt` |

### 8.8 observation WriteManager + final gates

| 字段 | 内容 |
| ---- | ---- |
| 做什么 | observation writer；PROMPT §7 gate matrix |
| 已执行 | [x] |
| RED 证据 | `research/execute-evidence/8.8-red.txt` |
| GREEN 证据 | `research/execute-evidence/8.8-green.txt` |

---

## 9. 四层测试

| 层 | 范围 | 命令 |
| -- | ---- | ---- |
| L1 | loader/guard/lineage/roll | `test_layer2_sensor_loader.py` |
| L2 | WriteManager 集成 | tmp_path DB tests |
| L3 | batch3/batch25 gates | PROMPT §7 |
| L4 | 全量回归 | `pytest -q` |

---

## 10. Tier

Tier A: §5 验收命令；Tier B: `pytest -q` 全绿。

---

## 11. Audit 交接

- [x] §8 全部步骤已执行
- [x] `validate-execute-handoff` 通过
- [x] merge_gate_report.md 更新
- [x] 无 production-live 声称

---

## 12. Execute Skill 冻结清单

| Skill | 本任务 | 已执行 |
| ----- | ------ | ------ |
| trellis-execute | 必做 | [x] |
| test-driven-development | 必做 | [x] |
| incremental-implementation | 必做 | [x] |
| karpathy-guidelines | 必做 | [x] |
| testing-guidelines | 必做 | [x] |
| spec-driven-development | 必做 | [x] |
| trellis-implement | 必做 | [x] |
