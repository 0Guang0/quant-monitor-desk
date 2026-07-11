# task-01 执行文档权威索引（缝隙关闭）

> **日期：** 2026-07-12（严格口径：06∥07 **Execute CLOSED**；F05-A 测债已关；G1-02/R4 仍 OPEN）  
> **用途：** 最终执行计划集合 + 归档指向；同主题冲突时 **层级高者** 为准。  
> **退役产物：** 已迁入 [`归档/`](归档/README.md)（只读，不指挥实现）。

---

## 1. 权威层级（高 → 低）

| 层                      | 文件                                                                                                                                                                                | 角色                                            | 执行时                                            |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------- |
| **L0 design**           | `docs/decisions/design/ADR-017-*.md` · `ADR-018-*.md` · `docs/modules/design/data_sources.md` §5.2.1 · 其余 `MIGRATION_MAP` 索引 design                                             | 产品/架构 SSOT                                  | **只读遵守**；改须用户审阅 + ADR/promote          |
| **L1 跨模块门**         | `gate1-integration-spec.md`                                                                                                                                                         | Gate 1 切片、阻塞边、跨 task 验收               | G1-02～G1-08 顺序以此为准                         |
| **L2 本票 R4 计划**     | `task_plan.md`                                                                                                                                                                      | 工作包、R1–R10、依赖图、allow-list、关账条件    | 模块级进度与范围                                  |
| **L3 G1-02 防漂移**     | `g1-02-execution-brief.md`                                                                                                                                                          | 入口 ID 全表、两层契约、删除顺序、禁令、验证 §7 | **开 G1-02 / WP3～4x 必读**；细节优先于 L2 旧措辞 |
| **L4 接线事实**         | `g1-01-wiring-inventory.md`                                                                                                                                                         | 正式入口盘点（Plan r6 READY）                   | G1-02 清债对照表；**不是**实现规格                |
| **L5 决策痕迹**         | `decision-map-enable-seam.md`                                                                                                                                                       | #1–#4 已决议索引 → ADR-018                      | 查「为什么」；不另开启用形状票                    |
| **L6 台账**             | `findings.md`（含 **F05-A node-id 表**）· `progress.md` · `note.md` · `docs/quality/待修复清单.md` · [`PROJECT_IMPLEMENTATION_ROADMAP.md`](../../PROJECT_IMPLEMENTATION_ROADMAP.md) | 问题/进度/执行裁定/阶段外置双登记               | 关账用；不替代 L0–L3                              |
| **证据（非开工 SSOT）** | `completion-check-plan-g1-01-r6.md` · `completion-check-audit.md`                                                                                                                   | G1-01 Plan 关账；模块 R4 Audit（仍 OPEN）       | 证明历史结论；≠ 实现规格                          |

**冲突裁决：** design > brief（G1-02 细节）> task_plan 范围措辞 > inventory 事实表。

---

## 2. 最终执行计划集合（父目录保留）

开工只带：

1. 本索引 · `README.md`
2. `task_plan.md`（L2）
3. `gate1-integration-spec.md`（L1）
4. `g1-02-execution-brief.md`（L3）
5. `g1-01-wiring-inventory.md`（L4）
6. `decision-map-enable-seam.md`（L5，可选）
7. design：ADR-017 / ADR-018 / `data_sources.md` §5.2.1（L0）
8. `findings.md` + `progress.md` + `note.md`（执行阶段现场裁定）
9. 本地票：`.scratch/task-01-g1-02-enable-seam/`（不发 GitHub）

---

## 3. 已归档（见 `归档/`）

旧 Plan r1–r5、早期 `completion-check-plan.md`、`g1-01-increment-close`、`ADR-018-proposed` 指针、research / adversarial 快照、fred-builder、architecture HTML。明细见 [`归档/README.md`](归档/README.md)。

---

## 4. 依赖顺序（已确认）

```text
G1-01 READY
    ├── WP1 Capability          ⎫ 可并行（票 01/02/03）
    ├── WP2 macro_supplementary ⎭
    └── WP3：3A 问开关 → 3B 安检 → 3C 测试+3-OBS
              ├── 4a E-INC-*     ⎫
              ├── 4b E-CLI-20    ⎬ 票 06∥07∥08 并行
              └── 4x bridge      ⎭
                    └── 票 09 G1-02 证据 → 票 10 FRED 合并（G1-08）
                          └── 4c = G1-03～05 → 4d → 4e → WP5 → WP6
```

**禁令：** 未落地问开关禁止删 ESR；4c 不得抢在 4a/4b 前宣称策略同路。

**台账指针（2026-07-12）：** 票 **06/07 Execute CLOSED**（CC 对象 F/G）；F05-A **测债已关**；开放 F06/F07/F08/F09 待复验/F10–F12/F03 余 4x/FRED 合并。**06/07 CLOSED ≠** G1-02 ≠ R4。

---

## 5. 本地票

见 [`.scratch/task-01-g1-02-enable-seam/README.md`](../../.scratch/task-01-g1-02-enable-seam/README.md)。**Frontier：** 06∥07 = `impl-green-pending-cc`；可选 ∥ 08。
