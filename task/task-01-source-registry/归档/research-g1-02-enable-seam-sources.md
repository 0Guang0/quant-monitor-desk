# 研究报告：G1-02「两层启用接缝」应对齐的权威契约与计划缺口

> **日期：** 2026-07-11  
> **角色：** research（只读 primary sources；**未**改 `**/design/**`、未改运行时代码）  
> **研究问题：** G1-02「两层启用接缝」执行计划应对齐哪些权威字段/接口/退役条件？`task_plan` / `gate1-integration-spec` 里可能缺哪些细节？  
> **方法：** 逐条回指下列 primary sources；找不到权威处标 **UNVERIFIED**。

---

## 0. Primary sources 清单（本轮核对）

| # | 路径 | 用途 |
|---|------|------|
| 1 | `docs/decisions/design/ADR-018-enable-seam-two-layer-and-fred-merge-gate.md` | 两层接缝、证据档位、FRED 合并四门槛、删除顺序 |
| 2 | `docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md` | 持久化启用覆盖层；禁止调用方内存绕过 |
| 3 | `docs/modules/design/data_sources.md` §5.2.1 | `source_activation_overlay` 表形与有效启用合成 |
| 4 | `task/task-01-source-registry/g1-01-wiring-inventory.md` | 入口 ID、策略路径、档位、责任矩阵 |
| 5 | `task/task-01-source-registry/decision-map-enable-seam.md` | #1–#4 已确认决议（与 ADR-018 对齐） |
| 6 | `task/task-01-source-registry/completion-check-plan-g1-01-r6.md` | Summary / 闭环控制（PLAN-READY → G1-02） |
| 7 | `task/task-01-source-registry/task_plan.md` §4A、工作包 3/3A/4a/4b | 策略查询契约与工作包叙述 |
| 8 | `task/task-01-source-registry/gate1-integration-spec.md` G1-02 行 / 唯一策略接口 | Gate 切片验收措辞 |

辅助台账（非 design，用于合并截止）：`docs/quality/待修复清单.md` → `T01-ENABLE-FRED-MERGE-001`。

---

## 1. 权威摘录（带路径 + 小节引用）

### 1.1 ADR-018 — 两层接缝、证据、FRED、删除顺序

**文件：** `docs/decisions/design/ADR-018-enable-seam-two-layer-and-fred-merge-gate.md`  
**状态：** Accepted（2026-07-11）

#### §决策.1 两层接缝（开关本 ≠ 安检）

- **第一层 — 开关本（activation overlay）**  
  - 只回答：「管理员有没有允许这个已登记来源参与该领域/操作？」  
  - **最小对外结果：** `is_allowed`、`reason_code`（机器可读）、`overlay_revision`（须进入 RoutePlan / 血缘可观察字段）  
  - **输入键：** `source_id` + `data_domain` + `operation`（与 design 表一致）
- **第二层 — 安检（RoutePlanner / 路由门控）**  
  - 在开关本之后：基础登记、license/auth、platform matrix、capability、ResourceGuard 等；任一项不满足即失败关闭  
  - 任务/CLI/调度器/服务**只能读取**合成有效启用结果；**不得**内存改写 registry、替换角色查询或强制平台判定  
- **演进：** 一次只存在一个启用策略版本；接口只许附加字段，不得静默改义已有拒绝语义

#### §决策.2 测试与证据档位

- 产品默认库不得因测试打开默认禁用源  
- 验收 / dry-run **仅**允许在**隔离数据根**写入标明测试/沙箱用途的正规 overlay，并走第一层接口  
- **禁止：** `__setattr__`、monkeypatch 已加载对象、未文档化的 `force_enable` 后门  
- 报告档位须标明沙箱 / `gate_live` 等；**禁止**升格为「产品已默认启用」

#### §决策.3 FRED 编排壳：先拆启用，后有期限合并

- G1-02 **必须立即**从 FRED 路径删除启用撬门（与其它宏源同一共享根因）  
- 可暂留：按 series 灌水位线、FRED 专用 binding / `execute_binding` 壳等（非启用策略）  
- **合并四门槛**（须**同时**满足；最迟 **Gate 1 的 G1-08 之前**关账，或另立审阅 ADR 废止合并）：  
  1. 全库生产路径已无 `enabled_source_registry` / 强制 `_platform_allows` / 双份 `enabled_fred_*`  
  2. FRED 水位线注入与通用宏源在接口形状上可互换（proxy 只做取数前注入）  
  3. 执行壳已对齐共享 runner，或新 ADR 证明差异不可消除（禁止口头永久双轨）  
  4. 沙箱 overlay 下同参反证：preview / incremental 与通用路径同 source/status/reason  
- 合并后：删除专用启用工厂与多余 proxy 别名；全库检索无第二套启用旁路  
- 台账：`T01-ENABLE-FRED-MERGE-001`

#### §决策.4 重复 enable 工厂删除顺序

1. 先实现第一层「问开关」接口  
2. 全部调用方改为只问该接口  
3. 删除 `fred_incremental_watermark` 等处的重复 enable 拷贝  
4. 全库检索清零生产路径上的内存撬门  

#### §后果与模块责任（摘）

| 范围 | 责任 |
|------|------|
| task-01 | 开关本读写与「问开关」接口；删除 OVERRIDE；按 ADR 关账 FRED 合并项 |
| task-02 | RoutePlan 安检只读有效启用；持久化 `activation_overlay_revision` |
| task-17 / 18 | CLI/调度不私设强制启用；沙箱测只用正规 overlay |
| 测试治理 | 夹具只构造策略输入（含沙箱 overlay），不改已加载生产对象 |

---

### 1.2 ADR-017 — 覆盖层与禁止内存绕过

**文件：** `docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md`  
**相关小节：** §决策.1「两种状态分离」；§后果与模块责任

#### §决策.1（摘录）

- Source Registry = 稳定能力目录；不因一次故障被运行时改写  
- 另设项目管理员经受控配置/CLI 管理的**持久化启用覆盖层**  
- 覆盖层只表达：「当前是否允许这个已登记来源参与某领域/操作的路由」  
- 须记录：操作者、时间、原因、版本和撤销信息  
- 不允许任务自行永久改开关  

#### §后果（task-01 行）

> Source Registry、Capability、管理员启用覆盖层、来源/质量标签契约；**禁止调用方内存绕过**。

**说明：** ADR-017 **未**单独规定「问开关」最小三字段（`is_allowed` / `reason_code` / `overlay_revision`）；该最小契约由 **ADR-018** + `data_sources.md` §5.2.1 接缝分层补齐。

---

### 1.3 `data_sources.md` §5.2.1 — 表形与有效启用合成

**文件：** `docs/modules/design/data_sources.md` → `### 5.2.1 有效启用覆盖层`

#### 表 `source_activation_overlay` 字段（design SQL）

| 字段 | 约束要点 |
|------|----------|
| `overlay_id` | PRIMARY KEY |
| `source_id` | NOT NULL |
| `data_domain` | NOT NULL |
| `operation` | NOT NULL |
| `enabled` | BOOLEAN NOT NULL |
| `reason` | TEXT NOT NULL |
| `changed_by` | VARCHAR NOT NULL |
| `changed_at` | TIMESTAMP NOT NULL |
| `revision` | VARCHAR NOT NULL |
| `revoked_at` / `revoked_by` / `revoke_reason` | 撤销三元组（可空） |

#### 有效启用合成（原文语义）

> 有效启用 = 基础 `is_enabled`、最新未撤销 overlay、license/auth、platform matrix、capability 与 ResourceGuard **均允许**。任何一项不满足即失败关闭；任务、CLI 和调度器只能读取这个结果，不能在内存中改写 registry 或 platform 判定。

#### 接缝分层（同节 ADR-018 指针）

- overlay「开关本」层：管理员是否允许；输出含 `overlay_revision`  
- RoutePlanner「安检」层：执照/平台/能力/护栏  
- 测试：仅隔离根正规 overlay；禁止内存撬门  
- FRED：编排壳与启用撬门分离；合并关账见 ADR-018  

**分层含义（研究结论）：**  
「有效启用」全合成 = 第一层开关本 + 第二层安检；**问开关接口本身不应把 license/platform/capability 混进一层函数**（ADR-018 明确弃用方案 A）。

---

### 1.4 decision-map-enable-seam.md — 已确认决议摘要

**文件：** `task/task-01-source-registry/decision-map-enable-seam.md`  
**状态：** #1–#4 Resolved → 已写入 Accepted ADR-018

| # | 决议要点 |
|---|----------|
| #1 | 两层；开关本输出 `is_allowed` + `reason_code` + `overlay_revision`；输入三键；错误码全入口一致（见 `task_plan.md` §4A） |
| #2 | 隔离沙箱写正规测试 overlay；产品默认库不因测打开源；档位禁升格；禁 monkeypatch/`force_enable` |
| #3 | 先留编排、启用必拆；合并四门槛 + G1-08 前关账；台账 `T01-ENABLE-FRED-MERGE-001` |
| #4 | 问开关 → 调用方迁移 → 先删 watermark 重复 enable → rg 清零生产撬门 |

雾区（不阻塞 #1–#4，但执行计划应知情）：overlay 表字段落地/migrate；scheduler PRODUCT-LIVE vs matrix 双轨（G1-05 / FIND-3-01）；Validation 全链（G1-03）。

---

### 1.5 g1-01-wiring-inventory.md — 入口 / 档位 / 责任

**文件：** `task/task-01-source-registry/g1-01-wiring-inventory.md`  
**状态：** Plan r6 = PLAN-READY（≠ 实现完成）

#### 档位图例（§1 图例 · 证据允许范围）

| 档位 | 允许证据 | 禁止升格为 |
|------|----------|------------|
| `dry_run` | CLI 默认 dry-run 计划/预览 | R4 / G1-08 |
| `product_default` | 未覆盖 registry 的预览/拒绝 | — |
| `override_runtime` | 仅作「绕过仍存在」反证 | 产品启用证明 |
| `gate_live` | `QMD_DATA_ROOT` 含 `.audit-sandbox/source-route-db` 且非 dry-run | fixture/replay PASS |
| `staged_fixture` | `staged_fixture_mode=True` 宏增量 | 产品默认 |
| `danger_skip_isolation` | **仅**登记暗门；禁止作任何完成/发布证据 | 一切正式档位 |

当前事实：overlay 列填 `none（ADR-017/018 待 G1-02）`。

#### §3 责任矩阵 — task-01 / G1-02 必须吃进

> OVERRIDE-MEM（§1.3–1.4 含 E-CLI-20 全金路径）、E-TEST-*、E-REG-01～04、E-ACC-ISO-01、E-ACC-SKIP-01、E-ACC-BRIDGE-01、E-SVC-01、E-OPS-01～03b；ADR-018 两层接缝。

---

### 1.6 completion-check-plan-g1-01-r6.md — Summary / 闭环控制

**文件：** `task/task-01-source-registry/completion-check-plan-g1-01-r6.md`

- **最终状态：** `PLAN-READY`；声称 `permitted`（允许进入 G1-02 / 工作包 RED；**禁止**解读为实现或 R4）  
- **闭环控制：** 下一步以清单 §1–§3 为开工蓝图开 G1-02 RED（两层接缝 / 清 OVERRIDE，含 **E-CLI-20 全金路径** 与 **E-ACC-BRIDGE-01 处置**）。Execute/Audit 须独立跑；pytest 绿与 §5 勾选不得单独证明实现关账。  
- **CC-5：** E-CLI-20 = 全金路径 OVERRIDE（fred 编排壳 + else ESR）；**不得只拆 fred builder**  
- **CC-3：** bridge 须按删除条件处置，不得口头漏登  

---

### 1.7 task_plan.md — §4A 与工作包 3 / 4a / 4b（现状）

**文件：** `task/task-01-source-registry/task_plan.md`

#### §4A「跨模块内部接口契约」（仍偏「整层策略查询」）

| 契约项 | Task-01 提供 |
|--------|----------------|
| 输入 | 平台、领域、操作、频率（如适用）及经 Gate 0 批准的授权/启用上下文 |
| 输出 | RoutePlan / 错误码风格统一决策：可选 source、状态、机器可读原因码、用户说明、策略版本/配置指纹 |
| 拒绝语义 | `USER_AUTH_REQUIRED`、禁用、能力缺失、平台不支持等可区分且全入口一致 |
| 变更规则 | 一次一个启用策略版本；新增字段向后兼容 |
| 测试/夹具 | 构造策略输入前声明受控配置；不得改写已加载生产对象或平台判定 |

#### 工作包 3「唯一启用策略接缝」

- 依赖：0、1；问题 T01-F03  
- RED：未授权/未启用不能被对象突变放行；已批准启用经唯一接缝稳定读取（含原因与审计）  
- GREEN：只实现 Gate 0 批准的持久化表达；无任意 `force_enable` / 平台跳过  
- 测试资产：改写 `service_path_support.py` 等，禁止 patch 已加载对象  

#### 工作包 4a / 4b

- 4a：宏观增量（`macro_incremental_common`、`fred_incremental_watermark`）删动态覆盖，改问工作包 3 接缝  
- 4b：`data_commands` 回填/预览例外 → 正式策略接缝  

**缺口提示：** §4A / 工作包 3 仍把「有效启用 + capability + 平台」揉成**一层对外策略查询**叙述；**未**显式写出 ADR-018 的「问开关」三字段与安检二层拆分（见 §6 缺口表）。

---

### 1.8 gate1-integration-spec.md — G1-02 行

**文件：** `task/task-01-source-registry/gate1-integration-spec.md`

- **权威输入行已含 ADR-018**  
- **唯一策略接口：** 输入含「只读的有效启用状态」；输出含 `registry/overlay revision`  
- **G1-02 切片：**「有效启用 + capability 查询成为唯一策略入口；直接 CLI/宏观绕过删除」；验证：「允许／未授权／能力缺失」三种同参测试  

**缺口提示：** G1-02 验收句仍是「一层唯一策略入口」语气；**未**点名两层拆分、沙箱 overlay 档位、E-CLI-20 全金路径、E-ACC-BRIDGE-01、FRED 合并四门槛 / 删除顺序（见 §6）。

---

## 2. 「问开关」最小契约（执行计划必须对齐）

> 权威：ADR-018 §1；decision-map #1；`data_sources.md` §5.2.1 输入键与 `revision`；与 §4A「整层策略」区分。

### 2.1 输入键（开关本层）

| 键 | 权威来源 | 备注 |
|----|----------|------|
| `source_id` | ADR-018；§5.2.1 表列 | 已登记来源 |
| `data_domain` | 同上 | 领域 |
| `operation` | 同上 | 操作；与 design 表一致 |

**不在开关本层输入（属安检层 / 整层 RoutePlan）：** platform、frequency、license/auth 上下文、capability、ResourceGuard — 这些在 ADR-018 第二层与 `task_plan` §4A / gate1「唯一策略接口」中出现；执行计划应写清**调用顺序**：先问开关 → 再安检。

### 2.2 输出字段（开关本层 · 最小）

| 字段 | 权威含义 |
|------|----------|
| `is_allowed` | 管理员是否允许该源参与该领域/操作 |
| `reason_code` | 机器可读拒绝/允许原因（全入口一致） |
| `overlay_revision` | 开关本版本号；须进入 RoutePlan / 血缘可观察字段（ADR-018；task-02 持久化名 `activation_overlay_revision`） |

### 2.3 错误 / 拒绝语义（分层注意）

| 层级 | 权威要求 | 计划应对齐 |
|------|----------|------------|
| 开关本 | 机器可读 `reason_code`；不得静默改义 | 管理员未允许 / 无有效 overlay / 已撤销等（**具体枚举码 UNVERIFIED** — 见 §7） |
| 安检 / 整层策略 | §4A：`USER_AUTH_REQUIRED`、禁用、能力缺失、平台不支持等可区分 | 属第二层或合成结果；**不得**把「强制 `_platform_allows`」藏进问开关 |
| 演进 | 一次一策略版本；只许附加字段 | 禁止兼容 OVERRIDE 作为长期态（decision-map / ADR-018 方案 B 未选用） |

### 2.4 读写职责（开关本持久化）

| 能力 | 权威 |
|------|------|
| 管理员经受控配置/CLI 写 overlay | ADR-017 §1；R8（task_plan） |
| 记录操作者、时间、原因、版本、撤销 | ADR-017 §1；§5.2.1 表字段 |
| 任务不得自行永久改开关 | ADR-017 §1 |
| 消费者只读合成结果 | ADR-017/018；§5.2.1 |

---

## 3. 测试 / 沙箱 overlay 证据档位约束

> 权威：ADR-018 §2；decision-map #2；wiring-inventory §1 档位图例；§4A 测试/夹具行。

| 约束 | 权威陈述 | 对 G1-02 执行计划的含义 |
|------|----------|-------------------------|
| 产品默认库 | 不得因测试打开默认禁用源 | 禁止用产品根写「测开」overlay 当发布证据 |
| 隔离根 + 正规 overlay | 验收/dry-run 仅在隔离数据根写标明测试/沙箱用途的 overlay，并走第一层接口 | RED/GREEN 夹具构造 = 写 overlay 输入，不是 patch 对象 |
| 禁止撬门 | 禁 `__setattr__` / monkeypatch 已加载对象 / 未文档化 `force_enable` | 处置 E-TEST-01/02 等；工作包 3 测试资产改写 |
| 档位诚实 | 标明沙箱 / `gate_live` 等；禁升格「产品已默认启用」 | 证据标签必须用 inventory 档位名；`override_runtime` 只能反证绕过仍在 |
| `danger_skip_isolation` | 永久禁止作完成/发布证据 | E-ACC-SKIP-01 只登记、不升格 |
| `gate_live` | 须 audit-sandbox 根且非 dry-run；E-OPS-03b skip 不单独证明隔离 | 先验 resolve 必须出现在证据链 |
| staged_fixture | 宏增量 fixture 模式 ≠ 产品默认 | E-INC-BUNDLE 清 OVERRIDE 后不得用 staged 冒充 product_default |

---

## 4. FRED 合并四门槛与删除顺序

### 4.1 立即（G1-02 / 工作包 3～4a）— 启用拆干净

| 留 | 删 |
|----|----|
| series 水位线注入、FRED binding / `execute_binding` 编排壳 | 任何「顺便强制打开源」（含委托 ESR 的 enable 工厂、双份 `enabled_fred_*`） |

### 4.2 合并四门槛（ADR-018 §3；decision-map #3）

须**同时**满足；**最迟 G1-08 前**合并关账或审阅 ADR 废止：

1. **启用已外置：** 全库无 `enabled_source_registry` / 强制 `_platform_allows` / 双份 `enabled_fred_*`  
2. **水位线形状对齐：** `since_by_series` ↔ 通用 `since_by_instrument`（或统一命名）可互换；proxy 仅取数前注入  
3. **执行壳对齐或新 ADR：** 同走 `run_macro_incremental` 族，或书面证明 `execute_binding` 不可消除差异  
4. **同参反证绿：** 沙箱 overlay 下 preview/incremental 与通用路径同 source/status/reason  

台账：`T01-ENABLE-FRED-MERGE-001`（`docs/quality/待修复清单.md`）。

### 4.3 重复 enable 工厂删除顺序（ADR-018 §4；decision-map #4）

1. 落地「问开关」接口（工作包 3）  
2. 全部调用方只问该接口（含 CLI backfill、matrix、各 `enabled_*`）  
3. **先删** `fred_incremental_watermark.py` 内重复 `enabled_fred_source_registry`；`fred_incremental_run` 薄委托或一并删  
4. 全库 rg：`enabled_source_registry`、`object.__setattr__(.*is_enabled`、`_platform_allows\s*=` — 生产路径为零（测试仅允许构造 overlay 输入）  

合并完成后：删 `FredIncrementalFetchProxy`（或零逻辑别名后再删）；rg 无第二套 enable；E-INC-FRED 策略路径改为只读问开关 + 编排备注。

---

## 5. G1-01 清单必须进入执行计划的入口 ID（不得遗漏）

> 权威：`g1-01-wiring-inventory.md` §3 责任矩阵「task-01 / G1-02」行 + r6 闭环控制点名项。  
> **原则：** 下列 ID 须在 G1-02 执行计划中有明确处置（清 OVERRIDE / 改问开关 / 正规 overlay / 删除或迁入正式链 / 降档知情）；不得口头「没人用」省略。

### 5.1 核心 OVERRIDE / 策略消费者（必清）

| ID | 为何进计划 |
|----|------------|
| **E-CLI-20** | **全金路径** OVERRIDE（fred 编排壳 + else ESR）；r6 CC-5：不得只清 fred |
| **E-CLI-13** | mootdx `enabled_source_registry` |
| **E-INC-FRED** | 与 BUNDLE 同模式 OVERRIDE；编排≠启用权威；挂钩 ADR-018 / 合并台账 |
| **E-INC-AV** | OVERRIDE-MEM |
| **E-INC-UST** | OVERRIDE-MEM |
| **E-INC-BIS** | OVERRIDE-MEM |
| **E-INC-WB** | OVERRIDE-MEM |
| **E-INC-CFTC** | OVERRIDE-MEM |
| **E-INC-CNINFO** | OVERRIDE-MEM |
| **E-INC-SEC** | OVERRIDE-MEM |
| **E-INC-DER** | OVERRIDE-MEM |
| **E-INC-BUNDLE** | `load_incremental_route_bundle` / 强制 `_platform_allows` + staged_fixture |
| **E-ACC-01** | matrix preview=OVERRIDE（含 baostock）；live 宏源常 OVERRIDE |

### 5.2 验收 / 隔离 / 暗门 / bridge（知情 + 处置）

| ID | 为何进计划 |
|----|------------|
| **E-ACC-BRIDGE-01** | r6 点名；零外部调用仍须处置；删除/并入 E-OPS-03 条件 |
| **E-ACC-ISO-01** | `ensure_isolated_db` 无内置隔离 assert；任意根可写 registry |
| **E-ACC-SKIP-01** | `danger_skip_isolation`；永久禁升格 |
| **E-OPS-03a** / **E-OPS-03b** / **E-ACC-02** | accept-source-route-db；gate_live 与 skip 诚实边界 |
| **E-OPS-01** / **E-OPS-02** | ops packaging；转发须套用对应 E-CLI 档位 |

### 5.3 Registry 同步与 SSOT 基准

| ID | 为何进计划 |
|----|------------|
| **E-REG-01** | `qmd-sync-registry` |
| **E-REG-02** | init-basic（与 G1-04 交界；清单要求 G1-02 吃进） |
| **E-REG-03** | `qmd-init-db --sync-registry` |
| **E-REG-04** | `DataSyncOrchestrator.bootstrap(sync_registry=True)` |
| **E-SVC-01** | SSOT-DEFAULT 基准；同参对照 |

### 5.4 测试专属注入（必须改写/删除）

| ID | 为何进计划 |
|----|------------|
| **E-TEST-01** | `service_path_support` monkeypatch |
| **E-TEST-02** | `_enable_*_route` `__setattr__` |
| **E-TEST-03** | orch fixtures 直接 `sync_to_db` |
| **E-TEST-04** | bootstrap(sync_registry=True) 测试覆盖 |
| **E-TEST-05** | audit remediation 直接 sync |
| **E-TEST-06** | `test_syncToDb_*`（单测 API；不得作产品同路证据） |

### 5.5 同参探针（验收输入，非入口但计划须绑定）

| 探针 | 产品默认期望（无 overlay） |
|------|---------------------------|
| **P-DAILY** | READY / baostock |
| **P-MINUTE** | DISABLED_SOURCE + 授权类 reason |
| **P-MACRO** | DISABLED_SOURCE |
| **P-SUPP** | VALIDATION_ONLY_BLOCKED（工作包 2 另修默认策略；G1-02 不得用 OVERRIDE 冒充） |

### 5.6 明确不在 G1-02「选源闭环」主责、但计划应降档知情

| ID | 边界 |
|----|------|
| E-CLI-01～12、E-CLI-30 | 主责多在 G1-04；G1-02 须保证其不再依赖 OVERRIDE（尤其 E-CLI-12 执行侧） |
| E-SCH-01/02 | 主责 G1-05；FIND-3-01 双轨雾区 |
| E-CLI-40～43 | N/A-POLICY；不得作策略证据 |

---

## 6. task_plan / gate1 相对权威的缺口表

| 缺口 | 证据（权威有 / 计划缺） | 建议写入计划何处 |
|------|-------------------------|------------------|
| **两层拆分未写成工作包验收句** | ADR-018 §1 明确开关本三字段 vs 安检；`task_plan` 工作包 3 / §4A 仍写「唯一接缝 / RoutePlan 风格整层输出」 | 工作包 3：拆成「3-开关本 API」+「安检只读合成」；§4A 增加「问开关」子表，与整层策略查询并列 |
| **问开关输入仅三键** | ADR-018 / §5.2.1；§4A 输入含 platform/frequency/授权上下文（整层） | 工作包 3 RED：断言问开关签名 = `source_id,data_domain,operation`；platform 等不得塞进第一层 |
| **`overlay_revision` 进入血缘** | ADR-018；gate1 唯一接口输出含 overlay revision；工作包 3A 写「策略版本/指纹」但未点名 overlay revision 字段名 | 工作包 3/3A + 与 task-02 交接：`activation_overlay_revision` 可观察字段 |
| **沙箱正规 overlay 测法** | ADR-018 §2；decision-map #2；工作包 3 仅写「构造受控配置」、未写「隔离根 + overlay 表/接口」 | 工作包 3 测试资产处置 + G1-02 验证证据：隔离根写 overlay、档位标签 |
| **证据档位枚举** | inventory 六档位；ADR-018 禁升格；task_plan/gate1 **未**列出档位名与禁升格规则 | G1-02 验收节或工作包 5：强制引用 inventory §1 档位表 |
| **E-CLI-20 全金路径** | inventory + r6 CC-5；task_plan 4b 只提「回填/预览例外」，未写「fred + else 全金路径」 | 工作包 4b：点名 E-CLI-20；验收「只清 fred 漏 else → FAIL」 |
| **E-INC-\* 全表** | inventory §1.4 九工厂 + BUNDLE；工作包 4a 只点名 macro_common + fred_watermark | 工作包 4a：入口 ID 清单 = §5.1 全表；rg 刷新调用方 |
| **E-ACC-BRIDGE-01 处置条件** | inventory + r6；task_plan/gate1 **未**提及 bridge | G1-02 清理清单：删除模块或并入 E-OPS-03；禁止口头漏登 |
| **E-ACC-ISO / SKIP / OPS-03 档位诚实** | inventory §1.6；计划未写入 G1-02 证据禁令 | G1-02 验证门：danger_skip 禁作证据；skip 须先验 resolve |
| **FRED 合并四门槛 + G1-08 截止** | ADR-018 §3；台账 T01-ENABLE-FRED-MERGE-001；task_plan 4a 未写四门槛/废止 ADR 选项 | 工作包 4a：区分「G1-02 拆启用」vs「G1-08 前合并关账」；链待修复清单 |
| **删除顺序** | ADR-018 §4；工作包未写 1→2→3→4 顺序（尤其「先删 watermark 拷贝」） | 工作包 3→4a 依赖说明：按 ADR 删除顺序执行 |
| **gate1 G1-02 验收仅三种同参** | gate1：「允许／未授权／能力缺失」；ADR-018 还要求沙箱同参反证、禁升格、清 OVERRIDE rg | 扩展 G1-02 验证证据行：三探针 + rg 清零 + 沙箱 overlay 档位 + E-CLI-20 反证 |
| **gate1「唯一策略入口」易误读为一层函数** | ADR-018 弃用方案 A；gate1 措辞「有效启用 + capability 查询成为唯一策略入口」 | 改写为：「问开关 + 安检只读」双接缝；capability 属安检层 |
| **ADR-018 索引进 task_plan 权威列表** | gate1 已列 ADR-018；task_plan §3 权威来源列表仍以 ADR-017 / data_sources 为主，**未显式列 ADR-018** | task_plan §3 / Gate 0 后补「ADR-018 Accepted」为启用接缝 SSOT |
| **reason_code 具体枚举** | 要求机器可读 + §4A 若干类别；**无** design 级开关本专用码表 | 见 §7 UNVERIFIED；计划应「复用 ERROR_CODE_GUIDE / 既有 route status」或开 design 审阅，禁止自造静默同义 |
| **overlay migrate / DDL 落地步骤** | §5.2.1 SQL 草案；decision-map 雾区；工作包 3「经 Gate 0 批准的启用配置/存储」过粗 | 工作包 3：显式 migrate 触及文件；若改表字段须用户审阅 design + promote（ADR-018 后续动作 5） |

---

## 7. UNVERIFIED（找不到权威）

下列事项在已列 primary sources 中**找不到**可执行级权威定义；执行计划不得假装已裁定：

| 项 | 已找到的边界 | 缺失内容 |
|----|--------------|----------|
| **开关本 `reason_code` 完整枚举表** | 须机器可读、全入口一致；§4A 举例偏整层（`USER_AUTH_REQUIRED`、禁用、能力缺失、平台不支持） | 开关本独有码（如「无 overlay / 已撤销 / enabled=false」）的规范列表与命名 |
| **Python/API 符号名** | 行为契约（问开关 / 表形） | 函数/类/模块最终命名（如 `ask_activation` 等）— **UNVERIFIED**，由实现选型但不得改语义 |
| **`overlay_id` / `revision` 生成算法** | 字段存在且 revision 须可观察 | UUID vs 单调版本、与 RoutePlan 字段的精确映射实现细节 |
| **管理员写 overlay 的 CLI 子命令名** | ADR-017：受控配置/CLI；R8 | 具体命令字、参数、权限模型 — 未在本轮 sources 钉死 |
| **「标明测试/沙箱用途」的强制标记字段** | ADR-018 要求标明；表形有 `reason`/`changed_by` | 是否有专用 flag 列 vs 约定 reason 前缀 — **UNVERIFIED** |
| **FRED 水位线统一命名最终词** | decision-map：`since_by_series` ↔ `since_by_instrument`（或统一命名） | 最终统一字段名未在 ADR 钉死 |
| **合并废止 ADR 的编号/模板** | 允许「另立审阅 ADR 废止合并」 | 废止文具体格式以外的内容 — 非本票可猜 |
| **E-ACC-BRIDGE-01 删除的精确截止切片** | 「G1-02 后无生产引用则删除或并入 E-OPS-03」 | 是否必须在 G1-02 GREEN 当切片关闭，或可延到工作包 5 — 措辞未钉死单一 checkbox |

**非 UNVERIFIED（已有权威，仅属后续切片）：** Validation 全链 → G1-03；scheduler 双轨 FIND-3-01 → G1-05；UI → 不阻塞 Gate 1A。

---

## 8. 研究结论（给 G1-02 执行计划作者）

1. **必须对齐的最小接缝：** 输入 `(source_id, data_domain, operation)` → 输出 `(is_allowed, reason_code, overlay_revision)`；安检另层；禁止内存 OVERRIDE。  
2. **必须对齐的持久化：** `source_activation_overlay` 表形（§5.2.1）；有效启用 = 基础 + 最新未撤销 overlay + 安检各项。  
3. **必须对齐的退役条件：** 删除顺序四步；FRED 启用撬门 G1-02 立即删；编排合并四门槛 + 最迟 G1-08 / 或废止 ADR；台账 `T01-ENABLE-FRED-MERGE-001`。  
4. **必须对齐的证据：** 隔离根正规 overlay；inventory 档位禁升格；r6 点名 E-CLI-20 全金路径与 E-ACC-BRIDGE-01。  
5. **计划缺口重心：** `task_plan` 工作包 3/§4A 与 `gate1` G1-02 行仍停留在 ADR-017「一层唯一策略」语气，**尚未吸收 ADR-018 两层形状、入口 ID 全表、合并门槛与档位禁令** — 应用本报告 §5–§6 补进执行计划后再开 RED。

---

## 9. 溯源索引（快速跳转）

| 主题 | Primary |
|------|---------|
| 两层最小字段 | ADR-018 §1；decision-map #1 |
| 表 DDL | data_sources.md §5.2.1 |
| 禁内存绕过 | ADR-017 §1 + 后果表；§5.2.1 末段 |
| 沙箱/档位 | ADR-018 §2；inventory §1 图例 |
| FRED 四门槛 | ADR-018 §3；decision-map #3；待修复清单 `T01-ENABLE-FRED-MERGE-001` |
| 删除顺序 | ADR-018 §4；decision-map #4 |
| 入口 ID | inventory §1.3–1.7、§3；r6 Summary/CC-3/CC-5 |
| 计划现状 | task_plan §4A、工作包 3/4a/4b；gate1 G1-02 行 |

---

*本文件为研究笔记，不构成 design 变更，不构成实现关账。*
