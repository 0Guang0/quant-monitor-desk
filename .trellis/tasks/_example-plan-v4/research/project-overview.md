# Project Overview — GitNexus 1a（样板）

**Query：** Plan v4.1 execution bundle / manifest generation

**Scope：** `.trellis/scripts/common/execution_index.py` · `plan_protocol.py`

**Findings：**

- v4.1 使用 `research/00-EXECUTION-ENTRY.md` 作为 Execute 路由入口
- `generate_manifests` 根据 `plan_protocol_version` 切换 slot2

**Caveats：** 样板任务无生产域逻辑
