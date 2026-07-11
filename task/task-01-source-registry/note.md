# task-01-source-registry · 执行决策记录（note）

> **本文件记什么：** 执行阶段、计划未写死时的**临时拍板 / 方案取舍**（选了 A 不选 B、怎么接、做到哪停）。  
> **不记什么：** 问题现象、开放债、已修复证据 → 一律进 [`findings.md`](findings.md)；动作时间线 → [`progress.md`](progress.md)。  
> **不替代：** ADR / `task_plan` / `g1-02-execution-brief`。  
> **更新规则：** 计划未穷尽处**当场写入**；按票追加，不删历史。

---

## 票 03（3A）

| 议题 | 备选 | 拍板 |
|------|------|------|
| 平台放行 | 强制 `_platform_allows` vs 构造输入 | **自定义 `platform_matrix_path` YAML fixture**（构造输入，不 patch 规划器） |
| overlay 与 fetch 不同库 | service 不传 con vs overlay 写入 fetch DB | **`enable_source_route(..., con=)` 写到 fetch 同一 DB**；此时 planner `activation_con=None`（避免被 `fetch(con=)` 覆盖） |
| 默认可关源再测安检 | 直接断言 vs 先开 | **先 overlay 打开，再断言** license/env 等安检结果 |

---

## 票 04（3B）

| 议题 | 计划未定处 | 拍板 |
|------|------------|------|
| 无 DB 时怎么问开关 | brief 只写「只读合成」 | **有 `con` → `ask_activation`；无 `con` → 回落 YAML 内存 `is_enabled`**（`ponytail` 过渡；产品 fetch 必须传 con） |
| 安检链顺序 | ADR 原则未钉死代码顺序 | **activation → capability → platform/license**（后果：默认关源常先出 `source_disabled_by_default`，见 findings F05-A7） |
| `overlay_revision` 算法 | brief UNVERIFIED | **透传 `ask_activation` 返回值**；无 overlay 用 `""`；只附加字段不改义 |
| 3-OBS | 允许结构化日志，未定管道 | **stderr JSON**（对齐 `write_telemetry`）；事件 `source_policy_resolved` / `source_policy_denied`；`QMD_SOURCE_POLICY_TELEMETRY` 可关 |
| Service 改多少 | fetch CRITICAL | **只透传 `con` 给 `plan`**，不改状态机 |
| 本票是否清生产 ESR | 范围边界 | **不删**；留给 4a / 票 06·07 |

落点：`route_planner.py` · `route_models.py` · `service.py` · `event_payload.py`

---

## 票 05（3C）

| 议题 | 计划未定处 | 拍板 |
|------|------------|------|
| 「删 patch」落到哪 | helper 粒度 | **`enable_source_route` = overlay + sync_to_db`**；关账证据禁用 `__setattr__` / 强制 `_platform_allows` |
| 域默认关怎么测 | 改生产 YAML？ | **只改测试 registry 副本**（`domain_enabled_by_default` + capability op） |
| 本票是否清生产 ESR | 与 4a 边界 | **否**（05=夹具；清零属 4a/4b） |

落点：`tests/service_path_support.py` · `test_etest_overlay_governance.py`

---

## 接线后回归怎么处置（用户确认后拍板）

| 议题 | 备选 | 拍板 |
|------|------|------|
| 全量红怎么动 | 一律修生产 / 一律改测 / 先分再动 | **先分诊再修**（问题台账在 findings F05；此处只记分诊规则） |
| 分诊规则 | — | **A** = 旧口径（ESR/`__setattr__` 或旧 skip 顺序）→ 清期望或迁 overlay，**挂 4a/4b**；**B** = YAML 本可启用但空库未 sync → **本切片修夹具** |
| 「清理」A 类测 | 删文件 vs 改夹具/断言 | **不删测文件**；清旧期望/旧撬门 |
| B 修哪里 | 改 `sync_to_db` / 改 ask / 改夹具 | **只加测试 helper `seed_activation_base`**（调用既有 `sync_to_db`，不改 HIGH 符号） |
| 编排器模块 DB | 模块级 sync 一次 vs 每测 sync | **每测 sync**（因 `truncate_mutable_tables` 清空含 `source_registry`） |
| 本切片修到哪 | B+A / 只 B | **先只修 B**（用户选定）；关账前又闭环 **A7** 断言（对齐 ADR-018 先开关） |
| A7 断言（关账前） | 挂起 vs 本阶段改 | **本阶段改**：默认先 `source_disabled`；overlay 后再 `missing_env` |

问题开闭与证据：**只写在 findings**（F05-A **node-id 全表**开放挂 06/07 / F05-B·A7 已关），此处不重复 ledger。双登记：`docs/quality/待修复清单.md` + 仓库根 `PROJECT_IMPLEMENTATION_ROADMAP.md`。

---

## 04/05 质量复核拍板（2026-07-11）

| 议题 | 拍板 |
|------|------|
| `_emit_source_policy_event` 字段 allowlist frozenset | **删掉**；自建 payload + 滤掉 `None`（行为不变） |
| `bootstrap_vendor_e2e_db` 重复 sync | **复用** `seed_activation_base` |
| etest 重复 assert `write_activation_overlay` | **删一行** |
| 测试 import 私有 `_platform_key` | **不做**（避免测试耦合私有符号） |
| `enable_source_route` 内存改副本 | **暂留** → findings **T01-F06** → 票 06 |
| 无 con 内存回落 | **暂留** → findings **T01-F07** → 票 06+07 后删 |
| 阶段性代码混放正式路径 | **未发现**需迁 `phase-scripts` 的 04/05 产物（实现在 `backend/`，测在 `tests/`） |

---

## 刻意未做（范围拍板，非问题列表）

- 不为保绿恢复 ESR / `__setattr__` / 强制 platform  
- 不改 `**/design/**`、不 promote  
- 本切片不做 4a/4b 全量迁 overlay  
- 不以全量 pytest 绿宣称 04/05 或 G1-02 关账  

---

*与 findings 分工：本文件 =「当时选了什么」；findings =「还有什么问题 / 已关什么问题」。*
