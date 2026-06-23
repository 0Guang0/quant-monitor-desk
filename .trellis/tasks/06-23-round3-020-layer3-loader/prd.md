# Round 3 020: Layer3 industry chain loader

## Goal

交付 staged-only 产业链五类 registry loader（chain/anchor/node/edge/cross-chain），执行 `layer3_loader_contract.yaml` 硬校验；为 `021` snapshot builder 提供 typed 配置加载结果。

## Requirements

- 遵循 `019` `sensor_loader.py` 的 `staged_fixture_only` 模式
- 校验：唯一 ID、边引用、anchor.node_id、event_only、P0 source_keys
- 禁止 production-live registry 路径与声称
- 禁止修改 layer2/4/5、lineage contract、production DB
- `R3-B2.75-REQ2-EM` 保持 DEFERRED

## Acceptance Criteria

- [ ] AC-020-1：五类 registry 从 staged fixture 加载为 `IndustryChainLoadResult`
- [ ] AC-020-2：违反 contract 硬规则时 fail-fast
- [ ] AC-020-3：`event_only` 私有公司不得作为普通日度价锚
- [ ] AC-020-4：`P0_CORE`/`P0_EVENT` anchor 须有 `source_keys`
- [ ] AC-020-5：非 `staged_fixture_only` 模式拒绝
- [ ] AC-020-6：Tier A 验收命令 exit 0

## Notes

- snapshot / lineage 写入 defer `021`
- Execute 前须用户/协调者批准 Plan freeze
