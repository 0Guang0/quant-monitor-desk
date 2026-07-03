# R3X_ponytail_pilot_prep_bucket_a — Ponytail 桶 A（PROMPT_14 前置信任切片）

## 1. 任务性质

最小 ponytail + 行为修复切片，为 PROMPT_14 staged real-data pilot 准备 **可审计的 fetch/write/route 路径**。

**不是：** 69 项全量、不是 `live_pilot.py` 拆分（OP-01）、不是 ingestion/lineage 大 refactor。

## 2. 分支

| Field        | Value                                                 |
| ------------ | ----------------------------------------------------- |
| Branch       | `fix/round3-ponytail-pilot-prep-bucket-a`             |
| Base         | `master` @ `d1a15e4b`                                 |
| Worktree     | `../quant-monitor-desk-wt-fix-r3-ponytail-pilot-prep` |
| Merge target | `master`（协调者）                                    |

## 3. 必须闭合项（桶 A）

| ID    | 来源          | 最小修复目标                                                                                 |
| ----- | ------------- | -------------------------------------------------------------------------------------------- |
| DS-01 | ponytail scan | fetch_log **单点写入**（service 为 owner；adapter 默认不写 DB）                              |
| DS-02 | ponytail scan | `create_adapter` / `create_test_adapter` 去重（ponytail：单 `_build_adapter`）               |
| DS-03 | ponytail scan | production `fetch()` 不得隐式 `create_test_adapter`；test 路径仅显式 DI / fixture mode       |
| SC-02 | ponytail scan | `staged_evidence` WriteManager 旁路：契约测试 + 最小 runtime gate（`phase=` 或等价）         |
| OP-02 | ponytail scan | `interface_probe` 不得 import `live_pilot` 私有符号；抽 `ops/mutation_proof.py`（≤必要 LOC） |
| SY-04 | ponytail scan | sync fetch 与 ResourceGuard 统一 `_fetch_with_guard`（ponytail：一处 helper）                |
| VA-03 | ponytail scan | `as_text(None)` 语义统一（不返回字面量 `"None"`）                                            |
| DB-03 | ponytail scan | 若 `assert_can_write` / `assert_can_write_with` 仍镜像：合并为单入口（仅当 RED 证明仍重复）  |

已 CLOSED 项：先 RED 验证；若已绿则标 **ALREADY_CLOSED** + 回归测试，禁止重复大改。

## 4. Allowed files

- `backend/app/datasources/service.py`, `base_adapter.py`, `adapters/__init__.py`
- `backend/app/storage/staged_evidence.py`
- `backend/app/ops/interface_probe.py`, `backend/app/ops/mutation_proof.py`（新建，最小）
- `backend/app/sync/runners.py`（仅 SY-04 相关）
- `backend/app/validators/common.py`, `data_quality.py`, `source_conflict.py`（VA-03）
- `backend/app/db/validation_gate.py`（仅 DB-03 若需要）
- `tests/**`（新增/修改）
- `.trellis/tasks/fix-round3-ponytail-pilot-prep-bucket-a/**`

## 5. Forbidden

- 拆分 `live_pilot.py` 全文件（OP-01）
- `ingestion.py` / lineage 三重复制（L1/L2/SC P0）
- live network fetch、production DB 写入、default enable disabled sources
- 关闭 `R3-B2.75-REQ2-EM`
- 修改测试目的以换绿（可改断言实现，不可改测试所验证的行为契约）

## 6. 工程纪律（用户强制）

1. **TDD**：每项 RED → `execute-evidence/{id}-red.txt` → GREEN → `{id}-green.txt`
2. **Skills**：`/karpathy-guidelines`, `/testing-guidelines`, `/tdd`, `/ponytail` full
3. **测试注释**：每个新增/修改测试函数 docstring 必须含：**覆盖范围**、**测试对象**、**目的/目标**
4. **验收**：`python -m pytest -q` exit 0；定向 gate 见 §7
5. **无污染**：仅用 fixture/tmp sandbox DB；禁止连接生产 DuckDB 路径；禁止 live vendor fetch

## 7. Verification

```bash
python -m pytest tests/test_datasource_service.py tests/test_data_adapter_contract.py tests/test_r3x_data_source_routing_blockers.py -q
python -m pytest tests/test_sync_orchestrator.py tests/test_sync_jobs.py -q
python -m pytest tests/test_db_validation_gate.py tests/test_raw_store.py -q
python -m pytest tests/test_data_quality_validator.py tests/test_source_conflict_validator.py -q
python -m pytest tests/test_interface_probe_018c.py tests/test_batch275_live_pilot_gate.py -q
python -m pytest tests/test_r3x_ponytail_pilot_prep_bucket_a.py -q
python -m pytest -q
python scripts/check_doc_links.py
```

## 8. Deliverables

- `merge_gate_report.md`（桶 A 逐项 FIXED / ALREADY_CLOSED）
- `tests/test_r3x_ponytail_pilot_prep_bucket_a.py` 伞测
- Commit on branch；**不 merge/push**（协调者 merge）
