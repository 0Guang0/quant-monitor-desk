# Handoff · task-01-source-registry

> **日期：** 2026-07-11（完整重写 · 票 01–05 Execute CLOSED 后 · 下一刀 06∥07）  
> **给：** 下一会话 / 新 agent（实现 4a/4b · 迁 ESR）  
> **本文件位置：** `task/task-01-source-registry/HANDOFF.md`（用户指定）  
> **原则：** 不复制计划/ADR/票正文；只给加载顺序、状态、禁令与指针（context-engineering）。

---

## 0. 三件套核对（接手先扫一眼）

| 文件 | 是否对齐「01–05 关账 · 下一刀 06∥07」 | 要点 |
| --- | --- | --- |
| [`task_plan.md`](task_plan.md) | **是** | 文首下一刀=票 06∥07（4a/4b）；01–05 Execute CLOSED |
| [`progress.md`](progress.md) | **大体是** | 末条已记 04/05 CLOSED；文首 Phase0 一行可能仍写「CC 未关」→ **以末条 + task_plan + 本 HANDOFF 为准** |
| [`findings.md`](findings.md) | **是** | 开放：T01-F03 余 4a/4b/4x、F05-A、F06、F07；3B/3C / F05-B / A7 已关 |

**不要**用旧 HANDOFF（「下一刀 04∥05」或「问开关尚未接 RoutePlanner」）当现状。

**本地票索引可能滞后：** `.scratch/.../README.md` 若仍写「下一刀 04/05」，以本 HANDOFF + scratch 票文件 Status 为准；接手可顺手改 README Frontier。

---

## 1. 下一会话目标（默认）

**Frontier：** 票 **06**（4a · 迁 E-INC-\* / BUNDLE / FRED 启用拆干净）∥ 票 **07**（4b · E-CLI-20 全金路径 + E-CLI-13）。均可与 **08**（bridge）并行；均 blocked-by 已关的 **04+05**。

| 票 | brief | 业务一句话 |
| --- | --- | --- |
| 06 | §6 **4a** | 增量/验收路径不再内存撬门；沙箱正规 overlay 证明 READY |
| 07 | §6 **4b** | backfill 金路径 fred **与** else 都只读问开关；反证「只清 fred 漏 else → 红」 |

正式代码：**TDD**；改 symbol 前 GitNexus `impact`（`enabled_source_registry` 曾标 **CRITICAL**）。  
**禁止**把本 handoff、票 01–05 CLOSED、子集 pytest 绿或 Plan READY 当成 **G1-02 整包 / 模块 R4 / G1-08** 完成。

**分支提示：** 近期多在 `feat/g1-02-ask-activation-03`（未合并）。新切片可续该分支或另开；**勿两 agent 抢同一核心文件组**（`macro_incremental_common` / ESR 工厂 / `data_commands` 金路径 / acceptance matrix）。

**工作区：** 接手先 `git status`——可能有未提交的 04/05 实现、测、台账、`completion-check-execute` 追加；看清再续写。

---

## 2. 上下文加载顺序（context-engineering）

按层级加载，**单次任务只带本切片**（目标 &lt;2k 行有效上下文），勿一次塞满 `task-01/`：

| 序 | 加载什么 | 路径 |
| --- | --- | --- |
| 1 | 规则 | 仓库根 `AGENTS.md` · `agent-toolchain.md` · project-global / ponytail |
| 2 | **执行索引（先读）** | [`EXECUTION-DOC-INDEX.md`](EXECUTION-DOC-INDEX.md) |
| 3 | 本切片票 | `.scratch/task-01-g1-02-enable-seam/issues/06-*.md` 和/或 `07-*.md`（并行则两份；08 另开会话） |
| 4 | G1-02 细节 | [`g1-02-execution-brief.md`](g1-02-execution-brief.md) §2 删除顺序 · §3.1 必清 OVERRIDE · §6 **4a/4b** · §7 验证 |
| 5 | 现场裁定 | [`note.md`](note.md)（04/05 拍板与分诊规则；**勿**把 note 当问题台账） |
| 6 | design（只读） | ADR-017 · **ADR-018** · `docs/modules/design/data_sources.md` §5.2.1 |
| 7 | 已落地能力（消费方） | `activation_overlay.py` · `ask_activation` · `SourceRoutePlanner.plan(con=)` · `enable_source_route` / `seed_activation_base` |
| 8 | 入口对照 | [`g1-01-wiring-inventory.md`](g1-01-wiring-inventory.md)：E-INC-\* · E-INC-BUNDLE · E-CLI-20/13 · E-ACC-01 |
| 9 | 将改源码 + 同类 pattern + 对应测试 | 见票；`impact` 后再动 |
| 10 | 失败输出 | 只贴失败断言/栈，不贴整份 pytest |

**状态指针（需要时再读一行）：** [`findings.md`](findings.md) · [`progress.md`](progress.md) · [`task_plan.md`](task_plan.md) §9 · [`completion-check-execute.md`](completion-check-execute.md)（对象 A–E 已 CLOSED）· `docs/quality/待修复清单.md`（`T01-F05-A` / `F06` / `F07` / `T01-ENABLE-FRED-MERGE-001`）。

**不要加载当开工 SSOT：** [`归档/`](归档/README.md)。

**冲突裁决：** design > `g1-02-execution-brief`（G1-02 细节）> `task_plan`（模块范围）> inventory（事实表）。

---

## 3. 当前状态（一句话）

| 项 | 状态 |
| --- | --- |
| Gate 0 / ADR-017 / **ADR-018** | Accepted（design 已索引） |
| G1-01 清单 | Plan r6 **`PLAN-READY`** |
| **票 01–05** | Execute **CLOSED**（`completion-check-execute.md` 对象 A–E） |
| 问开关 + 安检接线 | **已落地**：`ask_activation` → `plan(con=)`；`overlay_revision`；stderr `source_policy_*` |
| E-TEST 夹具 | **已落地**：正规 overlay；关账证据禁 setattr / 强制 platform |
| 生产 ESR / CLI 金路径 OVERRIDE | **仍在** → 票 **06/07**（T01-F03 余债） |
| 开放 finding | **T01-F03**（余 4a/4b/4x）· **F05-A** · **F06** · **F07**（均已阶段外置登记） |
| 本地票 Frontier | **06∥07**（可∥08）；**不发 GitHub** |
| G1-02 整包 / 实现 R4 | **OPEN** |
| FRED 编排合并 | 台账 `T01-ENABLE-FRED-MERGE-001` · 最迟 G1-08 · **票 10**（06 只拆启用撬门，不关合并） |

### 业务价值（已交付 vs 下一刀）

| 已交付（01–05） | 下一刀（06∥07）要交付的价值 |
| --- | --- |
| 能力契约可校验；宏域默认诚实关；开关本可写可问；拉数/预览按开关本安检；测试不再假绿 | **正式增量 CLI / 验收矩阵与服务同路**：同参同拒绝；沙箱 overlay 才能 READY；产品默认库不因旧 ESR 假开 |

### 下一产品决策点（非本切片阻塞）

- **06/07 本身不需新拍板**（ADR-018 已定）。  
- 用户再进场：① 真实监控库「谁/用什么入口开源」（R8 运维面）；② G1-08 前 FRED 合并 vs 新 ADR 废止；③ 改 `**/design/**` 须审阅。

---

## 4. 依赖（勿改主链）

```text
01✓ ∥ 02✓ ∥ 03✓ → 04✓ → ┬→ 06 ─┐
              03✓ → 05✓ → ┤→ 07 ─┼→ 09 → 10
                           └→ 08 ─┘   （06∥07∥08 并行）
```

**硬禁令（简）：** 禁止未迁调用方就删 ESR 根；禁止只清 fred 漏 E-CLI-20 **else**；禁止内存 OVERRIDE 长期兼容；禁止未审阅改 `**/design/**`；禁止用 sandbox READY 升格「产品已默认启用」；禁止为保绿恢复 `__setattr__` / 强制 `_platform_allows`；阶段性代码只放 `phase-scripts/`。全文见 brief §0。

**命名：** brief **4a**=票 06；**4b**=票 07；**4x**=票 08（bridge）。**勿**把 FRED **编排合并**（票 10）塞进 06 关账。工作包 **4c**=G1-03～05（跨模块），≠ G1-02。

**本切片须承接的阶段外置债：** F05-A（旧口径测迁 overlay）· F06（夹具去内存构造）· F07（06+07 后删 `plan(con=None)` 回落）— 见 findings + 待修复清单；**登记≠关账**。

---

## 5. 已落地代码指针（勿重做）

| 能力 | 位置 |
| --- | --- |
| 问开关 | `backend/app/datasources/activation_overlay.py` · migration `017_*` |
| 安检接线 | `route_planner.py`（`plan(..., con=)` / `ask_activation`）· `service.py` 透传 · `route_models.overlay_revision` |
| 策略日志 | `_emit_source_policy_event`（stderr JSON；`QMD_SOURCE_POLICY_TELEMETRY`） |
| 测试夹具 | `tests/service_path_support.py`：`enable_source_route` · `seed_activation_base` |
| 票级测 | `test_activation_overlay.py` · `test_route_planner_activation.py` · `test_etest_overlay_governance.py` |

**再验 04/05（回归用，≠ 06 完成）：**

```text
uv run pytest -q tests/test_route_planner_activation.py tests/test_etest_overlay_governance.py tests/test_platform_source_matrix.py::test_qmtXqshareMissingEnvNotSchedulable
```

---

## 6. 最终执行文件（父目录保留）

`EXECUTION-DOC-INDEX` · `task_plan` · `gate1-integration-spec` · `g1-02-execution-brief` · `g1-01-wiring-inventory` · `decision-map-enable-seam` · `findings` · `progress` · `note` · `README` · Plan completion-checks · `completion-check-audit` · **`completion-check-execute`（票 01–05 追加在同一文件；06/07 关账继续追加）**

---

## 7. Suggested skills（下一会话按需 @）

| 时机 | Skill |
| --- | --- |
| 开写正式代码前 | `agent-toolchain` → 定分支；`test-driven-development`；`testing-guidelines`（五字段）；ponytail / `karpathy-guidelines` |
| 改 ESR / 增量工厂 / 金路径前 | `gitnexus-impact-analysis`（`enabled_source_registry` 等） |
| 查调用链 / 入口 ID | `gitnexus-exploring` · inventory |
| 删 OVERRIDE / Strangler | `deprecation-and-migration`；`gitnexus-refactoring` |
| 票 06/07 夹具与证据档位 | completion-check `TEST-EVIDENCE-GOVERNANCE`；禁 patch 已加载对象作关账证据 |
| 目标/边界不清 | `grilling` / grill-me（**停猜**） |
| 切片关账 | `completion-check`（Execute：追加既有 `completion-check-execute.md`；勿用 01–05 CLOSED 冒充 G1-02） |
| 收尾瘦身 | `ponytail-review` / `code-simplification`（只动本 diff） |
| 新会话续作 | 先读本 `HANDOFF.md` + `EXECUTION-DOC-INDEX.md` |

---

## 8. 已知坑 / UNVERIFIED（勿假装已裁定）

- 开关本 `reason_code` 允许时多为空串（复用 ERROR_CODE）；完整枚举 / **管理员写 overlay 的产品 CLI** / revision 算法仍 UNVERIFIED → grill 或审阅 design（**不挡** 06/07 迁调用方）。
- 撤销列在 DDL；**撤销 API** 未做。
- F06：`enable_source_route` 仍改测试副本内存字段 → 06 收敛；不得声称「夹具已零构造」直至 F06 关。
- F07：无 `con` 仍回落 YAML `is_enabled` → **06+07 完成后**再删；产品 fetch 必须传 `con`。
- 票 06 **不**关闭 `T01-ENABLE-FRED-MERGE-001`（合并四门槛 → 票 10 / G1-08）。
- inventory **P-SUPP** 文案可能仍写旧 `VALIDATION_ONLY_BLOCKED` → 文档漂移，顺手改，不挡 RED。
- `PROJECT_IMPLEMENTATION_ROADMAP.md` 仓库缺失 vs 阶段外置双登记 → **不挡** RED（待修复清单已登记）。
- GitNexus index 可能滞后；以当前仓库 + rg 为准。

---

## 9. 给下一 agent 的第一句话（可复制）

> 读 `task/task-01-source-registry/HANDOFF.md` 与 `EXECUTION-DOC-INDEX.md`。票 **01–05 Execute 已 CLOSED**（`completion-check-execute.md` 对象 A–E）。下一刀：**06∥07**（brief 4a/4b · 迁 ESR / 金路径 overlay）；细节以 `g1-02-execution-brief.md` §3.1/§6 为准；现场裁定见 `note.md`；开放债见 `findings.md`（F05-A/F06/F07）。改 `enabled_source_registry` 前先 `impact`。反证：只清 fred 漏 else → 必须红。先 `git status`。不要加载 `归档/`。不要宣称 G1-02 / R4。不要在本切片关 FRED 编排合并台账。

_敏感信息：无。本 handoff 不含密钥。_
