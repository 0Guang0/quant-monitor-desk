# Plan Boot — R3H-08 24-Source Live Productization

## 0. 开工顺序（用户纠正 @ 2026-06-29）

1. **先** 参考项目调研（三等级 L1/L2/L3）→ `reference-adoption-r3h08.md`
2. **再** 实现方案与架构设计 → `live-tier-architecture.md`
3. **后** Plan v4.1 加固 skill 与 5e 打包（本目录后续产出）

## 1. 活卡 §1–§3 摘要（不迁入 research 全文）

| 项           | 内容                                                                               |
| ------------ | ---------------------------------------------------------------------------------- |
| **Wave**     | 2 · BATCH_3H · R3H-08A–D（本 Trellis 票合并为单 Execute 包，串行 08C→08A→08B→08D） |
| **目的**     | 24 源 env-gated **产品 live**；经 `DataSourceService`；Tier A/B/C 正确落库         |
| **Module**   | C3（主）· A3 · B\* · G6                                                            |
| **评级**     | `R3_STAGED_FIXTURE_CLOSED` → `R4_SANDBOX_REAL_DATA_OR_REHEARSAL`                   |
| **前置**     | R3H-10 CLOSED · R3H-07 CLOSED @ `94ccd326` · R3H-06 CLOSED                         |
| **不在范围** | web_search 真 API · 新 migration · Round4 API                                      |

活卡路径（待 freeze）：`docs/implementation_tasks/.../R3H_08_LIVE_PRODUCTIZATION.md`（Plan 5e 前创建）

## 2. 已读设计文档

- `R3H_PASS_EXECUTION_PLAN.md` §2–§4
- `BATCH_3H_COORDINATOR_PLAYBOOK.md` §2.3 Wave 2
- `docs/quality/production_live_pilot_policy.md`（rehearsal 与产品边界）
- R3H-10 archived `00-EXECUTION-ENTRY.md`（C2 SSOT · R3H-08 defer 表）

## 3. 调研产出（必做 · 已完成）

| 文件                                   | 状态                      |
| -------------------------------------- | ------------------------- |
| `research/reference-adoption-r3h08.md` | ✅ 三等级 + 24 源表       |
| `research/live-tier-architecture.md`   | ✅ 组件 + 子轨 + 测试策略 |

Phase P0 complete（调研门禁通过；Plan 加固待续）
