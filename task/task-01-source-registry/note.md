# task-01-source-registry · 执行决策记录（note）

> **本文件记什么：** 执行阶段、计划未写死时的**临时拍板 / 方案取舍**（选了 A 不选 B、怎么接、做到哪停）。  
> **不记什么：** 问题现象、开放债、已修复证据 → 一律进 [`findings.md`](findings.md)；动作时间线 → [`progress.md`](progress.md)。  
> **不替代：** ADR / `task_plan` / `g1-02-execution-brief`。  
> **更新规则：** 计划未穷尽处**当场写入**；按票追加，不删历史。

---

## 票 03（3A）

| 议题                    | 备选                                      | 拍板                                                                                                                     |
| ----------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 平台放行                | 强制 `_platform_allows` vs 构造输入       | **自定义 `platform_matrix_path` YAML fixture**（构造输入，不 patch 规划器）                                              |
| overlay 与 fetch 不同库 | service 不传 con vs overlay 写入 fetch DB | **`enable_source_route(..., con=)` 写到 fetch 同一 DB**；此时 planner `activation_con=None`（避免被 `fetch(con=)` 覆盖） |
| 默认可关源再测安检      | 直接断言 vs 先开                          | **先 overlay 打开，再断言** license/env 等安检结果                                                                       |

---

## 票 04（3B）

| 议题                    | 计划未定处               | 拍板                                                                                                                                  |
| ----------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| 无 DB 时怎么问开关      | brief 只写「只读合成」   | **有 `con` → `ask_activation`；无 `con` → 回落 YAML 内存 `is_enabled`**（`ponytail` 过渡；产品 fetch 必须传 con）                     |
| 安检链顺序              | ADR 原则未钉死代码顺序   | **activation → capability → platform/license**（后果：默认关源常先出 `source_disabled_by_default`，见 findings F05-A7）               |
| `overlay_revision` 算法 | brief UNVERIFIED         | **透传 `ask_activation` 返回值**；无 overlay 用 `""`；只附加字段不改义                                                                |
| 3-OBS                   | 允许结构化日志，未定管道 | **stderr JSON**（对齐 `write_telemetry`）；事件 `source_policy_resolved` / `source_policy_denied`；`QMD_SOURCE_POLICY_TELEMETRY` 可关 |
| Service 改多少          | fetch CRITICAL           | **只透传 `con` 给 `plan`**，不改状态机                                                                                                |
| 本票是否清生产 ESR      | 范围边界                 | **不删**；留给 4a / 票 06·07                                                                                                          |

落点：`route_planner.py` · `route_models.py` · `service.py` · `event_payload.py`

---

## 票 05（3C）

| 议题               | 计划未定处    | 拍板                                                                                                    |
| ------------------ | ------------- | ------------------------------------------------------------------------------------------------------- |
| 「删 patch」落到哪 | helper 粒度   | **`enable_source_route` = overlay + sync_to_db`**；关账证据禁用 `__setattr__` / 强制 `_platform_allows` |
| 域默认关怎么测     | 改生产 YAML？ | **只改测试 registry 副本**（`domain_enabled_by_default` + capability op）                               |
| 本票是否清生产 ESR | 与 4a 边界    | **否**（05=夹具；清零属 4a/4b）                                                                         |

落点：`tests/service_path_support.py` · `test_etest_overlay_governance.py`

---

## 接线后回归怎么处置（用户确认后拍板）

| 议题              | 备选                              | 拍板                                                                                                                                        |
| ----------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 全量红怎么动      | 一律修生产 / 一律改测 / 先分再动  | **先分诊再修**（问题台账在 findings F05；此处只记分诊规则）                                                                                 |
| 分诊规则          | —                                 | **A** = 旧口径（ESR/`__setattr__` 或旧 skip 顺序）→ 清期望或迁 overlay，**挂 4a/4b**；**B** = YAML 本可启用但空库未 sync → **本切片修夹具** |
| 「清理」A 类测    | 删文件 vs 改夹具/断言             | **不删测文件**；清旧期望/旧撬门                                                                                                             |
| B 修哪里          | 改 `sync_to_db` / 改 ask / 改夹具 | **只加测试 helper `seed_activation_base`**（调用既有 `sync_to_db`，不改 HIGH 符号）                                                         |
| 编排器模块 DB     | 模块级 sync 一次 vs 每测 sync     | **每测 sync**（因 `truncate_mutable_tables` 清空含 `source_registry`）                                                                      |
| 本切片修到哪      | B+A / 只 B                        | **先只修 B**（用户选定）；关账前又闭环 **A7** 断言（对齐 ADR-018 先开关）                                                                   |
| A7 断言（关账前） | 挂起 vs 本阶段改                  | **本阶段改**：默认先 `source_disabled`；overlay 后再 `missing_env`                                                                          |

问题开闭与证据：**只写在 findings**（F05-A **测债已关**·node-id 表仍保留作证据；F05-B·A7 已关；开放见 findings 开放项），此处不重复 ledger。双登记：`docs/quality/待修复清单.md` + 仓库根 `PROJECT_IMPLEMENTATION_ROADMAP.md`。

---

## 04/05 质量复核拍板（2026-07-11）

| 议题                                                 | 拍板                                                                             |
| ---------------------------------------------------- | -------------------------------------------------------------------------------- |
| `_emit_source_policy_event` 字段 allowlist frozenset | **删掉**；自建 payload + 滤掉 `None`（行为不变）                                 |
| `bootstrap_vendor_e2e_db` 重复 sync                  | **复用** `seed_activation_base`                                                  |
| etest 重复 assert `write_activation_overlay`         | **删一行**                                                                       |
| 测试 import 私有 `_platform_key`                     | **不做**（避免测试耦合私有符号）                                                 |
| `enable_source_route` 内存改副本                     | **暂留** → findings **T01-F06** → 票 06                                          |
| 无 con 内存回落                                      | **暂留** → findings **T01-F07** → 票 06+07 后删                                  |
| 阶段性代码混放正式路径                               | **未发现**需迁 `phase-scripts` 的 04/05 产物（实现在 `backend/`，测在 `tests/`） |

---

## 刻意未做（范围拍板，非问题列表）

- 不为保绿恢复 ESR / `__setattr__` / 强制 platform
- 不改 `**/design/**`、不 promote
- 本切片不做 4a/4b 全量迁 overlay
- 不以全量 pytest 绿宣称 04/05 或 G1-02 关账

---

## 票 01–05 独立评审边界（2026-07-12）

| 议题         | 拍板                                                                                                                 |
| ------------ | -------------------------------------------------------------------------------------------------------------------- |
| 审查基线     | **`0cad574f`**（票 01–05 已提交状态）；不把当时未提交的 06/07 改动计入 01–05 结论                                    |
| 审查动作     | **只审查、不改实现或权威设计**；可执行问题进 findings T01-F08～F12                                                   |
| 下一执行顺序 | **不得直接把 06/07 当作唯一下一步**：先由用户确认是否插入 F08/F09/F11/F12 纠正切片；F10 在正式管理员写入口前必须闭合 |

---

## 票 06∥07（4a/4b）现场拍板（2026-07-12）

| 议题                                       | 备选                                              | 拍板                                                                                                                           |
| ------------------------------------------ | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| sync dry-run 是否静默 ensure overlay       | 像 backfill 自动写 vs 显式夹具                    | **不静默**（保留「未启用 → DISABLED」反证）；测侧显式 `prepare_audit_sandbox_route_activation`；有 duckdb 则 preview 传 `con=` |
| mootdx `--source-id` 与域 primary=baostock | 事后改 selected_source_id vs 规划期钉 primary     | **规划期** `plan(preferred_primary_source_id="mootdx")`（不改 registry 副本；正式路径禁 `build_sandbox_route_planner`）        |
| matrix live 与 preview domain/op 不一致    | 只按 request 写 overlay vs 按 live 实际 domain/op | **live 实际值为主**，若与 request 不同再 `ensure` 合并 request 侧（`_matrix_live_route_planner`）                              |
| F06 本切片是否关                           | 关 / 暂留                                         | **暂留**（`build_sandbox_route_planner` 仍改副本 domain/capability；升级路径另记 findings）                                    |
| F07 是否本切片删 YAML 回落                 | 06+07 后立刻删 vs 另切片                          | **另切片再删**（先保证正式入口皆传 `con`）                                                                                     |
| FRED 编排合并台账                          | 随 06 关 vs 票 10                                 | **不关**（`T01-ENABLE-FRED-MERGE-001` → 票 10）                                                                                |
| 本切片关账口径                             | pytest 绿即 Execute CLOSED vs 须 completion-check | **须 `/completion-check`**；pytest 绿 ≠ G1-02/R4                                                                               |

## 票 06∥07 联审 disposition（2026-07-12）

| 发现                                                   | 处置                                                                                                                           |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `service_path_support` 三死 helper                     | **本轮已删**（非阶段外置）                                                                                                     |
| 生产包 `build_sandbox_route_planner` 内存撬门          | **本轮已迁出**：正式路径 `build_activation_route_planner` + `plan(preferred_primary_source_id=)`；副本构造仅留 `tests/`（F06） |
| 金路径「只清 fred」反证在 phase-scripts                | **按 TEST-EVIDENCE-GOVERNANCE 故意拆开**；票 07 / 测试模块 docstring 已对齐；非缺项                                            |
| backfill/mootdx 沙箱 `ensure_sandbox_route_activation` | **按本切片拍板保留**（仅 sync dry-run 禁静默）                                                                                 |
| 删 meta 测文件                                         | **测试资产治理**（非 F05-A A1–A6）；不记新债                                                                                   |
| F06                                                    | 阶段外置 → **票 08 后**（仅 tests 夹具零构造；生产包硬违规已闭环）                                                             |
| F07                                                    | 阶段外置 → **票 08 后**删回落                                                                                                  |
| F08/F10/F11/F12                                        | 原「待修复」无绑票 → **阶段外置并绑票 09 前/票 09**（双登记）                                                                  |
| F09                                                    | 代码已改 → **票 09 证据前独立复验**                                                                                            |
| F03 余 + `enabled_*` 误导名                            | → **票 08**                                                                                                                    |
| FRED 合并                                              | → **票 10**（不变）                                                                                                            |

## 票 06∥07 · L5 审查清零拍板（2026-07-12）

| 议题                   | 备选                                  | 拍板                                                                             |
| ---------------------- | ------------------------------------- | -------------------------------------------------------------------------------- |
| 审查等级               | 只报 L5 / L3–L5 全收                  | **L5 为主，L3/L4 同类一并清零**（金融量化）                                      |
| 沙箱根判定             | 子串 `.audit-sandbox` vs 路径段       | **路径段精确**；`source-route-db` 允许 `source-route-db-*` 前缀段                |
| preferred 域外源       | 一律禁止注入 vs capability 声明才可升 | **capability 声明该域才可升 Primary**（保留 mootdx CLI 钉源；禁 fred→cn_equity） |
| sync/backfill 选源校验 | 各写一份 vs 共享                      | **`raise_if_ready_selected_mismatch`**                                           |
| preview 构造           | 各写一份 vs 共享                      | **`plan_with_preferred_primary`**                                                |
| ensure 后构 planner    | 仍在 writer 内 vs 出锁                | **出锁后再 `build_activation_route_planner`**                                    |
| 业务套件源码 meta-test | 留 / 删                               | **删**（hygiene phase-scripts 已覆盖）                                           |

## 并行会话边界（2026-07-12）

| 议题              | 拍板                                                                      |
| ----------------- | ------------------------------------------------------------------------- |
| 测债治理 vs 票 08 | **分线**：测债不改 `backend/`、不宣称 G1-02；产品线 Frontier=票 08        |
| HANDOFF           | 根文件由测债会话改写为「Batch A–G + 票务指针」；产品细节以三件套为准      |
| 收尾提交          | **两次原子提交**：① 06/07+L5 产品实现；② 测债治理 Batch A–G（勿混成一粒） |

## 收尾提交现场（2026-07-12）

| 议题                | 备选                                       | 拍板                                                         |
| ------------------- | ------------------------------------------ | ------------------------------------------------------------ |
| GitNexus            | 带脏树提交 vs 先 analyze                   | **先** `node .gitnexus/run.cjs analyze` 再收尾               |
| mootdx dry-run 测绿 | 无 DB→`con=None` YAML 回落 vs 显式 prepare | **显式** `_prepare_mootdx_dry_run_route`（有 DB 才暴露假绿） |
| `.scratch` 票文件   | `git add -f` vs 本地保留                   | **不提交**（gitignore；以 task 三件套为准）                  |

---

_与 findings 分工：本文件 =「当时选了什么」；findings =「还有什么问题 / 已关什么问题」。_
