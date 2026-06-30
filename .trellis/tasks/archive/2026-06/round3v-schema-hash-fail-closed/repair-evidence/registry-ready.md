# Registry-ready — B3V-DATA `VR-DATA-001`（defer 三件套）

> **Policy:** 本分支 **禁止** 直接 commit `AUDIT_DEFERRED_REGISTRY.md` / `UNRESOLVED_ISSUES_REGISTRY.md` / `RESOLVED_ISSUES_REGISTRY.md`。  
> 主会话 §7.3 批处理 proposed delta。

## 分支交付面（Execute + Repair）

| 能力                                      | 状态     | 证据                                                         |
| ----------------------------------------- | -------- | ------------------------------------------------------------ |
| 结构化 SUCCESS 必填 `schema_hash`（契约） | **DONE** | `specs/contracts/data_adapter_contract.md`                   |
| CSV/Parquet/JSON 有界 infer               | **DONE** | `skeleton_base.py` + adapter 测试                            |
| ValidationGate 缺 hash fail-closed        | **DONE** | `validation_gate.py` + gate 测试（含三后缀 + registry 回退） |
| B3V-AUD-05 负向保全                       | **DONE** | `test_schemaHashDriftWithoutApproval_rejects` 等未削弱       |

## B02-DATA-05 — 主会话闭合（registry 三件套）

| 字段           | 值                                                                      |
| -------------- | ----------------------------------------------------------------------- |
| ID             | `B02-DATA-05` / `VR-DATA-001` registry 行                               |
| Owner          | 主会话 coordinator（`BATCH_3V_COORDINATOR_PLAYBOOK.md` §7.3）           |
| Phase          | Batch 3V merge 后 + `B3V-C05` REG 分支协同                              |
| Runtime slice  | **本分支已闭合**（fail-closed 行为面）                                  |
| Registry slice | **DEFER** — schemaless 源登记、source_registry 字段、COVERAGE §8 行更新 |

### Proposed delta（coordinator 应用）

```yaml
VR-DATA-001:
  status: PARTIAL_RESOLVED_RUNTIME
  branch: fix/round3v-schema-hash-fail-closed
  evidence:
    - .trellis/tasks/round3v-schema-hash-fail-closed/research/execute-evidence/
    - .trellis/tasks/round3v-schema-hash-fail-closed/repair-evidence/zero-open-signoff.md
  remaining_for_B02-DATA-05:
    - source_registry schemaless 标记与 gate 正向豁免测（G-02）
    - 非 skeleton fetch_log 写入路径 integration（G-05 / OP-01）
  closure_test: >
    B3V-C05 merge 后：registry 行 RESOLVED 或 precise re-defer；
  G-02 正向用例绿；UNRESOLVED_ITEM_TASK_COVERAGE §8 B3V-C02 更新。

commit_policy: proposed_only_no_direct_registry_commit
coordinator_status: COORDINATOR-QUEUED
```

## 未改文件（负向边界）

- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`（§8 行由主会话更新）
