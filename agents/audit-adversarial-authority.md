# 对抗性审计权威层级（A1–A8 全员）

> **派发纪律：** 一维一 agent；全文 Read 本文件 + 本维 `agents/*.md` 模板。

## 权威来源（按优先级）

### 第一级（同级 · 最高）

- **设计文档**（`docs/modules/**`、`research/source-index.md`、模块设计 §）
- **规则 / 契约**（`specs/contracts/**`、`specs/**`、registry SSOT）

### 第二级（同级）

- **本维 agent 模板**（`agents/audit-a*.md`、`security-auditor.md`、`code-reviewer.md`、`qa-expert.md`、`performance-engineer.md` 等）
- **原始任务卡**（`docs/implementation_tasks/**/NNN_*.md`）

### 第三级

- **`audit.jsonl` / `AUDIT.plan.md` Trace Authority**（索引与验证矩阵，非 scope 上限）

## 仅作参考（不得当作审计完备性上限）

- **`MASTER.plan.md` §5 / §8**（执行计划、测试矩阵、切片表）
- **Execute `implement.jsonl`**（manifest 点名，非行为全集）
- **首轮 `audit.report.md`**（可被本轮推翻）

**假设：** 执行计划本身可能存在缺口、漏洞、未列边界。审计须 **对抗性** 追问：「若只按计划测，什么仍会漏到生产？」

## 各维最低对抗动作

| 维  | 除模板 checklist 外，必须额外对照                                                                                                                                          |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1  | 设计文档边界 + 契约 scope vs diff；任务卡 Red Flags；计划未索引的 defer/越界                                                                                               |
| A2  | 设计文档既定模式 vs 实现；计划外重复、可删路径、未请求抽象                                                                                                                 |
| A3  | 契约信任边界 + 任务卡安全约束；计划未写的 mutation/bypass/密钥/旁路                                                                                                        |
| A4  | 设计文档语义 + 契约字段一致性；计划未写的错误模型、脆弱断言                                                                                                                |
| A5  | 任务卡 AC + 设计文档行为；**计划外** runtime 路径与证据真实性                                                                                                              |
| A6  | 设计/任务卡性能与资源约束；MASTER §10 或 AUDIT.plan 冻结阈值；计划未写的 hot path、无界 I/O、批大小/内存尖峰（Plan 标 SKIP 时仍须写 SKIP 理由 + 是否存在计划外 perf 风险） |
| A7  | 设计文档数据路径 + schema 契约；计划未写的 DB/migration/数据污染面                                                                                                         |
| A8  | 契约 `validation_tests` + 任务卡 Red Flags；**计划外**边界与弱断言                                                                                                         |

## 产出要求

- 每个 `research/phase7-reaudit/a*.md`（或维度证据）须含 **`## 计划外发现`** 表（可为空但须显式声明已对抗搜索）。
- 发现项标 **BLOCKING / NON-BLOCKING**；不得因 MASTER 已列用例而降级为「已覆盖」。
