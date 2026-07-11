# ADR-018：启用策略两层接缝与 FRED 编排合并关账

**状态：** Accepted（2026-07-11 经项目用户确认；本 ADR 与 `MIGRATION_MAP.md` 索引设计共同构成后续实现依据）

**日期：** 2026-07-11

**决策者：** 项目用户 / 产品负责人

**关联：** ADR-017（动态降级与启用覆盖层）；ADR-016（来源矩阵诚实关闸）；
task-01-source-registry（G1-02 工作包 3～4a）；
`docs/modules/design/data_sources.md` §5.2.1

## 背景

ADR-017 已规定：稳定 Source Registry 与管理员**持久化启用覆盖层**分离，且
**禁止调用方内存绕过**。设计还给出 `source_activation_overlay` 表形与
「有效启用 = 基础状态 + overlay + license/auth + platform + capability + ResourceGuard」的合成规则。

实现侧仍大量使用 `enabled_source_registry`（改 `is_enabled` / 改写 `get_domain_roles`）以及
强制 `planner._platform_allows = True`，使 CLI 回补预览、宏观增量与验收矩阵在 YAML 默认禁用时
仍可「变绿」。FRED 的 `build_fred_incremental_*` 常被误读为另一套启用权威，实则多为编排壳，
启用仍走同一 OVERRIDE 根因。

若不把「开关本」与「路由安检」拆成清晰接缝，并给 FRED 编排合并设硬门槛，则会出现：

- 同参不同入口结论分裂；
- 测试靠内存撬门，无法证明产品默认策略；
- 「以后再合并 FRED」无限搁置，双轨再次固化。

## 决策

### 1. 两层接缝（开关本 ≠ 安检）

**第一层 — 开关本（activation overlay）**

只回答：「管理员有没有允许这个已登记来源参与该领域/操作？」

最小对外结果：

- `is_allowed`（能不能用）；
- 机器可读 `reason_code`；
- `overlay_revision`（开关本版本号，须进入 RoutePlan / 血缘可观察字段）。

输入键与 design 表一致：`source_id` + `data_domain` + `operation`。

**第二层 — 安检（RoutePlanner / 路由门控）**

在开关本之后继续检查：基础登记、license/auth、platform matrix、capability、ResourceGuard 等。
任一项不满足即失败关闭。

任务、CLI、调度器与服务**只能读取**合成后的有效启用结果，**不得**在内存中改写 registry、
替换角色查询或强制平台判定。

一次只存在一个启用策略版本；接口演进只许附加字段，不得静默改义已有拒绝语义。

### 2. 测试与证据档位

产品默认库不得因测试需要而打开默认禁用源。

验收 / dry-run 仅允许在**隔离数据根**写入标明测试/沙箱用途的正规 overlay 记录，并走第一层接口；
禁止 `__setattr__`、monkeypatch 已加载对象、或未文档化的 `force_enable` 后门。

报告档位须标明沙箱 / `gate_live` 等真实档位，**禁止**升格为「产品已默认启用」的发布证据。

### 3. FRED 编排壳：先拆启用，后有期限合并

G1-02 必须立即从 FRED 路径删除启用撬门（与其它宏源同一共享根因）。

允许暂留的业务编排（非启用策略）：按 series 灌水位线、FRED 专用 binding / `execute_binding` 壳等。

**合并进通用 `MacroIncrementalFetchProxy`（或等价共享编排）的硬门槛**——须同时满足，且
**最迟在 Gate 1 的 G1-08 之前**完成合并关账，或另立经用户审阅的 ADR 明确废止合并：

1. 全库生产路径已无 `enabled_source_registry` / 强制 `_platform_allows` / 双份 `enabled_fred_*`；
2. FRED 水位线注入与通用宏源在接口形状上可互换（proxy 只做取数前注入）；
3. 执行壳已对齐共享 runner，或新 ADR 证明差异不可消除（禁止口头永久双轨）；
4. 沙箱 overlay 下同参反证：preview / incremental 与通用路径同 source/status/reason。

合并完成后删除专用启用工厂与多余 proxy 别名；全库检索确认无第二套启用旁路。

台账：`T01-ENABLE-FRED-MERGE-001`（`docs/quality/待修复清单.md`）。

### 4. 重复 enable 工厂的删除顺序

1. 先实现第一层「问开关」接口；
2. 全部调用方改为只问该接口；
3. 删除 `fred_incremental_watermark` 等处的重复 enable 拷贝；
4. 全库检索清零生产路径上的内存撬门。

## 备选方案

### 方案 A：一层函数同时做开关与安检

优点是调用面小。缺点是难测、难审计，且易再次把「强制 platform」藏进同一函数。

**未选用。**

### 方案 B：永久保留内存 OVERRIDE 作为兼容层

优点是现有 dry-run 少改。缺点是直接违反 ADR-017，并固化入口分裂。

**未选用。**

### 方案 C：两层接缝 + 沙箱正规 overlay + FRED 有期限合并

对齐 ADR-017，测试不造假，防止双轨无限搁置。

**选用。**

## 后果与模块责任

| 范围         | 责任                                                                          |
| ------------ | ----------------------------------------------------------------------------- |
| task-01      | 实现开关本读写与「问开关」接口；删除 OVERRIDE 根因；按本 ADR 关账 FRED 合并项 |
| task-02      | RoutePlan 安检只读有效启用；持久化 `activation_overlay_revision`              |
| task-17 / 18 | CLI / 调度不私设强制启用；沙箱测只用正规 overlay                              |
| 测试治理     | 夹具只构造策略输入（含沙箱 overlay），不改已加载生产对象                      |

本决策增加 overlay 迁移与调用方改造成本，换来可审计启用、同参同结论，以及可关闭的编排合并债。

## 后续动作

1. 本文件已纳入 `docs/decisions/design/`，并由 `MIGRATION_MAP.md` 索引。
2. 同步 `docs/architecture/design/08_decision_log_index.md` 与 `docs/decisions/README.md`。
3. G1-01 按 Plan r5 修正接线清单后重审；G1-02 工作包 3 按两层接口 RED→GREEN。
4. G1-08 前关闭 `T01-ENABLE-FRED-MERGE-001`，或另立审阅 ADR 废止合并。
5. 若 overlay 表字段相对 `data_sources.md` §5.2.1 仍需变更，须再次用户审阅 design 后 promote。
