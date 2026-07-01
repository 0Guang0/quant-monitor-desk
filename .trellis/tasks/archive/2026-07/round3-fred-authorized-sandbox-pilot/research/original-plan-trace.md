# Original Plan Trace — B01-FRED

| 来源                                               | MASTER AC      | 备注                                                  |
| -------------------------------------------------- | -------------- | ----------------------------------------------------- |
| `R3E_fred_authorized_sandbox_pilot.md` §2 预期结果 | AC-FRED-01..07 | forward SSOT                                          |
| `R3E` §9 垂直切片 FRED-01..06                      | §8.1–8.6       | FRED-05 纠偏：pilot-local health，非 data_health 主体 |
| `R3E` §11 验收命令                                 | §10 Tier A     | 含 `test_ops_data_health.py` 回归-only                |
| `BATCH_01_TASK_CARD_MANIFEST.md` §3 依赖           | §1.3           | C01 → C02                                             |
| `BATCH_01_HARDENING_RULES.md` §3–§7                | §0 授权 · §3   | live 授权 YAML                                        |
| `PROMPT_04` (B01-L04)                              | AC-FRED-06     | macro_supplementary ≠ FRED                            |
| `018B` (B01-L05)                                   | §3.2 defer     | sandbox gate                                          |
| `R3Y_readonly_data_health_v1.md` (B01-L03)         | §3.2           | 只读模式参考；v2 归 DH2                               |
| Playbook §8.5 B01-FRED PASS                        | §10            | 验收命令块                                            |
| `AUDIT_DEFERRED_REGISTRY.md` `B2.5-O-05`           | AC-FRED-06     | 关闭/re-defer 决策                                    |

## WL 白名单追溯

| WL 产出（B01-C01）                                          | FRED 用法                                     |
| ----------------------------------------------------------- | --------------------------------------------- |
| `specs/model_inputs/layer1_macro*.yaml`（预期）             | Execute SSOT：P0 series 列表                  |
| `R3D_model_input_whitelist.md` §9 WL-01                     | Plan 期只读：DGS10/T10Y3M/VIXCLS/SP500/DFII10 |
| Layer1 axis specs `environment_axis_indicator_spec.yaml` 等 | Plan/Execute 回退 SSOT                        |

## Batch map item

`ROUND3_BATCH_IMPLEMENTATION_MAP.md` — Batch 01 · FRED sandbox pilot · Track A merge #3。
