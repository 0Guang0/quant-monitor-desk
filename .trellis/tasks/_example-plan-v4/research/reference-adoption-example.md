# Reference Adoption — example（trellis-research 样板）

**Query：** 其他仓库如何组织 Execute 入口文档？

**Scope：** 本仓库 R3H-10 `research/00-EXECUTION-ENTRY.md`（结构参考，非 runtime）

**Date：** 2026-06-29

**Findings：**

- 双层索引：包内 ENTRY + 包外 EXTERNAL-INDEX §A/B/C
- 切片 AC 单一 SSOT：`to-issues-slices.md`

**Caveats：** 禁止将 `参考项目/**` 作为 runtime 依赖
