# 垂直切片工单 — R3FR-05（Phase 3.5 to-issues）

| Slice ID | 交付物                                                             | 依赖      | AC               |
| -------- | ------------------------------------------------------------------ | --------- | ---------------- |
| SLICE-A  | `tests/test_provider_catalog.py` 结构/enum/registry 覆盖 RED→GREEN | —         | AC-1, AC-2       |
| SLICE-B  | `provider_catalog.yaml` 全量 25 条目 + registry 补 2 行            | SLICE-A   | AC-1, AC-3, AC-4 |
| SLICE-C  | `provider_catalog.py` loader                                       | SLICE-B   | AC-6             |
| SLICE-D  | contract yaml 交叉引用                                             | SLICE-B   | AC-7             |
| SLICE-E  | guardrails R3FR-05 closure 测试                                    | SLICE-B   | AC-5, AC-6       |
| SLICE-F  | full pytest + loop_maintain merge gate                             | SLICE-A–E | AC-6, AC-7       |

映射 EXECUTION_INDEX §9.1–9.6。
