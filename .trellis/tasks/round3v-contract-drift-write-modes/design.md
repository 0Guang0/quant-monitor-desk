# Design — B3V-OPS

见 **MASTER.plan.md §4–6**。

- YAML loader 于 `db_inspector`（模块内私有）
- `write_contract` implemented/reserved 分栏

`skip_phase4_reason`: 三条全满足 — 无新 package/无跨 caller 新公共 API/无 schema migration。
