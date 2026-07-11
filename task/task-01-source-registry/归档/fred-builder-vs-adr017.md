# 「fred 专用 builder」是什么？与 ADR-017 冲突吗？

> **日期：** 2026-07-11  
> **范围：** task-01 / Gate 1 · G1-02 启用策略接缝  
> **配套：** [架构深化报告 HTML](architecture-review-fred-enable-seam.html) · [决策地图](decision-map-enable-seam.md)  
> **结论先行：** 这是**当前代码与已 Accepted 设计（ADR-017）之间的实现冲突**；不是 ADR 自相矛盾。应**改架构（落地 overlay + 删内存绕过）**，而不是把 OVERRIDE 永久兼容成正式机制。

---

## 1. 「fred 专用 builder」字面意思

在清单 / 对话里说的「fred 专用 builder」，指的是代码里这一类函数：

- `build_fred_incremental_preview_service`
- `build_fred_incremental_service`
- （以及 watermark / `execute_binding` 编排）

**它真正「专用」的是 FRED 增量编排**，不是另一套启用策略：

| 真正专用（合理深度） | 并不是专用（与宏源相同） |
|----------------------|--------------------------|
| `FredIncrementalFetchProxy`：按 series 注入 watermark | 启用：仍调 `enabled_source_registry("fred","macro_series")` |
| P0 series whitelist / binding | 平台门：经 `load_incremental_route_bundle` 强制 `_platform_allows=True` |
| 走 `execute_binding` 的增量执行壳 | 改 `is_enabled` / `get_domain_roles` 的内存补丁 |

### backfill 预览调用链（简化）

```text
qmd-data data backfill
  → _gold_path_backfill_route_preview
       ├─ fred + macro_series
       │    → build_fred_incremental_preview_service()
       │         → load_incremental_route_bundle(fred)
       │              → enabled_source_registry + 强制 platform
       └─ 其它金路径 source_id
            → 直接 enabled_source_registry + 强制 platform
```

因此：清单 E-CLI-20 写成「OVERRIDE-MEM（fred 专用 builder）」**形义错误**——容易让人以为只有 fred 在绕过；**非 fred 金路径同样 OVERRIDE**。这是 G1-01 盘点措辞问题（Plan r5 已记），与「要不要改 ADR」无关。

---

## 2. ADR-017 要的效果是什么？

权威：`docs/decisions/design/ADR-017-...md`（Accepted）

1. **稳定能力目录**（`source_registry`）≠ 运营开关；故障时不靠运行时改 YAML 记录。  
2. **持久化启用覆盖层（overlay）**：管理员经受控配置/CLI 改「是否允许参与路由」，可审计、可撤销。  
3. **task-01 责任明文：**「禁止调用方内存绕过」。  
4. CLI / 调度只能**读取**有效启用结果，不能 `__setattr__` / 换 `get_domain_roles` / lambda 开平台门。

当前仓库：**无** `source_activation_overlay` 实现（清单填 `none`）；正式路径大量走 `enabled_source_registry` + `_platform_allows = lambda: (True, None)`。

---

## 3. 这是「代码 vs 设计」冲突，还是别的意思？

用三分类说清楚：

| 类型 | 是否适用 | 含义 |
|------|----------|------|
| **(A) 仅清单写错** | **部分是** | E-CLI-20「fred 专用」夸大了差异；应改成「全金路径 OVERRIDE，fred 多一层编排壳」。 |
| **(B) 已排期实现债** | **主判是这个** | 设计已定（overlay）；代码仍是过渡 shim（T01-F03）；G1-02 / 工作包 3～4 要删绕过并落地唯一启用接缝。 |
| **(C) 设计与设计冲突 / 必须重写 ADR** | **否** | ADR-017 与「稳定 registry + overlay」一致；冲突的是**未实现的设计 vs 现存内存补丁**。 |

**一句话：**  
不是「ADR-017 写错了所以要强行兼容现在的 builder」；  
而是「现在的 builder/共享 override **故意偏离** ADR-017，属于已知债，应用架构改动消掉，而不是把 OVERRIDE 合法化」。

---

## 4. 要不要「强行兼容」？

| 做法 | 评价 |
|------|------|
| 长期保留 `enabled_source_registry` + 强制 platform，只给 fred 留专用壳 | **禁止**——与 ADR-017 / T01-F03 / G1-02 目标相反 |
| 短期：盘点诚实登记 OVERRIDE，G1-02 从共享根因一次删除 | **允许**（Plan 已这样安排） |
| 目标态：overlay 合成「有效启用」→ `SourceRoutePlanner` / CLI 只读；`FredIncrementalFetchProxy` 可保留为**编排**深模块 | **应对齐的架构改动** |

删除测试（deletion test）：若删掉 `enabled_source_registry`，复杂度不会消失，而会散回各 CLI——说明它**暂时**有杠杆，但是**错误接缝**上的杠杆；正确做法是把杠杆挪到 overlay resolver，再删掉 patch。

---

## 5. 架构词汇（与报告一致）

- **应有的 seam：** registry 基础状态 + overlay →「有效启用」接口；planner/CLI 只读。  
- **实际泄漏的 seam：** `macro_incremental_common.enabled_source_registry` / `load_incremental_route_bundle` 被 10+ 调用方共用。  
- **fred builder：** 浅包装 + 合理内部适配器（watermark proxy）；**启用策略深度为零**（副作用污染接口）。  
- **深化方向：** 一个深模块「有效启用解析」；删除各处内存 patch；fred 只保留编排接口。

---

## 6. 建议你怎么走（历史；**SUPERSEDED**）

> **状态：** 下列「先修清单 / proposed ADR」步骤已完成。当前以 design **ADR-018 Accepted**、G1-01 Plan **r6 READY**、[g1-02-execution-brief.md](g1-02-execution-brief.md) 为准。勿再按本节开工。

1. ~~先修清单（关 Plan r5）~~ → 已修并 r6 READY。  
2. **G1-02 实现：** 见 brief + `task_plan` 工作包 3～4x。  
3. **不要**为了让现有 dry-run 继续绿而把 OVERRIDE 写进 design。

**权威 ADR：** [`docs/decisions/design/ADR-018-enable-seam-two-layer-and-fred-merge-gate.md`](../../docs/decisions/design/ADR-018-enable-seam-two-layer-and-fred-merge-gate.md)。  
task 目录 [`ADR-018-proposed-enable-seam-two-layer.md`](ADR-018-proposed-enable-seam-two-layer.md) 仅为指针。台账：`T01-ENABLE-FRED-MERGE-001`。
