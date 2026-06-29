# Audit 阶段 — 维度 / Agent / Skill 候选词典

> **默认验证矩阵（§2）** — Plan 未在 `AUDIT.plan.md` §1 覆写时，Audit 按本文件 §2 执行。  
> **维度 skill / 派发 / 必读** — 见 `audit-skill-paths.yaml` + `agents/` 下模板（Plan 不手填 §1）。  
> **Audit agent 不读本文**（Plan 填 AUDIT 时查阅）。

---

## 1. 标准维度 — Skill 冻结

| ID  | 名称     | Agent            | 执行者     | Skill                                                      |
| --- | -------- | ---------------- | ---------- | ---------------------------------------------------------- |
| A1  | Spec     | audit-spec       | 子 agent   | trellis-check + doubt-driven-development                   |
| A2  | 过度工程 | audit-ponytail   | 子 agent   | ponytail-review + doubt-driven-development                 |
| A3  | 安全     | audit-security   | 子 agent   | security-and-hardening + doubt-driven-development          |
| A4  | 代码质量 | audit-quality    | 子 agent   | code-review-and-quality + doubt-driven-development         |
| A5  | 完成情况 | audit-completion | 子 agent   | verification-before-completion + doubt-driven-development  |
| A6  | 性能     | audit-perf       | 子 agent   | 项目脚本 / systematic-debugging + doubt-driven-development |
| A7  | 运维     | audit-ops        | 子 agent   | doubt-driven-development                                   |
| A8  | 测试缺口 | audit-test-gap   | 子 agent   | testing-guidelines + doubt-driven-development              |
| A9  | 风险汇总 | —                | **主会话** | —                                                          |

---

## 2. 维度验证默认模板（Plan 写入 AUDIT.plan §2）

> **与 INDEX §2.1 无关。** Execute 验收冻在 `EXECUTION_INDEX.md` §1/§2/§2.1；Audit 验证冻在 AUDIT §1。  
> **Boot SSOT：** `agents/audit-boot-v4.1.md`
> 验证类型：`static` | `read-only` | `review-only` | `trace-ac` | `pytest-isolated` | `cli-sandbox`

| 维     | 验证焦点                                                                                                                                                             | 验证类型        | 典型命令 / 检查                                                                   | 环境          | 隔离                     | 通过条件（摘要）                                   | 对抗性触发器（Plan 冻结）                                                                              |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | --------------------------------------------------------------------------------- | ------------- | ------------------------ | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **A1** | Spec / original-source compliance：检查 ENTRY/INDEX/AUDIT 是否完整继承原始任务卡、项目地图、轮次地图、任务输入索引、unresolved coverage；检查未声明依赖与 scope 偏离 | read-only       | trellis-check；diff vs check.jsonl；Trace Authority Set 倒查；GitNexus 未声明依赖 | local         | 无写                     | findings 表为空；checklist 满足                    | **必须**对照 Trace Authority Set 验证原始 scope 已进入 ENTRY/INDEX/AUDIT 或 explicit filtered/deferred |
| **A2** | 过度工程                                                                                                                                                             | review-only     | ponytail-review；Lxx + net lines                                                  | —             | —                        | findings 表为空；checklist 满足                    | **必须**找到 ≥1 处 ≥20 行可简化/删除的代码？找不到则说明为什么                                         |
| **A3** | 安全                                                                                                                                                                 | static          | 威胁面；密钥/URL grep；注入点                                                     | local         | 无写                     | findings 表为空；checklist 满足                    | **必须**检查 3 类隐蔽威胁（硬编码 URL 变体、JWT/API key 模式、SQL 拼接），无发现则说明为什么           |
| **A4** | 代码质量                                                                                                                                                             | review-only     | code-review-and-quality 多轴                                                      | —             | —                        | findings 表为空；checklist 满足                    | **必须**找到 ≥1 处错误处理缺失或边界遗漏？找不到则说明为什么                                           |
| **A5** | AC source-chain completion：从原始任务、registry、Round map、unresolved coverage 追溯到 ENTRY/INDEX AC、Execute §1、evidence、registry closeout                      | trace-ac        | 逐条 ENTRY/INDEX AC ↔ 验证链；1–5 分                                              | local         | 无写                     | findings 表为空；AC 追溯 ≥4                        | **必须**从原始 source-chain 验证 evidence，不得只检查文件存在                                          |
| **A5** | **证据抽检（必做，非条件）**                                                                                                                                         | cli-sandbox     | 选 Execute INDEX §2.1 B/C 证据最弱的 **2 行**，于 audit-sandbox 独立复跑          | audit-sandbox | 独立 DATA_ROOT           | 与 Execute 声称一致；不一致 → §4.3                 | 复跑结果与 Execute 证据是否一致？                                                                      |
| **A5** | **独立复验（必做）**                                                                                                                                                 | read-only       | INDEX §2.1 最弱 2 行独立跑测 + git diff 对照 AC；v4 遗留可对照 green.txt          | local         | 无写                     | 代码/测试与 AC 一致；不一致 → finding              | 不信文档自述—独立跑测与 diff 是否支撑 AC？                                                             |
| **A6** | 性能/资源                                                                                                                                                            | cli-sandbox     | profiling / 资源脚本                                                              | audit-sandbox | `.audit-sandbox/`        | 指标 ≤ 阈值                                        | 真实数据量级下指标还成立吗？sandbox 数据量是否与生产一致？                                             |
| **A7** | 运维/幂等/日志                                                                                                                                                       | cli-sandbox     | init/migrate walkthrough + **必做 1 异常场景**（kill 进程后重跑、磁盘满等）       | audit-sandbox | 独立 DATA_ROOT           | 幂等；失败可观测                                   | 第二次跑不只是"不报错"，数据是否完整未被破坏？                                                         |
| **A8** | Original Red Flags test-gap：从原始任务和 unresolved coverage 中提取边界，验证测试是否覆盖，而不是只看 ENTRY/plan-doubt-review                                       | pytest-isolated | 补 Red Flags / 边界用例；**可追加 2 个自选边界用例**                              | audit-sandbox | tmp DB / `@audit` marker | findings 表为空；Red Flags 已覆盖或 explicit check | 原始 Red Flags 须有测试或 explicit audit check                                                         |

> **Findings 表 SSOT：** `agents/audit-finding-schema.md`。任一行非占位 → 该维 `audit_matrix.json` **fail**。

### 2.1 谁需要 prod-path-like（audit-sandbox / audit-prod-path）

| 角色                          | audit-sandbox    | audit-prod-path | Execute prod-path       | 真实生产 |
| ----------------------------- | ---------------- | --------------- | ----------------------- | -------- |
| Execute INDEX §2.1 Tier B/C   | 否               | 否              | **必须**                | 否       |
| A1–A4                         | 否               | 否              | 否                      | 否       |
| A5 追溯                       | 否               | 否              | 否（读证据）            | 否       |
| A5 抽检（必做）               | **必须**         | 否              | 否                      | 否       |
| A5 证据文件真实性（必做）     | 否（读证据文件） | 否              | 否                      | 否       |
| A5 完整复验（必做）           | 否               | **必须**        | 否                      | 否       |
| A6、A7、A8（A6 **未跳过**时） | **必须**         | **必须**        | 否                      | 否       |
| A6 **Plan 跳过**              | 否               | 否              | 否                      | 否       |
| Repair 收尾                   | 否               | 否              | **复跑 INDEX §2.1 B/C** | 否       |

**audit-prod-path 操作规范（写入 AUDIT §2）：**

1. `cp -r $DATA_ROOT $AUDIT_PROD_ROOT`（复制真实数据到审计专用副本）
2. **验证：** `AUDIT_PROD_ROOT=$AUDIT_PROD_ROOT python -c "from app.config import Config; assert Config.DATA_ROOT == '$AUDIT_PROD_ROOT'"` 确认应用程序读取了该环境变量
3. 对副本跑 INDEX §2.1 全套 + Tier B/C
4. 使用 `AUDIT_PROD_ROOT` 环境变量指向审计副本，其余配置与生产一致
5. 审计完成后 `rm -rf $AUDIT_PROD_ROOT`（清理）
6. **禁止**修改 Execute 验收库或真实生产数据

### 2.2 Plan 填 §2：`{{}}` 与 A6 跳过

- **`{{}}` 占位符**：Plan 须换成可执行命令/路径；留空 = 未冻结。说明见 [AUDIT 模板 §2.1](./templates/AUDIT.plan.md)。
- **A6 无性能要求**：§1 标「不用」；§2 写 SKIP 行 + 一句理由；Audit 在 §3.6 注 SKIP。说明见 [AUDIT 模板 §2.2](./templates/AUDIT.plan.md)。

---

## 3. GitNexus / CodeGraph

| 时机             | 产出                                                                                   |
| ---------------- | -------------------------------------------------------------------------------------- |
| 7.pre（Audit）   | `gitnexus-audit-summary.md`                                                            |
| 7.pre.1（Audit） | Trace Authority Presence Check（manifest 入口；不派发 A1–A8 前）                       |
| A1–A8            | 读 audit 摘要 + Trace Authority 相关 `audit.jsonl` 条目 + ≥1 query → audit.report §3.x |

> v4.1 Execute **不强制** `gitnexus-execute-summary.md`；legacy v4 任务可保留。

---

## 4. 双契约速查

| 契约           | 文件                            | 执行者  |
| -------------- | ------------------------------- | ------- |
| Execute 验收   | `EXECUTION_INDEX.md` §1/§2/§2.1 | Execute |
| Audit 维度验证 | AUDIT §1 + Boot v4.1            | A1–A8   |
| Repair 回归    | INDEX §2.1 + `uv run pytest -q` | Repair  |

---

## 5. A9 / Repair / Finish

- A9 主会话：合并 A1–A8 `research/audit-a{n}-report.md` §计划内 + §计划外 → `audit.report.md` §4.1 / `research/audit-repair-ledger.md`
- **PASS** — 全维 pass/skip 且 findings 合并表仅占位 → Phase 9
- **FAIL** — 任维 fail 或 findings 非空 → REPAIR.plan → Phase 8（**禁止** PASS_WITH_FIXES）
- Repair 关账：`project-global.mdc` §无遗留 + `uv run pytest -q` 全绿
