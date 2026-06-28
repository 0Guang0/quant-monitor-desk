# Plan 冻结记录 — R3H-04 Prediction and Web Evidence Adapters

> **读者：Plan agent** · Execute / Audit **不读**

---

## 1. Plan 阶段 Skill 执行记录

| Phase  | Skill                       | 产出                              | 已完成 |
| ------ | --------------------------- | --------------------------------- | ------ |
| boot   | trellis-plan                | `research/plan-boot.md`           | [x]    |
| 1a     | gitnexus-plan-1a            | `research/project-overview.md`    | [x]    |
| 2a     | trellis-brainstorm           | `research/brainstorm-session.md` | [x]    |
| 2b     | spec-driven-development   | `research/spec-driven-development-notes.md` | [x]    |
| 3      | grill-me                    | `research/grill-me-session.md`    | [x]    |
| 3.5    | to-issues                   | `research/to-issues-slices.md`    | [x]    |
| 1b     | gitnexus-plan-1b            | `research/gitnexus-summary.md`    | [x]    |
| 5a     | planning-and-task-breakdown | INDEX §1 / 活卡 §9                | [x]    |
| 5b     | writing-plans               | INDEX §1 RED/GREEN + §2           | [x]    |
| 5c     | trellis-before-dev          | `research/integration-ledger.md`  | [x]    |
| 5d     | doubt-driven-development    | `research/integration-audit.md`   | [x]    |
| 5e     | trellis-plan                | `research/plan-consolidation.md`  | [x]    |

---

## 2. Plan 贡献溯源 & 5d 结论

- **对抗审计 PASS**：mock-first READY 可执行；web_search 真实 API 为唯一用户未决（不阻塞 mock 路径）。
- **BRANCH 优先**：不改 `resource_guard.py`、不碰 R3H-03 文件。

### 2.1 未决问题清单

| # | 问题 | 须 Grill-me？ | 默认（无用户回复） |
| --- | --- | --- | --- |
| 1 | `web_search` 是否需要真实搜索引擎 API（Bing/Google/自建）而非 mock stub？ | **是** | mock stub READY |
| 2 | kalshi/polymarket 是否要求本迭代 live API smoke（非 replay）？ | **是** | mock/replay only |
| 3 | polymarket `resolution_source` 字段是否允许存 URL 占位（非事实判定）？ | 否（Plan 已决） | 允许 URL 元数据；禁止 `resolved=true` |

---

## 3. 冻结自检

### 3.0v4 冻结三件套

| ✓   | Execute 验收（冻结卡 + 索引）                         | ✓   | Audit（AUDIT + 索引 §5）             |
| --- | ----------------------------------------------------- | --- | ------------------------------------ |
| [x] | `frozen/*.md` 含 §8 停止条件 + §9 步骤 + §10 测试契约 | [x] | `AUDIT.plan.md` §2 无 `{{}}` 占位符  |
| [x] | `EXECUTION_INDEX.md` §1 RED/GREEN + §2 验收 Tier      | [x] | 索引 §5 Audit 追溯集已填             |
| [x] | §3 仅列 **不可无损内联** 的原文路径                   | [x] | `audit.jsonl` 第一条 = AUDIT.plan.md |
| [x] | §4 已内联来源与冻结卡章节对照                         | [x] | A6：SKIP + 理由                       |
| [x] | `task.py freeze-task-card` 已执行                     | [x] | 7.pre → Audit 阶段（Plan 不产出） |
| [x] | `implement.jsonl` 第一条 = frozen 卡（自动生成）      | [x] | A1/A5/A8 倒查 frozen + 索引 §3       |

### 3.0e Plan consolidation（Phase 5e）

| ✓   | 检查项                                    |
| --- | ----------------------------------------- |
| [x] | `research/plan-consolidation.md` + **Phase 5e complete** |
| [x] | 各 research 草稿有 merged/pointer/n/a     |
| [x] | 可执行结论已写入活任务卡 §7–§15           |
| [x] | INDEX §4 已填                             |
| [x] | `prd.md` thin-index                       |
| [x] | `validate-plan-freeze` exit 0 |

### 3.0f 三件套完备性（Triad gate）

| ✓   | 检查项 |
| --- | --- |
| [x] | 决策草稿均 merged；integration-audit → frozen §14 pointer |
| [x] | OpenBB 参考路径已内联 frozen §14（仓库无 clone，不列 §3） |
| [x] | INDEX §4/§6 写明 Execute 不读 research/* |
| [x] | implement.jsonl 无 research/* 路径 |

### 3.0a Plan Phase 产出门禁

| ✓   | 检查项 |
| --- | --- |
| [x] | `research/project-overview.md` |
| [x] | `research/grill-me-session.md` |
| [x] | to-issues ≥2 切片（S0–S8） |
| [x] | `research/gitnexus-summary.md` |
| [x] | Phase 4 跳过理由：§9 已足够 |
| [x] | Phase 5d integration-audit PASS |

### 3.0b 原计划包门禁（v4）

| ✓   | 检查项 |
| --- | --- |
| [x] | 已读 `docs/implementation_tasks/README.md` + `GLOBAL_*.md`（4 个） |
| [x] | 已读 Batch 3H `README.md` + 活卡 §2 输入 |
| [x] | 已读 `R3H_04_*.md` 及 specs/contracts 输入 |
| [x] | `research/original-plan-trace.md` 已产出 |
| [x] | `EXECUTION_INDEX.md` §0 + §3 manifest 已填 |
| [x] | `implement.jsonl` 由 generate-manifests 生成 |

### 3.6 validate-plan-freeze

```text
Plan freeze validation passed (2026-06-28 P2 Plan-Audit)
validate-plan-phase 5e: passed
validate-plan-freeze: exit 0
research/plan-adversarial-audit.md: 9 findings / 9 fixed / 0 open
```

## 4. 用户批准

Plan 冻结候选完成 — **Execute `task.py start` 须用户显式批准**（分支 `feature/round3h-r3h04-prediction-web`）。

## 5. 修订记录

| 版本 | 日期       | 变更           |
| ---- | ---------- | -------------- |
| v0.1 | 2026-06-28 | P1 Plan 初稿   |
| v0.2 | 2026-06-28 | P2 Plan-Audit 对抗修复（9/9） |
