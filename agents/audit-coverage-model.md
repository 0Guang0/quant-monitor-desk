# Audit 覆盖模型 — 两条链 · 三类缺口（A1–A8 SSOT）

> **读者：Audit 各维 agent · A9 主会话**  
> **Execute 不 Read 本文件** — 缺口由 Audit 关账。

## 审计纪律（v4.1）

1. **先读上下文：** ENTRY + §5.1 全部 `research/*` + INDEX §3/§5 相关行 + EXTERNAL §A（与 Execute 同包，建立任务理解）。
2. **验证只信代码：** git diff · 独立跑测 · sandbox 复验 — **不相信任何文档自述**（含 ENTRY、slices、Execute `[x]`）。
3. **A1 / A5 分工不变**（见下表）；其他维按模板 + 本模型归类 findings。

## 两条权威链

```text
【链 A · 上游 → 任务包】
docs/modules · specs/contracts · ADR · 活任务卡 · GLOBAL_*
        │  下沉丢失？
        ▼
ENTRY · EXTERNAL §A · research/* · INDEX · frozen（指针）

【链 B · 任务包 → 实现】
to-issues-slices · INDEX §1/§2
        │  执行偏差？
        ▼
git diff · pytest · 运行时路径 · 独立复验
```

**链 A 缺口**：上游权威 **有**，Bundle **无或丢义** → §计划内 · **A1**  
**链 B 缺口**：Bundle **有**，实现/测试 **不符合** → §计划内 · **A5**  
**计划外**：上游 + Bundle **均未写**，对抗搜索发现 → §计划外 · **A3/A8** 等

---

## 三类缺口 ↔ findings 表

| 类型                  | 定义                                                           | findings 节 | 主责维         |
| --------------------- | -------------------------------------------------------------- | ----------- | -------------- |
| **计划内 · 下沉丢失** | 设计/契约/架构/活卡 **有**，ENTRY/research/slices **无或丢义** | §计划内问题 | **A1**         |
| **计划内 · 执行偏差** | slices/INDEX/ENTRY **有**，代码/测试 **不符合**                | §计划内问题 | **A5**         |
| **计划外**            | 上游 + Bundle **均未写**，对抗发现                             | §计划外发现 | **A3/A8** 牵头 |

禁止把「登记文件名对齐」 alone 当 PASS — 须 **读文档建上下文**，用 **代码+跑测** 裁决。

---

## A1 — 下沉丢失（链 A）

对照第一级权威 → Bundle 是否 faithful 下沉：

- [ ] 活卡 AC/Red Flags → slices 或 explicit defer
- [ ] 契约字段 → plan-spec / slices / ENTRY §2
- [ ] ADR/模块约束 → ENTRY §2 或 research
- [ ] EXTERNAL §A ↔ ENTRY §5.2 一致

### A5 — 执行偏差（链 B）

- [ ] 每条 slices AC → INDEX §1 步 → **代码/测试** 可验证（1–5 分）
- [ ] 独立复跑 INDEX §2.1 最弱 2 行
- [ ] diff 无 silent 扩大 scope

### A3 / A8 — 计划外

- [ ] 契约/活卡 **未写** 的信任边界是否仍有测试或 explicit check
- [ ] 不得因 Bundle 已列用例而省略对抗搜索

---

## Execute 分工（对比）

| Execute                                   | Audit                             |
| ----------------------------------------- | --------------------------------- |
| 读 ENTRY + research + 路由表；写代码/测试 | 读同包建上下文；**只信代码+跑测** |
| 可选对抗性自检并修缺口（不落盘表）        | A1–A8 落盘 findings               |
| 证据 = 代码 + pytest + `[x]`              | 不信文档自述                      |

---

## A9 / 主会话

- 7.pre.1：Trace Authority **Presence**（路径在不在）
- 合并 A1–A8 §计划内 + §计划外 → `audit.report.md` §4.1
