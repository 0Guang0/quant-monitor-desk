# Research: VR-OPS-001 / VR-WRITE-001 closure test 追溯

- **Query**: 每个 owned VR-\* 在 Plan/测试中是否有明确 closure test（非 registry 行闭合）
- **Scope**: internal
- **Date**: 2026-06-28

## Findings

### VR → AC → 测试 → 切片

| VR ID          | MASTER AC              | 切片               | 测试文件                                 | test\_\*                                                 | closure 语义                             |
| -------------- | ---------------------- | ------------------ | ---------------------------------------- | -------------------------------------------------------- | ---------------------------------------- |
| `VR-OPS-001`   | AC-OPS-DRIFT           | OPS-01, OPS-02     | `tests/test_contract_drift_ops_write.py` | `test_opsInspect_keyTables_matchContract`                | YAML key_tables 与 `KEY_TABLES` 全量一致 |
| `VR-OPS-001`   | AC-OPS-DRIFT           | OPS-02             | 同上                                     | `test_opsInspect_deferredMapping_matchContract`          | deferred_item_mapping 全量一致           |
| `VR-WRITE-001` | AC-WRITE-SPLIT         | WRITE-01, WRITE-02 | 同上                                     | `test_writeContract_implementedModes_matchWriteManager`  | `implemented_modes == SUPPORTED_MODES`   |
| `VR-WRITE-001` | AC-WRITE-RESERVED      | WRITE-03           | 同上                                     | `test_writeManager_reservedModes_rejectWithoutWrite`     | 每 reserved `ValueError` + 行数 0        |
| `VR-WRITE-001` | AC-WRITE-SPLIT（增补） | WRITE-02           | 同上                                     | `test_writeContract_reservedModes_matchUnsupportedModes` | `reserved_modes == UNSUPPORTED_MODES`    |

### 审计 INDEX 路由

`docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md`:

- `VR-OPS-001` → B02_01 → `fix/round3v-contract-drift-write-modes` → **contract drift test**
- `VR-WRITE-001` → B02_01 → same → **implemented/reserved write modes**

### RED/GREEN 证据路径（§9）

| 切片     | 证据                                                      |
| -------- | --------------------------------------------------------- |
| OPS-01   | `research/execute-evidence/9.1-red.txt` / `9.1-green.txt` |
| OPS-02   | `9.2-red/green.txt`                                       |
| WRITE-01 | `9.3-red/green.txt`                                       |
| WRITE-02 | `9.4-red/green.txt`                                       |
| WRITE-03 | `9.5-red/green.txt`                                       |

### Registry 闭合

- **Plan 禁止**：agent 不得直接 CLOSED registry 三件套。
- B02-CLOSE-01 → 主会话 Batch 收口；技术证据由上述 pytest + execute-evidence 提供。

## Caveats / Not Found

- `test_writeContract_reservedModes_matchUnsupportedModes` 已入 MASTER §5.3 / §9.4（2026-06-28 Plan QC 修补）。
