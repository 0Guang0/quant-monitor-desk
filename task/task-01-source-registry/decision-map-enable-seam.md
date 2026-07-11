# 决策地图：启用策略接缝（overlay vs 内存 OVERRIDE）

> **状态：** #1–#4 已由用户确认并写入 **Accepted ADR-018**（`docs/decisions/design/ADR-018-enable-seam-two-layer-and-fred-merge-gate.md`，已索引 `MIGRATION_MAP.md`）  
> **权威：** ADR-017 + ADR-018；`docs/modules/design/data_sources.md` §5.2.1；禁止以兼容 OVERRIDE 为长期态  
> **关联：** [归档/fred-builder-vs-adr017.md](归档/fred-builder-vs-adr017.md) · [归档/architecture-review-fred-enable-seam.html](归档/architecture-review-fred-enable-seam.html)  
> **领域词：** 仓库根 [CONTEXT.md](../../CONTEXT.md)

## 已内联决议（本轮不必再开票）

| 问题                              | 决议                                              |
| --------------------------------- | ------------------------------------------------- |
| fred builder 是否另一套启用策略？ | **否**；编排壳 + 共享 OVERRIDE                    |
| 与 ADR-017？                      | **代码 vs 设计**冲突（实现缺口），非 ADR 自相矛盾 |
| 强行长期兼容 OVERRIDE？           | **否**；G1-02 删除共享根因                        |
| E-CLI-20「fred 专用」？           | **盘点措辞错**；全金路径 OVERRIDE                 |

---

## #1: overlay 最小接口形状？

Blocked by: （无）  
Type: Grilling  
**Status:** Resolved 2026-07-11

### Question

「有效启用」对外接口最小应暴露什么？分两层还是一层？

### Answer

**分两层（用户确认）：**

1. **开关本（activation overlay 层）**
   - 只回答：「管理员有没有允许这个源做这件事？」
   - 最小输出：`is_allowed`（能不能用）+ 机器可读 `reason_code` + `overlay_revision`（开关本版本号）
   - 输入：`source_id` + `data_domain` + `operation`（与 design 表键一致）

2. **安检（RoutePlanner / 路由层）**
   - 再查：基础登记、license/auth、platform matrix、capability、ResourceGuard 等
   - 任一项不过 → 失败关闭
   - CLI / 调度 / 服务只读合成结果，**禁止**改 registry 内存或强制 `_platform_allows`

契约原则：一次只存在一个启用策略版本；新增字段只能附加；错误码全入口一致（见 `task_plan.md` §4A）。

---

## #2: 过渡期 dry-run 如何在无 OVERRIDE 时仍可测？

Blocked by: #1  
Type: Grilling  
**Status:** Resolved 2026-07-11

### Question

删掉内存 OVERRIDE 后，如何仍能测金路径 READY？

### Answer

**隔离沙箱写「正规测试开关本」（用户确认）：**

| 环境                    | 做法                                                       |
| ----------------------- | ---------------------------------------------------------- |
| 产品默认库              | 不因测试打开这些源；保持诚实默认                           |
| 验收 / dry-run 隔离目录 | 写入标明测试/沙箱的 overlay 记录（走 #1 接口，不内存撬门） |
| 报告档位                | 明确 `gate_live` / 沙箱；**禁止**升格为「产品已默认启用」  |

**禁止：** 测试 monkeypatch / `__setattr__` / 临时 `force_enable` 后门（一旦可观察即成事实契约）。

---

## #3: FredIncrementalFetchProxy 是否保留？何时必须合并？

Blocked by: #1  
Type: Grilling  
**Status:** Resolved 2026-07-11（含合并/删除关账条件，禁止无限搁置）

### Question

FRED 编排壳先留还是立刻并进 `MacroIncrementalFetchProxy`？

### Answer

**先留编排壳，启用必须拆干净；合并有硬门槛，不得无限延后（用户确认）。**

#### 现在必须做（G1-02 / 工作包 3～4a）

| 留                                                      | 删                                                        |
| ------------------------------------------------------- | --------------------------------------------------------- |
| 按 series 灌水位线、FRED binding / `execute_binding` 壳 | 任何「顺便强制打开源」的代码（含委托 ESR 的 enable 工厂） |

#### 合并触发条件（满足即可开工合并；不得无条件「以后再说」）

同时满足下列 **全部** 后，**必须在同一 Gate 1 发布窗（最迟 G1-08 前）完成合并或显式 ADR 废止合并**：

1. **启用已外置：** 全库无 `enabled_source_registry` / 强制 `_platform_allows` / 双份 `enabled_fred_*`（#4 已关）。
2. **水位线形状对齐：** FRED 的 `since_by_series` 与通用宏源 `since_by_instrument`（或统一命名）在接口上可互换；proxy 仅做「取数前注入 start_time」。
3. **执行壳对齐或证明不可对齐：** 要么 FRED 也走与其它宏源同一 `run_macro_incremental` 族，要么书面证明 `execute_binding` 差异不可消除并开 **新 ADR**（用户审阅）——不可口头永久双轨。
4. **同参反证绿：** 删掉 FRED 专用 enable 后，sandbox overlay 下 preview/incremental 与通用路径同 status/source/reason。

#### 删除条件（合并完成后）

- 删除 `FredIncrementalFetchProxy` 类（或降为对通用 proxy 的零逻辑别名后下一切片删除）。
- `rg` 无第二套 enable / 无旁路 `_platform_allows`。
- 清单 E-INC-FRED 策略路径改为只读 #1 接口 + 编排备注。

#### 台账

开放项 ID：`T01-ENABLE-FRED-MERGE-001` → [docs/quality/待修复清单.md](../../docs/quality/待修复清单.md)  
Owner：task-01 G1-02 → 工作包 4a；最迟触发：Gate 1 **G1-08 前**；阻断：不得在双轨 enable 未清时宣称策略同路完成。

---

## #4: 重复 enable 工厂删除顺序？

Blocked by: #1  
Type: Research  
**Status:** Resolved 2026-07-11

### Question

`fred_incremental_watermark` 与 `fred_incremental_run` 双份 enable 怎么删？

### Answer

**顺序（用户确认）：**

1. 落地 #1「问开关」接口（工作包 3）。
2. 所有调用方改为只问该接口（含 CLI backfill、matrix、各 `enabled_*`）。
3. **先删** `fred_incremental_watermark.py` 内重复 `enabled_fred_source_registry` 拷贝；`fred_incremental_run` 若仍有别名，改为薄委托或一并删除。
4. 全库 `rg`：`enabled_source_registry`、`object.__setattr__(.*is_enabled`、`_platform_allows\s*=` — 生产路径须为零（测试仅允许构造 **overlay 输入**，不得改已加载对象）。

资产：调用方表在 G1-02 RED 时由执行者从 GitNexus `context(enabled_source_registry)` + rg 刷新，链到本票 progress。

---

## 雾区（尚未成票 · 不阻塞 #1–#4）

- overlay 表字段落地 / migrate（design 已有草案；改 design 须用户审阅 + promote）
- scheduler PRODUCT-LIVE vs matrix 双轨（G1-05 / FIND-3-01）
- Validation 全链（G1-03）

## 完成判据

- [x] #1–#4 有用户确认 Answer
- [x] G1-01 清单按 r5+ADR-018 修正并获 Plan r6 `PLAN-READY`
- [ ] G1-02 工作包 3 按 #1 接口 RED→GREEN（开工必读 [g1-02-execution-brief.md](g1-02-execution-brief.md)）
- [ ] `T01-ENABLE-FRED-MERGE-001` 在 G1-08 前关闭或经新 ADR 废止

本地图在 G1-01 READY 后即可支撑开工工作包 3；**不**再增启用策略形状票。执行细节以 brief + ADR-018 为准，防止多轮 Plan CC 细节漂移。
