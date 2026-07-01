# OPEN-05 — observation_writer / roll_writer VR 绑定评估

**Verdict:** CLOSED (wont-fix + negative gate test)

## 评估结论

| Writer                    | 写入目标                                               | 是否产出 lineage envelope | VR 绑定需求                                                                                         |
| ------------------------- | ------------------------------------------------------ | ------------------------- | --------------------------------------------------------------------------------------------------- |
| `Layer2SnapshotWriter`    | `cross_asset_daily_snapshot` + `axis_snapshot_lineage` | **是**                    | **已实现** LIN-S4：`load_validation_report_provenance` + `assert_lineage_matches_validation_report` |
| `Layer2ObservationWriter` | `cross_asset_observation`                              | **否**                    | WriteManager `validation_report_id` gate only（行级观测，无 fetch/hash 列）                         |
| `Layer2RollEventWriter`   | `cross_asset_roll_event`                               | **否**                    | WriteManager `validation_report_id` gate only（事件表，无 lineage 列）                              |

## Wont-fix 理由

1. **R3Y-AUD-05 L05-W1/W2** 针对 **snapshot lineage** 漂移；观测与 roll 表在契约中 **不** 要求 `source_fetch_ids` / `source_content_hashes` 列。
2. 复用 L1 `SnapshotLineageBuilder.build_from_validation_report` 模式于 observation/roll writer 属 **过度工程**（无 envelope 可绑定）。
3. Fail-closed 已由 `DbValidationGate` 保证：缺失/失败 VR → write `FAILED`、无 SUCCESS audit（负向测见 `test_layer2RollEvent_rejectsMissingValidationReport`）。

## Residual

Production `fetch_log → VR` E2E for L2 observation path → owner **B01-023** / staged pilot track（与 `ADV-R3X-LINEAGE-001` DB 子范围一致）。
