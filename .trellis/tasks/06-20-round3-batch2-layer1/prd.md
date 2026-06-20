# PRD — Round 3 Batch 2 Layer 1

> 详见 `MASTER.plan.md` §1–3。本文件为薄索引。

## 目标

交付 Layer 1 五轴 spec 加载与解释快照基础，使 Batch 3（`019` Layer 2）可依赖可追溯的 Layer 1 registry 与快照 lineage。

## 子交付物

- `017` — AxisSpecLoader + 三表 registry/profile 初始化
- `018` — feature + interpretation 快照引擎
- `R3-EARLY-LINEAGE-CONSUMERS` — 快照 lineage 字段与 validation_report 消费

## 非目标

- Layer 2–5、FastAPI Layer1 路由、全量生产抓取、Migration 008 CHECK

## 验收

- MASTER §2 AC 全绿 + §10 Tier A/B
