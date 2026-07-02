# Plan Context — R3-DCP-06

## §5.2 Must-read manifest（Execute Boot）

| path                                                                   | manifest  | for                 |
| ---------------------------------------------------------------------- | --------- | ------------------- |
| `docs/decisions/ADR-029-dcp06-layer1-five-axis-clean-read.md`          | must-read | S00+                |
| `R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md`                                  | must-read | BOOT                |
| `docs/modules/layer1_global_regime_panel.md`                           | must-read | S00+                |
| `specs/layer1_axes/restructured_axes_v1_1/common/common_axis_rules.md` | must-read | S01–S05             |
| `specs/contracts/layer1_axis_contract.yaml`                            | must-read | S00+                |
| `specs/model_inputs/layer1_source_whitelist.yaml`                      | must-read | S06                 |
| `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md`        | must-read | S00（clean 表映射） |
| `research/reference-adoption-dcp06.md`                                 | must-read | RED 前              |
| `docs/quality/待修复清单.md` §4                                        | must-read | S06 台账            |

## §5.3 Context pack

Generated: `context_pack.json` via `context_router.py --task .trellis/tasks/wave4-r3-dcp-06-five-axis-clean`

Authority node: `layer1_axes` (G1, K2)

## Token budget notes

- 五轴 YAML：按轴切片只读对应 `*_indicator_spec.yaml`
- 不测全量 `test_layer1_observation_ingestion.py` 除非改 ingestion 桥

## Execute 禁止

- 改 `clean_write_targets.py` / incremental registry（DCP-05 所有权）
- 声称关闭 `B2.5-O-05` 或全链 `ACC-LAYER-E2E-LIVE-001`
