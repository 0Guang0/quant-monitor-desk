# Integration Ledger — R3FR-03（审计修复后）

## §3 must-read（不可内联）

见 `EXECUTION_INDEX.md` §3 全表（含 gate、编排、授权 MD、GLOBAL_RESOURCE_LIMITS、runtime_versions、staged_acceptance、playbook、integration-ledger）。

## R3FR-05 并行协议

- R3FR-03 **独占** `tdx_pytdx` `source_registry` / `source_capabilities` caps 与 `resource_caps`
- R3FR-05 provider-catalog 可增 catalog 元数据，**不得**改 tdx caps
- Playbook 合并序：TDX(3) → catalog(4)

## 新测试 catalog

Execute §9.7：`loop_maintain.py --fix` 登记 `tests/test_tdx_pytdx_port.py`。
