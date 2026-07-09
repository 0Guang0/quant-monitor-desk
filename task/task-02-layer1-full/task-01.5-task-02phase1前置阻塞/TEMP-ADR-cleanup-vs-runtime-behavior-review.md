# 【临时审阅】删掉的 ADR vs 代码里还在跑什么

> **性质：** 供你拍板「只改链接」还是「改代码/改文档」。不是正式 ADR。  
> **日期：** 2026-07-09  
> **查证：** GitNexus + `MIGRATION_MAP.md` + 磁盘 ADR 清单 + 代码 Read。

---

## 0. 什么叫「最终成品」——以后只认这些

| 层级                                         | 是什么                                                                                                  | 通俗理解                                                                                                      |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **根决策（项目第一天就有）**                 | `quant_monitor_implementation_docs_v1` 里 **ADR-0001～0005**                                            | DuckDB 本地优先、Agent 只读不写库、Layer1 才做全套标准化、Layer3 锚点模型、数据源 Primary/Validation/降级策略 |
| **你审过并保留的 ADR**                       | 本仓 `docs/decisions/` 里仍在磁盘上的：**003、004、007、009、010、011、015、016**（含改名后的 009/015） | 须**逐条**与 `MIGRATION_MAP` design 核对；下文 **§1.5** 已核对 **004、011**                                   |
| **成品设计图**                               | `**MIGRATION_MAP.md` 索引的全部 `**/design/`** 文件**                                                   | 模块长什么样、数据怎么流、API/Agent 边界——**R4 = 和这些文件一致**                                             |
| **底层长期事实（默认生效，本文不单独讨论）** | 接入写入顺序、DB CHECK 分工等已在保留 ADR 与 design 里落地的规则                                        | 不用每次会话重新争论                                                                                          |

**你已删掉的大部分 ADR** = 某个阶段、某张任务票、某个切片的**临时口径**；文档没了，但部分**安全开关**还留在代码里。  
本文只处理：**删文档后仍运行的东西**，并按「和成品一不一致」分两区。

```text
最终成品 = ADR-0001～0005 + 保留 ADR + MIGRATION_MAP 设计图
删掉的阶段性 ADR ≠ 自动删掉代码里的开关
```

---

## 1. 怎么读本文

每个条目两类标签：

| 标签         | 含义                                                                            |
| ------------ | ------------------------------------------------------------------------------- |
| **A + 数字** | **只改文字/链接**即可，**不改变**程序行为（报错里的文档路径、契约书目、注释等） |
| **B + 数字** | **程序里仍在执行**的规则；要动就得改代码或正式改设计                            |

全文分 **两大区**：

| 区域                | 含义                                                                       |
| ------------------- | -------------------------------------------------------------------------- |
| **一区·符合成品**   | 和上面「最终成品」**同方向**，属于补强或执行细节；优先保留，顶多补链接     |
| **二区·冲突或分歧** | 和成品**对不上、名字过时、两套口径并存**；需要你决定改代码、改文档还是退役 |

---

## 1.5 保留 ADR 专项核对：004「复杂度不修」、011「backfill 上限」

> 按你的要求：不能只因「文件还在 `docs/decisions/`」就默认合规，必须对照 **MIGRATION_MAP 索引的 design**。

### 白话：这两项分别是什么？

| 保留 ADR              | 一句话（产品/业务）                                                                                       | 代码里实际在干什么                                                                      |
| --------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **004 复杂度不修**    | 「写入路由那两段核心代码允许继续又长又分支多，**不靠大重构降复杂度**；以后真加第四种写入域再拆。」        | 不拦用户操作；只影响开发者是否被 linter（C901）逼着拆 `WriteManager` / `SourceRegistry` |
| **011 backfill 上限** | 「一次回补命令不能无限拉历史：默认最多 **3 个时间片**，单片最多 **31 自然日**，整条命令硬顶 **12 片**。」 | `qmd data backfill` / `full-load` 规划日期窗时超限报错或 `--truncate-to-cap` 截断       |

### 权威 design 怎么说？（MIGRATION_MAP 索引）

| 主题                 | 权威文件（均在 `**/design/`\*\*）                                      | 成品口径（摘要）                                                                                     |
| -------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| backfill 能拉多长    | `docs/ops/design/performance_limits.md` §8                             | **默认 5 个交易日**，**最多 20 个交易日**（backfill 日期窗口表）                                     |
| backfill 流程约束    | `specs/contracts/design/runtime_flow_contract.yaml` · `flows.backfill` | **默认 5 个交易日**；须用户确认；磁盘 <20GB 暂停                                                     |
| backfill 怎么跑      | `docs/modules/design/data_sync_orchestrator.md` §13.4.3                | 范围过大要检查并**自动拆分**（**未写** 31 天 / 3 片 / 12 片数字）                                    |
| 盘后禁止大回补       | `runtime_flow_contract` · `daily_after_close.forbidden`                | 禁止 `large_backfill`（与「单次 CLI 上限」是不同层）                                                 |
| WriteManager 形态    | `docs/modules/design/write_manager.md`                                 | 规定**写什么、怎么校验、怎么写库**；**未要求**也**未禁止**函数复杂度                                 |
| 004 / 011 是否在 MAP | `MIGRATION_MAP.md` 全文检索                                            | **无 ADR-004 卡片**；**无** `bounded_backfill_cap.yaml`（该文件在 `specs/contracts/`，非 `design/`） |

### 核对结论

| 保留 ADR                         | 与成品关系                                                                                                                                        | 分区                                          |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| **004**                          | **不冲突** — 属于工程/审计收口（Round2 `D3-P1-2`），不改变用户可见行为；成品 design **沉默**于复杂度，故 004 是**开发纪律**，不是产品形态         | **一区补强**（见 **B11**）                    |
| **011（backfill 上限部分）**     | **有分歧** — 成品用 **交易日 5/20**；现行 CLI 用 **自然日 31 × shard 数 3/12**，且 **未接** `us_trading_calendar` / CN 交易日历做 backfill 窗计数 | **二区冲突**（见 **B19**）                    |
| **011（文件名里的 CI nightly）** | ADR-011 **正文为空**；夜间 live 网络在 `docs/ops/nightly_ci.md`，与 backfill 上限**不是同一件事**                                                 | **二区** — 命名/文档张冠李戴（见 **B19** 末） |

---

# 一区·符合最终成品（补强，建议保留）

> 这些行为是在帮成品设计「落地」：不污染主库、不默认真上网、数据进对表、验收诚实等。

---

## 一区 · A 类（只改链接，行为不变）

### A1 · 报错里还指着已删的「真上网 ADR」

- **在哪：** `data_commands.py` 里 live-fetch 失败时的 `docs_anchor`
- **现在写什么：** 已删的 `ADR-008-product-live-env-gate.md`
- **处理：** 保留 ADR **015** 的环境门说明，或写 `product_live_gate.py`
- **和你无关的术语：** 只是报错 JSON 里多一行「去哪读说明」，**程序不靠打开这个文件才拦截**

### A2 · 报错里还指着已删的「必须点名数据服务 ADR」

- **在哪：** `data_commands.py` 另一处 `docs_anchor`
- **现在写什么：** 已删的 `ADR-006-sync-datasource-service-fail-closed.md`
- **处理：** `docs/modules/design/data_sync_orchestrator.md`（成品里已写：产品路径禁止偷偷用 adapter 绕过）
- **业务话：** 用户看到报错时，应被引向**正式模块设计**，不是一张已撕掉的任务 ADR

### A3 · Phase1 验收失败还链到旧文件名 `tier-a-live-acceptance`

- **在哪：** `phase1_acceptance.py`
- **处理：** 保留的 `ADR-015-live-acceptance-sandbox-dual-track.md`
- **业务话：** 隔离库验收入口没变，只是文档改名了

### A4 · 契约 YAML 的 `adr_refs` 书目断链

- **在哪：** `specs/contracts/source_route_db_acceptance_contract.yaml`
- **问题：** 仍列已删的 008、旧名 015-tier-a
- **处理：** 015 新文件名 + 016；008 删掉或改指 015/代码
- **业务话：** 给审计/人看的「依据列表」，**不参与**矩阵怎么跑

### A5 · `docs/decisions/README.md` 索引表过时

- **问题：** 仍链 005/006/008/012～014 等已删或不存在文件
- **处理：** 只列磁盘上真实存在的保留 ADR + 注明 v1 五篇在 `docs/architecture/design/08_decision_log_index.md`
- **业务话：** 目录别把人领进死胡同

### A6 · 运维速查、OpenWiki 里的旧 ADR 路径

- **在哪：** `data_sync_quick_reference.md`、`openwiki/workflows/data-sync-and-live-gates.md` 等
- **处理：** 保留 ADR + design 路径；删掉的编号改为「见 MIGRATION_MAP / data_sources.md」
- **业务话：** 运维文档和成品口径一致

### A7 · 代码注释里的「ADR-008」「ADR-006」字样

- **在哪：** `product_live_gate.py`、`runners.py`、`baostock_incremental_run.py` 等
- **处理：** 改成「环境门」「显式 DataSourceService」等白话，或指向保留 ADR/ design
- **业务话：** 给开发者看的便签，**不影响**用户怎么用产品

---

## 一区 · B 类（代码仍在跑，且与成品一致）

### B1 · 真上网要用户自己「开门」——原阶段性 ADR-008，现由 ADR-015 承接政策

- **你感受到什么：** 不设环境变量 `QMD_ALLOW_LIVE_FETCH=1`，同步/拉数**不会默认真访问外网**；资源紧张时也会被拦住。
- **为什么符合成品：** ADR-015 明确写了同一规则；`06_deployment_and_local_ops.md` 写明「进了 sandbox 也不等于已授权 live」。
- **代码在哪：** `product_live_gate.py`
- **建议：** **保留代码**；政策以 **ADR-015** 为文档 SSOT，不必恢复 008 文件。

### B2 · 生产同步必须走「正式数据服务」——原阶段性 ADR-006

- **你感受到什么：** 正式跑增量/回补/对账时，不能靠内部默认 adapter「偷偷拉数」；必须走你配置好的 `DataSourceService` 和路由计划。
- **为什么符合成品：** `data_sync_orchestrator.md` 写死——产品 CLI、验收、clean 写入**不得**用 adapter 旁路；仅测试可例外。
- **代码在哪：** `runners.py` 里 `guard_production_datasource_service_required` 等（改动影响面大，属核心护栏）。
- **建议：** **保留**；文档指 `data_sync_orchestrator.md` + ADR-0005 源角色，不恢复 006 文件。

### B3 · 对账时注入的抓取端口也必须过 live 门——原 ADR-008 延伸

- **你感受到什么：** 对账若带了自定义抓取实现，必须是「产品 live 模式」下构建的服务，不能绕开门禁。
- **为什么符合成品：** 与 B1、B2 同一套「不静默真上网、不绕路由」。
- **代码在哪：** `guard_reconcile_product_live_service`
- **建议：** **保留**，与 B1/B2 一并视为成品安全链。

### B4 · 验收和矩阵 live 必须用隔离库，不能写日常主库

- **你感受到什么：** `QMD_DATA_ROOT` 须在 `.audit-sandbox/...` 下；指向 `data/duckdb/quant_monitor.duckdb` 主库会被拒绝。
- **为什么符合成品：** ADR-015/016 + `06_deployment_and_local_ops.md`；与 ADR-0001「WriteManager 单写」一致。
- **代码在哪：** `acceptance_isolation.py`、`resolve_matrix_data_root`（要求路径含 `**source-route-db`\*\*）
- **建议：** **保留**；这是「能真拉网验货但不弄脏主库」的产品承诺。

### B5 · 22 源矩阵「诚实关账」——保留 ADR-016

- **你感受到什么：** 全矩阵报告里，QMT/iFinD 没牌照可以标红但**不挡发布**；SEC 网络坏了可以标外部失败并登记延期；**不能用假数据把行刷绿**。
- **为什么符合成品：** ADR-016 + `data_sources.md` 诚实源角色；与 ADR-0005「不能 silent switch」一致。
- **代码在哪：** `source_route_db_acceptance_matrix.py`、`production_gate.py`、契约 YAML
- **建议：** **保留**，这就是当前 release 关账 SSOT。

### B6 · 每个数据源增量写入哪张 clean 表——保留 ADR-009

- **你感受到什么：** baostock → 股票日线表；fred → 宏观观测表；巨潮 → 公告表……域错了就写不进去。
- **为什么符合成品：** `04_data_architecture.md`、WriteManager 流水线；ADR-0005 主源进 clean 的前提。
- **代码在哪：** `clean_write_targets.py`、migration 015
- **建议：** **保留**；文件名已去 `tier-a`，内容仍是成品一部分。

### B7 · Layer1 五轴从 clean 表读 P0 指标——保留 ADR-010

- **你感受到什么：** 宏观环境、信用、风险偏好、流动性、情绪五轴的**首批关键指标**从已清洗业务表读，不用「排练用假数据」冒充。
- **为什么符合成品：** ADR-0003「只有 Layer1 物化完整标准化」+ `layer1_global_regime_panel.md` + `specs/layer1_axes/design/...`
- **代码在哪：** `layer1_axes/clean_observation_reader.py`
- **建议：** **保留**；流动性轴用 alpha_vantage 作临时代理已在 ADR-010 写明 ponytail 路径。

### B8 · Layer2 VIX、Layer4 美股结构从 clean 读——原阶段性 ADR-013/014（文档已删）

- **你感受到什么：** VIX 传感器读 fred 清洗后的宏观序列；美股结构用美股**交易日**历；A 股默认 baostock，你显式指定 mootdx 则用 mootdx。
- **为什么符合成品：** `layer2_cross_asset_sensor.md`、`layer4_market_structure.md`、ADR-007、ADR-0005 路由语义——**不必**为每层各留一篇 ADR。
- **代码在哪：** `sensor_loader.py`、`market_structure.py`、相关 e2e 测试
- **建议：** **保留代码**；测试注释里的「ADR-013/014」可改为「ADR-010 原则 + 模块 design」。

### B9 · Layer5 证据能追溯到哪次抓取——原阶段性 ADR-012（文档已删）

- **你感受到什么：** 证据包要能挂上 fetch 编号和内容 hash，方便「这个结论依据哪份数据」。
- **为什么符合成品：** `layer5_security_evidence.md`、`snapshot_lineage_contract.yaml`、RESEARCHER_GUIDE 追溯字段。
- **代码在哪：** `layer5_evidence/provenance.py`
- **建议：** **保留代码**；若需要一篇短 ADR，应合并进 lineage/证据 design，不恢复 012 编号。

### B10 · 源健康「只读体检」和「写快照」分两条路——原阶段性 ADR-005（文档已删）

- **你感受到什么：** 日常健康检查（DH2）**不会**偷偷在库里建快照表；真正要写 `source_health_snapshot` 走单独 writer。
- **为什么符合成品：** `data_sources.md` 健康与审计边界；避免「查一下却改了库结构」。
- **代码在哪：** `data_health.py`（`DH2_FORBIDS_SNAPSHOT_DDL`）、`source_health_writer.py`
- **建议：** **保留代码**；README 里「005 待补」可改为指 `data_sources.md` §健康，或恢复极简说明页（不必恢复旧 005 全文）。

# 成品冲突或有分歧（需你拍板）

> 这些不是「有没有代码」的问题，而是**还在用旧任务口径**，容易让 Agent/会话继续按 M-DATA-03、Tier harness、11 源等**过期叙事**干活，拖慢 Phase 1。

---

## 二区 · A 类（先改链接，但改完仍要处理二区 B 的语义）

### A8 · 各处仍写「见 ADR-008 / ADR-006 做决策」

- **冲突点：** 会话若去读已删 ADR，会以为**没有 live 门**或**没有显式服务要求**——与 ADR-015、orchestrator design **相反**。
- **处理：** 同 A1/A2，但优先级**高于**一般断链——属于**误导型指针**。
- **改完后：** 以 ADR-015 + `data_sync_orchestrator.md` 为排障入口。

### A9 · README 仍把 012～014 列成「现行 ADR」

- **冲突点：** 让人以为每层还要单独 ADR 关账；成品已是 **MIGRATION_MAP 模块 design + ADR-010**。
- **处理：** 删掉或标「已合并进模块 design / ADR-010」。

### A10 · `RESOLVED_ISSUES_REGISTRY`、测试 docstring 仍写「ADR-008 隔离库」

- **冲突点：** 把**环境门**和**隔离库**混在已删编号下，和 ADR-015 两段式叙述不一致。
- **处理：** 改为「ADR-015 隔离 + 环境门」。

---

## 二区 · B 类（和成品对不上，要决策改代码 / 改文档 / 退役）

### B13 · 两套沙箱文件夹名：`m-data-03` 和 `source-route-db` 并存

- **你应知道什么：** **成品 SSOT**（ADR-015 文首取代说明、phase1、矩阵 spine）要求 `**source-route-db`**。**  
  **但部分测试/fixture 仍创建 `**.audit-sandbox/m-data-03`\*\*（旧 M-DATA-03 任务名）。
- **冲突在哪：** 同一份 ADR-015 正文前半段还举 `m-data-03` 为例，后半段又说 harness 已退役——**读者不知道以哪条为准**。
- **代码：** `acceptance_isolation.M_DATA_03_SANDBOX_SEGMENT` vs `SOURCE_ROUTE_DB_SANDBOX_SEGMENT`
- **请你拍板：**
  - **解决方案：** 测试全部迁到 `source-route-db`，ADR-015 删掉 m-data-03 作主路径的表述，常量 `m-data-03` 退役（删除清理干净）。
  -

### B14 · 代码里满屏「Tier A」命名，但 Tier harness 已退役

- **你应知道什么：** ADR-015 写明 `tier_*_live_acceptance` **已退役**；成品关账是 **22 源矩阵 + SourceRouteDbAcceptanceSpine**。  
  但仍有：`live_tier_router.py`、`tier_a_fetch_operation()`、`TIER_A_SOURCES`、测试名 `test_tierA_`\*。
- **冲突在哪：** 「Tier A」在旧任务里 = **11 源验收 harness**；在 `data_sources.md` 里 = **源优先级/候选角色**。同名不同义，导致会话继续找 `tier_a_live_acceptance.py`（**已不存在**）。
- **代码：** `live_tier_router.py` 仍被 `product_live_ports.py`、增量 registry 使用——**源分档表本身可能还有用**，但名字像过期 harness。
- **请你拍板：**
  - **解决方案：** 重命名为 `live_prod_source_tiers` / `prod_source_tier` 等，去掉 Tier harness 联想（关联 task Plan Slice 0-N）。

### B15 · ADR-015 正文仍写「要跑 `scripts/tier_a_live_acceptance.py`」

- **冲突点：** 脚本**已不在仓库**；与 ADR-015 自己的「取代说明」**自相矛盾**。
- **成品应是什么：** `qmd-ops accept-source-route-db` + `production_gate.py`（ADR-016）。
- **解决方案：** 改 ADR-015 正文删旧句，或交小票统一修订——**这是文档债，不是可选美化**。

### B16 · ADR-015 里 M-DATA-03 / R4_SANDBOX / MODULE_COMPLETION_RATING 叙事

- **冲突点：** 大段绑定已关闭任务 **M-DATA-03** 和模块评级表，和 **MIGRATION_MAP = R4 唯一标准** 的现行规则容易混用——Agent 会去翻 `MODULE_COMPLETION_RATING.md` 当成品。
- **成品应是什么：** R4 以 **MIGRATION_MAP 索引 design 与实现一致** 为准（`MIGRATION_MAP.md` 文首已写）。
- **解决方案：** ADR-015 缩减为「隔离库 + 环境门 + 双轨测试原则」，把 MCR/任务票历史删除清理干净避免再当执行 SSOT。

### B17 · `11 源` vs `22 源` 口径残留

- **冲突点：** 保留 ADR-009 表仍是 DCP-05 的 **11 源 canonical domain**（成品增量金路径）；ADR-016 / task-01 是 **22 源矩阵**。  
  旧会话常把「11 源 Tier A 全绿」当成整个产品数据面 PASS——与 22 源 design **范围不同**。
- **解决方案：** 在 ADR-009 或 `data_sources.md` 触点加一句：**11 源 = 增量 clean 金路径子集；22 源 = 全注册表验收面**，避免混为一谈。（用户认为更好的解决方案是统一成一份文件不再散落到多处，总量是22个数据源）

### B18 · `docs_anchor` 指向 tier-a 文件名（与一区 A3 重叠，但属分歧源）

- **冲突点：** 用户看到 `ADR-015-tier-a-`\* 会以为还要 **Tier A 专用沙箱规则**，而不是统一的 source-route-db。
- **解决方案：** 改文件名链接（A3）+ 确认错误文案是否仍出现「Tier A」字样（`tier_a_fetch_operation` 报错信息）——若出现，归入 B14 一并改名。

### B19 · backfill 上限（ADR-011）与权威 design **数字和计量单位不一致**

- **你感受到什么：** 跑 `qmd data backfill --start … --end …` 时，系统按 **自然日** 切时间片；默认大约 **3×31 自然日** 量级（可 `--truncate-to-cap`），与运维手册里「**5～20 个交易日**」不是同一套尺子。
- **权威（成品）怎么说：**
  - `performance_limits.md`：**backfill 日期窗口 = 默认 5 交易日、最大 20 交易日**
  - `runtime_flow_contract.yaml`：`max_trading_days_default: 5`，且 `requires_user_confirm: true`
  - `data_sync_orchestrator.md`：只要求「过大则检查、拆分」，**没有** 31/3/12
- **现行代码（阶段性）怎么说：**
  - `specs/contracts/bounded_backfill_cap.yaml`（**不在** MIGRATION_MAP `design/` 索引）：每片 **31 自然日**，默认 **3 片**，绝对上限 **12 片**
  - `plan_backfill_shards()` 用 `timedelta(days=…)`，**未**调用 ADR-007 的 `us_trading_calendar` 或 A 股交易日历
- **冲突性质：**
  1. **单位：** 成品 = **交易日**；代码 = **自然日**
  2. **数值：** 成品默认 **5** 交易日；代码默认约 **93** 自然日窗（3×31）才触顶
  3. **SSOT 层级：** ADR-011 正文写「见权威文件」却指向 **非 design 索引** 的 YAML；真正权威应是 `performance_limits.md` + `runtime_flow_contract.yaml`
  4. **文件名：** ADR-011 含「CI nightly」，正文空；夜间 live 在 `nightly_ci.md`，易让人以为 011 = 夜间流水线而非 backfill

- **解决方案：** 改 `plan_backfill_shards` / CLI — 按 **交易日** 计数，严格对齐 **design权威文件（C:\Users\Guang\Desktop\quant-monitor-desk\docs\ops\design\performance\_[limits.md](http://limits.md)）**
-

- B11 · 写入热路径「暂不拆大函数」——保留 ADR-004（工程政策，非产品规则）
  - **你感受到什么：** **无**——不改变同步、看盘、Agent 任何对外行为。
  - **是什么：** 审计曾要求降低 `WriteManager` / 源注册校验函数的圈复杂度；004 决定**暂不重构**，用测试锁住行为，只有新增「第四种独立写入域」时才考虑拆 handler。
  - **冲突性质：** `write_manager.md` 只规定写入契约与边界，**没规定**代码必须简单或必须拆分，但是不符合最佳工程纪律
  - **代码在哪：** `WriteManager._execute_write`、`SourceRegistry._validate_domain_roles`（及对应测试）
  - **解决方案：** **本票 S7 重构** — 提取 helper 降 C901，行为由 `test_write_manager` / `test_source_registry` 锁定；修订 ADR-004（见 `task_plan.md` S7）
  ### B12 · 旧 CLI 已退役，报错会指向正式命令
  - **你感受到什么：** 再跑 `sandbox-clean-write` 等老命令会直接提示「已退役」，请用 `qmd-data data sync|backfill|...` + 隔离库。
  - **指向：** 与 ADR-015「source-route-db + qmd data」取代说明一致。
  - **代码在哪：** `phase1_acceptance.py` 里 `LEGACY_COMMAND_RETIRED`
  - **冲突性质：**保留这种方式容易引起歧义
  - **解决方案：** 把老命令与相关老路径的代码全部删除清理干净
  ***
  # 二区·与最终

---

## 2. 建议你优先拍的板（简表）

| 优先级 | 编号              | 问题                                            | 推荐                                          |
| ------ | ----------------- | ----------------------------------------------- | --------------------------------------------- |
| P0     | B15、B16          | 保留 ADR-015 正文与自身「已取代」矛盾           | 修订 ADR-015，删 tier 脚本与 M-DATA-03 主叙事 |
| P0     | A8～A10、A1～A6   | 断链/误导指针                                   | 小票 `DOC-ADR-ref-cleanup`，行为不变          |
| P1     | B13               | 两套沙箱路径                                    | 测试迁 `source-route-db`，退役 m-data-03      |
| P1     | B14、B18          | Tier 命名混淆                                   | 重命名或 ADR 里强制释义                       |
| P1     | **B19**           | backfill 5/20 **交易日** vs 31×shard **自然日** | 对齐 design（甲）或改 design（乙）            |
| P2     | B17               | 11 源 vs 22 源                                  | 保留 ADR 各管一段，加一句范围说明             |
| P2     | B11               | 004 复杂度不修                                  | 保留作工程纪律即可，非产品阻塞                |
| —      | 一区 B1～B10、B12 | 安全与数据正确性                                | **默认保留代码**，文档指保留 ADR + design     |

---

## 3. 查证索引（给后续执行）

| 业务问题                              | 入口                                                                        |
| ------------------------------------- | --------------------------------------------------------------------------- |
| 能否真上网                            | `product_live_gate.py` · ADR-015 §环境门                                    |
| 同步是否走正式路由                    | `runners.guard_production`\_\* · `data_sync_orchestrator.md`                |
| 验收能否写主库                        | `resolve_matrix_data_root` · ADR-015/016                                    |
| 数据进哪张表                          | `clean_write_targets.py` · ADR-009                                          |
| 矩阵能否关账                          | ADR-016 · `source_route_db_acceptance_contract.yaml`                        |
| 五轴数据从哪读                        | `clean_observation_reader.py` · ADR-010                                     |
| backfill 上限（**与 design 有分歧**） | `plan_backfill_shards` · 权威应对齐 `performance_limits.md` §8 · 见 **B19** |
| 复杂度不修（工程纪律）                | ADR-004 · `WriteManager` 测试锁行为 · 见 **B11**                            |

---

## 4. 本文件之后

1. 你确认二区 B13～B18 的方案（或口头回复）。
2. 执行 `DOC-ADR-ref-cleanup`（A1～A10）。
3. 按方案改 ADR-015 正文 / 测试沙箱路径 / Tier 命名。
4. **删除本 TEMP 文件**，避免与 `MIGRATION_MAP` + 保留 ADR 双 SSOT。
