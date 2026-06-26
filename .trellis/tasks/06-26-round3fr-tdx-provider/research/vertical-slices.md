# Vertical Slices — R3FR-03 (Phase 3.5 /to-issues)

> 工单 ID = TDX-R3FR-01..07；Execute 不得合并为单 PR 水平堆砌（Batch 3F-R adversarial 精神）

| ID          | 标题                 | 建设内容                                                                                 | 验收标准                                                     | 依赖  | 证据                   | 测试                                          |
| ----------- | -------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ----- | ---------------------- | --------------------------------------------- |
| TDX-R3FR-01 | Provider port 包骨架 | 新建 `fetch_ports/` 包 + `tdx_pytdx_port.py`；optional `pytdx` import；`DISABLED_SOURCE` | RED: 无 port 模块；GREEN: 缺 pytdx 抛 PortError 不崩溃       | Boot  | —                      | 新/扩 port unit                               |
| TDX-R3FR-02 | Normalizers          | 新建 `normalizers/tdx.py`；三操作 raw→manifest                                           | RED: manifest 缺 fields/hash；GREEN: 与 adapter builder 对齐 | 01    | —                      | normalizer tests                              |
| TDX-R3FR-03 | 三操作 + caps 拒绝   | port 实现 security_list / equity daily / index daily；拒绝 minute & full-market & 超 cap | RED: 超 cap 仍成功；GREEN: `TDX_PROBE_REJECTED` 或 PortError | 01–02 | —                      | `test_tdx_manual_probe` 子集                  |
| TDX-R3FR-04 | 授权与 live 门       | port 要求 authorization 对象；`USER_AUTH_REQUIRED` 无授权                                | RED: 无授权联网；GREEN: gate + port 一致                     | 03    | —                      | `test_tdx_live_manual_probe_authorization.py` |
| TDX-R3FR-05 | Probe 编排瘦身       | `tdx_manual_probe` 调 port；`TdxPytdxProbeFetchPort` 委托                                | RED: 编排内联 pytdx；GREEN: 编排无直连 TdxHq_API             | 03–04 | mocked comparison json | `test_tdx_manual_probe.py` 全绿               |
| TDX-R3FR-06 | Registry caps        | 更新 `source_registry` + `source_capabilities` caps/notes                                | RED: caps 与任务卡不一致；GREEN: `test_source_capabilities`  | 05    | proposed delta yaml    | `test_source_capabilities.py`                 |
| TDX-R3FR-07 | Guardrails 收尾      | `reference_adoption_guardrails`；无 `参考项目/**` import                                 | RED: guard 失败；GREEN: 两 guard 模块绿                      | 05–06 | —                      | `test_reference_adoption_guardrails.py`       |

## Before / After（Coordinator Playbook §4）

| 自研薄轮       | Before                                     | After                                     |
| -------------- | ------------------------------------------ | ----------------------------------------- |
| TDX downloader | `TdxPytdxProbeFetchPort` 内联 pytdx        | `fetch_ports/tdx_pytdx_port.py` 自有 port |
| 规范化         | `adapters/tdx_pytdx.build_*_manifest` 散落 | `normalizers/tdx.py` + adapter 薄封装     |
| 探针           | 编排 + fetch 混合                          | `tdx_manual_probe` 仅编排 + evidence      |
| 兼容           | gate 禁止 `TdxPytdxProbeFetchPort` 直 live | 薄委托或等价 forbidden 语义保持           |

## 默认 caps

见 `research/plan-boot.md` §默认 caps。
