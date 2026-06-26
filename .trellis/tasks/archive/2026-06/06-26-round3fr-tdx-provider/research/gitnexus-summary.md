# GitNexus Summary — R3FR-03 (Phase 1b)

> Plan 期基于代码侦察 + 符号 grep；Execute 每步改 symbol 前须正式 MCP `impact()`。

## Query / 符号锚点

| 概念             | 发现                                                                                   |
| ---------------- | -------------------------------------------------------------------------------------- |
| TDX fetch 入口   | `TdxPytdxProbeFetchPort.fetch_payload` — `interface_probe_fetch_ports.py`              |
| 探针编排         | `run_tdx_manual_probe` · `run_tdx_live_manual_probe` — `tdx_manual_probe.py`           |
| 授权门           | `validate_tdx_live_manual_probe_authorization` — `tdx_live_manual_probe_gate.py`       |
| Adapter skeleton | `TdxPytdxAdapter` + `build_*_manifest` — `adapters/tdx_pytdx.py`                       |
| Registry         | `tdx_pytdx` — `source_registry.yaml:95` · `source_capabilities.yaml:337`               |
| 测试             | `tests/test_tdx_manual_probe.py` · `tests/test_tdx_live_manual_probe_authorization.py` |
| 历史证据         | `.trellis/tasks/round3-tdx-manual-probe/execute-evidence/*`                            |

## Impact 预判（Execute 前须正式 `impact()`）

| 符号/模块                                 | 变更类型   | 风险                                 |
| ----------------------------------------- | ---------- | ------------------------------------ |
| `TdxPytdxProbeFetchPort`                  | 瘦身为委托 | **MEDIUM** — gate 禁止直接 live 入口 |
| 新建 `TdxPytdxFetchPort`（拟名）          | 新增       | LOW                                  |
| `tdx_manual_probe`                        | 重构调用链 | **MEDIUM** — 多测试绑定              |
| `tdx_live_manual_probe_gate`              | caps 对齐  | LOW–MEDIUM                           |
| `source_registry` / `source_capabilities` | caps 更新  | LOW — 独占 `tdx_pytdx` 行            |
| `interface_probe_fetch_ports`             | 共享文件   | **MEDIUM** — Playbook 文件锁         |

## 建议

1. **新建** `datasources/fetch_ports/tdx_pytdx_port.py` + `datasources/normalizers/tdx.py`，勿在 `interface_probe_fetch_ports` 继续堆逻辑。
2. `TdxPytdxProbeFetchPort` 保留为薄兼容层或显式 deprecated 委托，满足 gate `FORBIDDEN_LIVE_ENTRYPOINTS` 语义。
3. Execute 改 `tdx_manual_probe` 前先 `impact({target: "run_tdx_manual_probe", direction: "upstream"})`。
4. 提交前 `detect_changes({scope: "compare", base_ref: "master"})`。
