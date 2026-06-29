# 对抗性审计权威层级（A1–A8 全员）

> **派发纪律：** 一维一 agent；全文 Read **`agents/audit-boot-v4.1.md`** + 本文件 + 本维 `agents/*.md` 模板。

## 权威来源（按优先级）

### 第一级（同级 · 最高）

- **设计文档**（`docs/modules/**`、`research/EXTERNAL-INDEX.md` §B/C、模块设计 §）
- **规则 / 契约**（`specs/contracts/**`、`specs/**`、registry SSOT）

### 第二级（同级）

- **Plan v4.1 Execution Bundle**（`research/00-EXECUTION-ENTRY.md` + ENTRY §5.1 登记 `research/*` + `research/to-issues-slices.md`）
- **本维 agent 模板**（`agents/audit-a*.md`、`security-auditor.md`、`code-reviewer.md`、`qa-expert.md`、`performance-engineer.md` 等）
- **原始任务卡**（`docs/implementation_tasks/**/NNN_*.md`；经 EXTERNAL-INDEX §A 路由）

### 第三级

- **`frozen/*.md`**（v4.1 薄指针 + 审计锚点）
- **`EXECUTION_INDEX.md`**（§1 步骤/证据 · §2 AC · §3 manifest · §5 Audit 追溯）
- **`audit.jsonl` / `AUDIT.plan.md` Trace Authority**（索引与验证矩阵，非 scope 上限）

## 仅作参考（不得当作审计完备性上限）

- **Execute `implement.jsonl` manifest 点名**（非行为全集）
- **首轮 `audit.report.md`**（可被本轮推翻）
- **`tasks/archive/` 内 v3 `MASTER.plan.md`**（历史只读；活跃任务不存在）

**假设：** Execution Bundle 本身可能存在缺口。**先读 Bundle 建上下文**；**验证只信代码 + 跑测 + 独立复验**，不信任何文档自述。

## 各维最低对抗动作

| 维  | 除模板 checklist 外，必须额外对照                                                                                            |
| --- | ---------------------------------------------------------------------------------------------------------------------------- |
| A1  | ENTRY §2 约束 + 契约 scope vs diff；活卡 Red Flags；Trace Authority / omission / integration-audit 闭环                      |
| A2  | ENTRY + to-issues 既定模式 vs 实现；计划外重复、可删路径、未请求抽象                                                         |
| A3  | 契约信任边界 + 活卡安全约束；计划未写的 mutation/bypass/密钥/旁路                                                            |
| A4  | ENTRY/spec-gap 语义 + 契约字段；计划未写的错误模型、脆弱断言                                                                 |
| A5  | 活卡 AC + ENTRY §1；**计划外** runtime 路径；**代码/测试** 独立复验（v4.1 不信 green.txt）                                   |
| A6  | ENTRY §2 性能/资源 + AUDIT.plan §1 冻结阈值；计划未写的 hot path、无界 I/O（Plan 标 SKIP 仍须 SKIP 理由 + 计划外 perf 扫描） |
| A7  | 活卡数据路径 + schema 契约；计划未写的 DB/migration/数据污染面                                                               |
| A8  | `plan-doubt-review` / Red Flags + `to-issues-slices` 建议测试；**计划外**边界与弱断言                                        |

## 产出要求

Read **`agents/audit-finding-schema.md`** 全文并满足其 **关账完成条件**。

- 落盘 `research/audit-a{n}-report.md`
- 含 **§维度裁决**、**§计划内问题**、**§计划外发现**
- **任一行 finding 非占位 → 维度裁决 = FAIL**
- 不得因 INDEX/ENTRY 已列用例而降级为「已覆盖」或省略计划外表
