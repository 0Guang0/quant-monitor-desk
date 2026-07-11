# Handoff · task-01-source-registry

> **日期：** 2026-07-11（重写 · 票 03/3A 关账后）  
> **给：** 下一会话 / 新 agent（实现）  
> **本文件位置：** `task/task-01-source-registry/HANDOFF.md`（用户指定；非 OS temp）  
> **原则：** 不复制计划/ADR/票正文；只给加载顺序、状态、禁令与指针。

---

## 1. 下一会话目标（默认）

**Frontier：** 票 **04**（3B 安检）∥ 票 **05**（3C 测试夹具）— blocked-by 已关的 **03**；  
票 **01/02/03** 票级 AC 已关（≠ G1-02 / R4）。

正式代码：**TDD**；改 symbol 前 GitNexus `impact`。  
**禁止**把本 handoff、票 01–03 CLOSED 或 pytest 绿当成 R4 / G1-02 整包 / G1-08 完成。

**分支提示：** 实现多在 `feat/g1-02-ask-activation-03`（未合并）；新切片可续该分支或另开（勿两 agent 抢同一核心文件组）。

---

## 2. 上下文加载顺序（context-engineering）

按层级加载，**单次任务只带本切片**，勿一次塞满全目录：

| 序  | 加载什么                            | 路径                                                                                                                                                                   |
| --- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 规则                                | 仓库根 `AGENTS.md` · `agent-toolchain.md` · project-global / ponytail                                                                                                  |
| 2   | **执行索引（先读）**                | [`EXECUTION-DOC-INDEX.md`](EXECUTION-DOC-INDEX.md)                                                                                                                     |
| 3   | 本切片票                            | `.scratch/task-01-g1-02-enable-seam/issues/0N-*.md`（见 §1 选哪张）                                                                                                    |
| 4   | 计划细节                            | 票 01→`task_plan` 工作包 1；票 02→工作包 2；票 04→[`g1-02-execution-brief.md`](g1-02-execution-brief.md) §1.2 / §6 **3B**；票 05→brief §6 **3C** + inventory E-TEST-\* |
| 5   | design（只读）                      | ADR-017 · **ADR-018** · `docs/modules/design/data_sources.md` §5.2.1                                                                                                   |
| 6   | 已落地问开关（改消费方时）          | `backend/app/datasources/activation_overlay.py` · `tests/test_activation_overlay.py` · migration `017_source_activation_overlay.sql`                                   |
| 7   | 入口对照（清 OVERRIDE / 3B 接线时） | [`g1-01-wiring-inventory.md`](g1-01-wiring-inventory.md) 相关 ID 行                                                                                                    |
| 8   | 将改源码 + 同类 pattern + 对应测试  | 见票；`impact` 后再动                                                                                                                                                  |
| 9   | 失败输出                            | 只贴失败断言/栈，不贴整份 pytest                                                                                                                                       |

**不要加载当开工 SSOT：** [`归档/`](归档/README.md)。

**冲突裁决：** design > `g1-02-execution-brief`（G1-02 细节）> `task_plan`（模块范围）> inventory（事实表）。

---

## 3. 当前状态（一句话）

| 项                             | 状态                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| Gate 0 / ADR-017 / **ADR-018** | Accepted（design 已索引）                                                                                                  |
| G1-01 清单                     | Plan r6 **`PLAN-READY`**；finding **T01-F04 已关闭**                                                                       |
| 最终执行计划集合               | Plan **`PLAN-READY`** → `completion-check-plan-execution-set.md`                                                           |
| **票 01 / 工作包 1**           | Execute 票级 AC **done**（T01-F01 已修复）；≠ 模块 R4                                                                      |
| **票 02 / 工作包 2**           | Execute 票级 AC **done**（T01-F02 已修复）；≠ 模块 R4                                                                      |
| **票 03 / 工作包 3A**          | Execute **`CLOSED`** → [`completion-check-execute.md`](completion-check-execute.md)；finding **T01-F03-3A 已修复（切片）** |
| 问开关实现                     | `ask_activation` / `write_activation_overlay(sandbox=)` + `source_activation_overlay` 表；**尚未**接 RoutePlanner/CLI      |
| **T01-F03（整条）**            | 仍 **待修复**（余 3B/3C/4a/4b/4x）；ESR 生产旁路仍在                                                                       |
| 开放 finding                   | **T01-F03**（F01/F02 已关）                                                                                                |
| 本地票                         | `.scratch/task-01-g1-02-enable-seam/` · **不发 GitHub**                                                                    |
| 实现 / R4 Audit                | **OPEN**（`completion-check-audit.md`）                                                                                    |
| FRED 编排合并                  | 台账 `T01-ENABLE-FRED-MERGE-001` · 最迟 G1-08 · 票 10                                                                      |

---

## 4. 依赖（勿改主链）

```text
01 ∥ 02 ∥ 03✓
              03✓ → 04 → ┬→ 06 ┐
              03✓ → 05 → ┤→ 07 ├→ 09 → 10
                        └→ 08 ┘   （06∥07∥08 并行；均需 04；06/07 另需 05）
```

**硬禁令（简）：** 问开关已落地，**仍禁止**未迁调用方就删 ESR 散装；禁止只清 fred 漏 E-CLI-20 else；禁止口头漏 bridge；禁止内存 OVERRIDE 长期兼容；禁止未审阅改 `**/design/**`。全文见 brief §0。

**命名：** brief **3A**=问开关（已关）；**3B**=安检；**3C**=测试治理；task_plan **3-OBS**=遥测（随 3B/3C，勿与 3A 混）。工作包 **4c**=G1-03～05（跨模块），≠ G1-02。

---

## 5. 最终执行文件（父目录保留）

`EXECUTION-DOC-INDEX` · `task_plan` · `gate1-integration-spec` · `g1-02-execution-brief` · `g1-01-wiring-inventory` · `decision-map-enable-seam` · `findings` · `progress` · `README` · Plan completion-checks · `completion-check-audit` · **`completion-check-execute`（票 03）**

---

## 6. Suggested skills（下一会话按需 @）

| 时机                                | Skill                                                                                                                   |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| 开写正式代码前                      | `agent-toolchain` → 定分支；`test-driven-development`；`testing-guidelines`（五字段）；`karpathy-guidelines` / ponytail |
| 改 RoutePlanner / registry / ESR 前 | `gitnexus-impact-analysis`（`enabled_source_registry` 曾标 **CRITICAL**）                                               |
| 查调用链                            | `gitnexus-exploring`                                                                                                    |
| 票 04 安检接线                      | `source-driven-development`；`api-and-interface-design`（两层勿揉）                                                     |
| 票 05 / E-TEST-\*                   | completion-check `TEST-EVIDENCE-GOVERNANCE`；禁 patch 已加载对象                                                        |
| 删 OVERRIDE / 迁工厂（票 06–08）    | `deprecation-and-migration`；`gitnexus-refactoring`                                                                     |
| 目标/边界不清                       | `grilling` / grill-me（**停猜**）                                                                                       |
| 切片关账                            | `completion-check`（Execute/Audit；勿用 Plan READY 或票 03 CLOSED 冒充 G1-02）                                          |
| 可观测字段（3-OBS）                 | `observability-and-instrumentation`（须含 `overlay_revision`）                                                          |
| 收尾瘦身                            | `ponytail-review` / `code-simplification`（只列或只动本 diff）                                                          |

---

## 7. 已知坑 / UNVERIFIED（勿假装已裁定）

- 开关本允许时 `reason_code` 现为空串（复用 ERROR_CODE，未自造成功码）；完整枚举 / 管理员 CLI 写 overlay / revision 算法仍 UNVERIFIED → grill 或审阅 design。
- 撤销列已在 DDL；**撤销 API** 未做（不在票 03 AC）。
- `PROJECT_IMPLEMENTATION_ROADMAP.md` 仓库缺失 vs 阶段外置双登记 → **不挡** RED；关手续时再处理。
- GitNexus index 可能滞后；以当前仓库文件 + rg 为准。
- 阶段性代码只放 `phase-scripts/`（中文功能/价值/退役注释）；正式接缝在 `backend/app/datasources/`。

---

## 8. 给下一 agent 的第一句话（可复制）

> 读 `task/task-01-source-registry/EXECUTION-DOC-INDEX.md` 与 `.scratch/task-01-g1-02-enable-seam/README.md`。票 **01/02/03 票级 AC 已关**（capability 契约 + macro_supplementary 失败关闭 + `ask_activation`）。下一刀：票 **04∥05**（3B/3C）；G1-02 细节以 `g1-02-execution-brief.md` 为准。改 `enabled_source_registry` / RoutePlanner 前先 `impact`。不要加载 `归档/`。不要宣称 G1-02 / R4。

_敏感信息：无。本 handoff 不含密钥。_
