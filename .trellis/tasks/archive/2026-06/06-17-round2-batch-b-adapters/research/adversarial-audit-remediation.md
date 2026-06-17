# Batch B 对抗审计 Remediation 全表

> **复核日期：** 2026-06-17  
> **计划版本：** MASTER v1.1（post Composer 2.5 adversarial audit）  
> **原始报告：** 主会话派发 adversarial agent · verdict **BLOCK** → 主会话逐项复核 **26 项**  
> **原则：** 有效项 **全部** 写入 MASTER v1.1；无效/误报标注 dismiss。

---

## 复核结论

| 维度 | 结论 |
|------|------|
| **Verdict 修订** | BLOCK → **Plan 已解除**（MASTER v1.1 + 关联工件已修订） |
| **Batch A 债务** | F01/F02/F06/F07 已纳入 §3.2/§6/§8/§10 |
| **仍 defer** | GPT-P1-5-DB、GPT-P2-2、GPT-staging-DB、GPT-P3-6、A2-shrink |
| **并行不阻塞** | GPT-SEC-CI、GPT-init_db（显式 defer 至 Batch D 或并行 sprint） |

---

## Findings 处置表

| ID | P | 有效? | 处置 | MASTER 章节 |
|----|---|-------|------|-------------|
| F01 | P0 | ✅ | **偿还** FileRegistry 可选注入 + AC-9 + §8.1 测试 | §3.1,§6.2,§8.1 |
| F02 | P0 | ✅ | cninfo 未发布 → EMPTY_RESPONSE（不扩 8 态）+ §8.4 测试 + 更新 grill-me | §1.3,§8.4,§13 |
| F03 | P0 | ✅ | §8.1–8.5 补全 Skill/RED/GREEN/环境/证据列 | §8 |
| F04 | P0 | ✅ | §8.1 parametrized PortError 测试 | §8.1,research tests |
| F05 | P0 | ✅ | 补全 §8.4 测试正文 | research tests |
| F06 | P1 | ✅ | §0.1 post-Execute GitNexus + CodeGraph | §0.1,§8.6 |
| F07 | P1 | ✅ | §10 Tier B 增 ci_ingestion_smoke | §9,§10 |
| F08 | P1 | ✅ | §8.3 增 QMT SUCCESS 测试 | §8.3 |
| F09 | P1 | ✅ | §9/§10 证据列 + prod raw smoke | §9,§10 |
| F10 | P1 | ✅ | §6.2 贴 `_ERROR_TYPE_MAP` | §6.2 |
| F11 | P1 | ✅ | §6.3 `fetch_port=None` → vendor 默认 Stub | §6.3 |
| F12 | P1 | ✅ | §6.2 `super().__init__(registry)` 顺序 | §6.2 |
| F13 | P1 | ✅ | grill-me Q2/Q5 与 MASTER 对齐 | grill-me-session.md |
| F14 | P1 | ✅ | §9 smoke 写死 ci_ingestion_smoke | §9 |
| F15 | P2 | ✅ | §8.0 GREEN 须 ≥1 tracer collected | §8.0 |
| F16 | P2 | ✅ | §8.6 明确最终 GREEN + 回归清单 | §8.6 |
| F17 | P2 | ✅ | §11 增 detect_changes | §11 |
| F18 | P2 | ✅ | AC-2/§8.1 content_hash 断言 | §2,§8.1 |
| F19 | P2 | ✅ | §6.2 skeleton SUCCESS row_count=1 冻结 | §6.2 |
| F20 | P2 | ✅ | AUDIT A8 扩覆盖 | AUDIT §2 |
| F21 | P2 | ✅ | AUDIT A5 audit-sandbox raw 抽检 | AUDIT §2 |
| F22 | P2 | ✅ | AUDIT A1 DECISIONS §9 交叉 | AUDIT §2 |
| F23 | P2 | ✅ | prd AC 与 MASTER §2 同步 | prd.md |
| F24 | P3 | ✅ | §3.2 显式 defer GPT-init_db | §3.2 |
| F25 | P3 | ✅ | §3.2 显式 defer GPT-SEC-CI 并行 | §3.2 |
| F26 | P3 | ✅ | plan.freeze 更新 v1.1 对抗轮 | plan.freeze.md |

**Dismiss：** 无 — 26 项均有效或已显式 defer。

---

## Batch A 延后项 cross-check（post v1.1）

| ID | Batch B? | v1.1 状态 |
|----|----------|-----------|
| GPT-P1-5-DB | 否 | defer Batch C |
| GPT-P2-2 | 否 | defer Batch D |
| GPT-init_db | 可选 | **defer Batch D**（§3.2 显式） |
| GPT-P3-6 | 否 | defer Batch D（§3.2） |
| GPT-staging-DB | 否 | defer Batch C |
| GPT-NOT-PUBLISHED | **是** | **偿还** EMPTY_RESPONSE 语义（§8.4） |
| GPT-SEC-CI | 并行 | **defer** 非阻塞（§3.2） |
| Beta §6 FileRegistry | **是** | **偿还** §8.1 AC-9 |
| Beta §6 NOT_PUBLISHED 8态 | **是** | **部分偿还** 语义无 8 态扩展 |
| P3-7 GitNexus 再索引 | **是** | **偿还** §0.1/§8.6 |
