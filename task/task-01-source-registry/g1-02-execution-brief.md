# G1-02 执行 brief（防漂移 SSOT）

> **日期：** 2026-07-11  
> **状态：** 对抗式多 skill 审计后落盘；**开工前必读**（G1-02 切片细节 SSOT；层级见 [EXECUTION-DOC-INDEX.md](EXECUTION-DOC-INDEX.md)）  
> **前提：** G1-01 Plan r6 = `PLAN-READY`（`completion-check-plan-g1-01-r6.md`）≠ 实现完成  
> **权威链：** ADR-017 → **ADR-018** → `data_sources.md` §5.2.1 → 本 brief → 工作包 RED  
> **研究底稿（已归档）：** [归档/research-g1-02-enable-seam-sources.md](归档/research-g1-02-enable-seam-sources.md)  
> **决策：** [decision-map-enable-seam.md](decision-map-enable-seam.md) · 背景见 [归档/fred-builder-vs-adr017.md](归档/fred-builder-vs-adr017.md)  
> **与 task_plan：** L2 管模块范围；本文件管 G1-02 **细节**；冲突时 design > 本 brief > task_plan 旧措辞。

---

## 0. 禁止偏离（执行者口头「简化」即 FAIL）

| 禁令 | 来源 |
|------|------|
| 禁止长期兼容 `enabled_source_registry` / 强制 `_platform_allows` | ADR-018 方案 B 未选用 |
| 禁止把开关本与安检揉成一层函数（方案 A） | ADR-018 |
| 禁止只清 fred builder、漏清 backfill **else 全金路径** | r5/r6 CC-5 · E-CLI-20 |
| 禁止口头「没人用」漏处置 `source_route_matrix_bridge` | r5/r6 CC-3 · E-ACC-BRIDGE-01 |
| 禁止测试 monkeypatch / `__setattr__` 已加载对象冒充启用 | ADR-018 §2 · E-TEST-* |
| 禁止 `danger_skip_isolation` / staged_fixture / override_runtime 升格 product_default 或 R4 | inventory 档位图例 |
| 禁止未审阅改 `**/design/**` 贴合实现 | AGENTS.md |
| 禁止 FRED 启用撬门未清却宣称策略同路；合并不得无限搁置 | `T01-ENABLE-FRED-MERGE-001` |

---

## 1. 两层接口契约（api-and-interface-design + ADR-018）

### 1.1 第一层 — 问开关（activation overlay）

| 项 | 契约 |
|----|------|
| 输入 | **仅** `source_id` + `data_domain` + `operation` |
| 输出 | `is_allowed` · `reason_code`（机器可读）· `overlay_revision` |
| 持久化 | `source_activation_overlay`（`data_sources.md` §5.2.1 DDL）；读写记录操作者/时间/原因/版本/撤销 |
| 不做 | license / platform / capability / ResourceGuard（属第二层） |
| 演进 | One-Version；只许附加字段；不得静默改义拒绝语义（Hyrum） |
| 错误 | 全入口同一 `reason_code` 策略；具体开关本枚举若 design 未钉死 → **复用既有 route/ERROR_CODE 语义或开 design 审阅**；禁止自造静默同义码（见 research §7 UNVERIFIED） |

### 1.2 第二层 — 安检（RoutePlanner）

在开关本之后合成「有效启用」：基础 `is_enabled` + 最新未撤销 overlay + license/auth + platform + capability + ResourceGuard。  
CLI / 服务 / 调度 / 增量 **只读**合成结果；**不得**改 registry 内存或强制 `_platform_allows`。

### 1.3 与 §4A「整层策略查询」的关系

`task_plan.md` §4A 描述的是**整层** RoutePlan 决策（含 platform/capability）。G1-02 工作包 3 必须先交付 **1.1**，再让安检/RoutePlan 消费它。不得用 §4A 一口吞掉两层。

---

## 2. 退役顺序（deprecation-and-migration）

严格按 ADR-018 §4 / decision-map #4：

```text
1. 实现问开关读写 + migrate（隔离根可测）
2. 全部调用方改只问该接口（含 E-CLI-20 全金路径、matrix、各 enabled_*）
3. 先删 fred_incremental_watermark 内重复 enabled_fred_source_registry
4. rg 清零生产路径：enabled_source_registry | object.__setattr__(.*is_enabled | _platform_allows\s*=
```

**Strangler：** 沙箱正规 overlay 并行 → 产品路径切只读 → 删除 OVERRIDE（禁止永久双轨）。

**FRED：** G1-02 **立即**拆启用撬门；编排壳可暂留。合并四门槛 + 最迟 **G1-08** / 或新 ADR 废止 → `T01-ENABLE-FRED-MERGE-001`。

---

## 3. 入口处置清单（issue-triage · 必须逐 ID 关账）

> 权威：`g1-01-wiring-inventory.md` §3 + r6 闭环。每行 disposition ∈ {改问开关, 正规 overlay 测, 删除/并入, 降档知情, 阶段外置(有 ID)}。

### 3.1 必清 OVERRIDE（工作包 3→4a/4b）

| ID | 处置要点 |
|----|----------|
| **E-CLI-20** | `_gold_path_backfill_route_preview`：**fred 壳 + else ESR** 全清；反证「只清 fred 漏 else → FAIL」 |
| **E-CLI-13** | mootdx ESR |
| **E-INC-BUNDLE** | `load_incremental_route_bundle` + 强制 platform（共享根因） |
| **E-INC-FRED** … **E-INC-DER** | 九工厂 + FRED 双份 enable；编排≠启用 |
| **E-ACC-01** | matrix preview（含 baostock）走 bundle=OVERRIDE → 改正规 overlay |

### 3.2 暗门 / 隔离（知情 + 证据禁令）

| ID | 处置要点 |
|----|----------|
| **E-ACC-BRIDGE-01** | 零调用仍须：G1-02 后无生产引用则**删除**或并入 E-OPS-03 文档化链 |
| **E-ACC-ISO-01** | API 不保证隔离；不得单独当 gate_live 证明 |
| **E-ACC-SKIP-01** | `danger_skip_isolation` 永久禁升格 |
| **E-OPS-03a/03b** | skip 须先验 resolve；不得误标 danger 或升格 product_default |
| **E-REG-01～04** | sync 入口对齐；bootstrap 可写勿漏 |
| **E-SVC-01** | SSOT 同参基准 |
| **E-TEST-01～06** | 改写为「隔离根写 overlay → 正式入口」；禁 patch 已加载对象 |

### 3.3 同参探针（验收输入）

P-DAILY / P-MINUTE / P-MACRO / P-SUPP — 产品默认期望见 inventory §0；**禁止**用 OVERRIDE 绿灯冒充。

---

## 4. GitNexus 冲击面（开工前再跑一遍）

| Symbol | Upstream impact（2026-07-11 快照） | 风险 |
|--------|-------------------------------------|------|
| `enabled_source_registry` | direct≈13 · processes≈12 · **CRITICAL** | 共享根因；一次改接口须迁全部调用方 |
| `_gold_path_backfill_route_preview` | → `backfill_plan` · LOW 直接但业务关键 | E-CLI-20 全金路径 |
| `run_matrix_spine_for_source` | 近零外部生产调用 · LOW | 仍须按 E-ACC-BRIDGE-01 删除/并入 |

实现前对将改符号再跑 `impact(upstream)`；提交前 `detect_changes`。

---

## 5. 可观测性（工作包 3A · 与 3 同交付）

On-call 四问（已在 task_plan 3A）：策略版本谁允许/拒绝、拒绝类别、入口是否同参分裂、是否有人打废止绕过。

| 信号 | 最小要求 |
|------|----------|
| 结构化日志 | `source_policy_resolved` / `source_policy_denied`；含 correlation id、域、操作、结果、`reason_code`、**`overlay_revision`** |
| 指标 | 仅低基数枚举标签；禁止 request id / 任意 source 名做 label |
| 绕过侦测 | 生产路径仍调用 ESR / `__setattr__` / 强制 platform → invariant FAIL（发布阻断） |

无现成遥测管道时：先交付结构化日志 + 可重复测试；不擅自引入新依赖。

---

## 6. 工作包切割（相对旧 task_plan 的优化）

| 切片 | 内容 | 完成判据 |
|------|------|----------|
| **3A-接口** | 问开关 API + overlay 读写 + migrate（表形对齐 §5.2.1；改字段须用户审阅 design） | RED：三键输入/三字段输出；未允许不可被突变放行 |
| **3B-安检接线** | RoutePlanner/Service 只读合成；`overlay_revision` 可观察 | 同参 P-* 与 E-SVC-01 一致 |
| **3C-测试治理** | E-TEST-* → 隔离根 overlay；删 patch helper | 无 monkeypatch 生产对象关账证据 |
| **4a** | 迁 E-INC-* + BUNDLE + FRED 启用拆干净；按删除顺序 | rg 生产 ESR/platform 强制为零；合并四门槛**不**在本切片强行关（挂台账） |
| **4b** | 迁 E-CLI-20 **全金路径** + E-CLI-13；matrix/acceptance 正规 overlay | 反证：只清 fred 漏 else → 测试红 |
| **4x-bridge** | E-ACC-BRIDGE-01 删除或并入 E-OPS-03 | 文件消失或文档化调用链 + 清单更新 |

依赖：3A → 3B/3C → 4a∥4b → 4x；**禁止**未落地问开关就删调用方（会散装回 CLI）。

**执行追记（2026-07-11）：** 3B/3C 代码已接线；接线后全量 pytest 分诊见 `findings.md` T01-F05；B 类夹具债已清；A 类挂 4a/4b。现场裁定全文见 [`note.md`](note.md)。

---

## 7. G1-02 验证证据（扩展 gate1 三种同参）

1. 允许 / 未授权 / 能力缺失（原 gate1）— 正式入口，**非** OVERRIDE  
2. 隔离根写正规测试 overlay → 金路径可 READY；产品默认库同参仍 DISABLED（P-MACRO）  
3. E-CLI-20：fred 与非 fred 金路径均无 ESR；只清其一则失败  
4. 全库 rg 生产路径清零（§2 步 4）  
5. E-ACC-BRIDGE-01 已处置；E-ACC-SKIP 未出现在完成证据  
6. 档位标签诚实：`gate_live` / sandbox；禁升格  

pytest 绿 ≠ G1-02 CLOSED；须独立 Execute/Audit completion-check。

---

## 8. UNVERIFIED（不得假装已裁定）

见 research §7：开关本 reason_code 完整枚举、Python 符号名、revision 生成算法、管理员 CLI 子命令字、沙箱标记专用列 vs reason 约定、FRED 水位线最终字段名。  
**做法：** 能复用 ERROR_CODE_GUIDE / 既有 route status 则复用；否则 grill-me / design 审阅后再写码。

---

## 9. 每切片最小上下文包

1. 本 brief + ADR-018 + `data_sources.md` §5.2.1  
2. `g1-01-wiring-inventory.md` 相关 ID 行  
3. 将改源文件 + GitNexus impact  
4. `findings.md` 关联条 + 上一轮命令输出  

*本 brief 不构成实现关账。*
