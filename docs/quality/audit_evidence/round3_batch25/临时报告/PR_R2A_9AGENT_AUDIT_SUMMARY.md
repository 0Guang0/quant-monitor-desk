# 9-Agent 对抗性审计总报告 — PR-R2a (`ingestion_evidence` extract)

**审计日期:** 2026-06-21  
**对象:** PR #25 `feat/ingestion-pr-r2a-evidence-extract` → `master`（**未合并**）  
**执行卡:** `docs/architecture/layer1_ingestion_refactor_rollback_plan.md` PR-R2a  
**协议:** Trellis Phase 7（7.pre + A1–A9 主会话汇总）

---

## 0. 状态确认

| 项          | 值                                                                      |
| ----------- | ----------------------------------------------------------------------- |
| PR          | https://github.com/0Guang0/quant-monitor-desk/pull/25                   |
| 合并状态    | **未合并**                                                              |
| 基线 commit | `126dd97` + 审计后修补 commit（registry / `_relative_path` / 门禁测试） |
| Batch 2.75  | **未执行**（与 R2a 互斥，正确）                                         |

---

## 1. 九维评分

| Agent | 维度                 |                     分数 | 结论                              |
| ----- | -------------------- | -----------------------: | --------------------------------- |
| 01    | 完成情况 & readiness |                       94 | MERGE-READY（修补后）             |
| 02    | 设计偏差             |                       88 | CONDITIONAL PASS                  |
| 03    | Ponytail / 简化      |                       88 | FAIL（95+ 栏；R2a 步骤 PASS）     |
| 04    | 代码质量             |                       86 | APPROVE                           |
| 05    | 可维护性 & 测试      |                       87 | APPROVE                           |
| 06    | 工程规范 & 架构      |                82→**90** | CONDITIONAL PASS（registry 已补） |
| 07    | 解耦 & 嵌套          |                       87 | R2a scope PASS                    |
| 08    | 性能                 |                       91 | PASS                              |
| 09    | 数据库深挖           | 87→**96**（pytest 绿后） | PASS                              |

**整体（PR-R2a 范围）:** **PASS — 可合并**（非 Batch 2.75 / 非 95+ 全项目 hygiene）

---

## 2. 全局发现台账（无遗漏）

### P0 — 阻塞

| ID  | 问题 | 状态 |
| --- | ---- | ---- |
| —   | 无   | —    |

### P1 — 高

| ID                   | 问题                                                               | 阻塞合并?  | 处置                                                       |
| -------------------- | ------------------------------------------------------------------ | ---------- | ---------------------------------------------------------- |
| A9-EXEC-P1-01        | 子 agent 环境未跑 pytest                                           | 是（审计） | **主会话已跑** I1–I7 + 全量 pytest                         |
| F-01 / A05-P1-01     | I5 JSON 键集无自动化守卫；golden `fetch_log_delta_note` 为归档注释 | 否         | **接受**：行为键由 phase3 测试断言；归档 JSON 不追加入代码 |
| F-02 / A07-R2a-P1-01 | `ingestion` ↔ `ingestion_evidence` 循环 import                     | 否         | **DEFERRED → R2b**（`ingestion_types.py`）                 |
| A03-P1-01-R2a        | `commit_clean_*` 333 行 monolith                                   | 否         | **DEFERRED → R2c**                                         |

### P2 — 中（本 PR 已闭合 vs 延期）

| ID                        | 问题                                      | 处置                                                                            |
| ------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------- |
| R2A-GAP-01 / A06-P1-01    | §3.3 registry 未标 R2a DONE               | **DONE** — `ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`                             |
| R2A-GAP-02                | `AUDIT_DEFERRED` 未同步                   | **N/A** — A03-P2-01 未入 deferred 表                                            |
| R2A-GAP-03 / A06-P1-02    | HYG-01 Problem 列陈旧                     | **DONE** — `UNRESOLVED_ISSUES_REGISTRY.md`                                      |
| A04-P2-01 / A07-R2a-P2-02 | `_relative_path` 私有跨模块 import        | **DONE** — 改 `ingestion_inventory._relative_to_project`                        |
| A04-P2-04                 | `ingestion_evidence` 无 `__all__`         | **DONE**                                                                        |
| A04-P3-01                 | phase4 `evidence_data_root` 死代码        | **DONE** — 删除未使用赋值                                                       |
| A05-R2a-P2-03             | 无 facade 对照测试                        | **DONE** — `test_layer1Ingestion_phase0_ingestionFacadeReexportsEvidenceModule` |
| A09-R2a-P3-02             | 无 mutation tables 归属测试               | **DONE** — `test_layer1Ingestion_phase0_evidenceModuleExportsPublicSurface`     |
| R2A-GAP-07 / A06-P2-04    | rollback plan 仍 PLANNING ONLY            | **DONE** — 状态头更新                                                           |
| A07-R2a-P2-01             | `service._db_path/_row_counts/_allowlist` | **DEFERRED → R2b**                                                              |
| A07-R2b-DEFER-01          | sandbox bootstrap 三重复                  | **DEFERRED → R2b**                                                              |
| A03-P2-02-R2a             | formatter 部分重复                        | **PARTIAL** — `_format_count_table_md` 已提取；矩阵 MD 留 R2b                   |
| A08-P1-02                 | CI 无 quick tier                          | **DEFERRED** — Round 3 CI hygiene                                               |
| A9-P2-01                  | migration 008 CHECK                       | **DEFERRED** — B2.5-O-06                                                        |
| A9-P2-02                  | 生产 DB checksum                          | **DEFERRED** — Batch 2.75                                                       |

### P3 — 低

| ID            | 问题                              | 处置                                                 |
| ------------- | --------------------------------- | ---------------------------------------------------- |
| R2A-GAP-08    | ruff format 未证据化              | **DONE** — 主会话 `ruff format --check`              |
| R2A-GAP-06    | GitNexus index stale              | **ACCEPTED** — `detect_changes` LOW；合并后 re-index |
| A05-R2a-P2-05 | phase3 测试未 patch ResourceGuard | **DEFERRED** — 非 R2a 回归项                         |
| A05-R2a-P2-06 | `datetime.now` 非冻结时钟         | **DEFERRED** — 预存模式                              |
| A08-R2a-P2-03 | 未重跑 A6 benchmark               | **DEFERRED** — R2b 前或 nightly                      |

---

## 3. 不变量 I1–I7（主会话复验）

| #   | 结果                                            |
| --- | ----------------------------------------------- |
| I1  | PASS — 53+ ingestion tests                      |
| I2  | PASS — `file_registry_delta == 1`               |
| I3  | PASS — phase4 artifacts                         |
| I4  | PASS — single fetch_log                         |
| I5  | PASS — 行为键不变；归档 JSON 注释键不追加入代码 |
| I6  | PASS — sandbox only                             |
| I7  | PASS — facade re-export + 新门禁测试            |

---

## 4. 明确未做（边界）

- PR-R2b / R2c / R2d
- Batch 2.75 live pilot
- migration 008
- orchestrator 拆分

---

## 5. 合并建议

**APPROVE MERGE** PR #25 after audit-fix commit pushed.

回滚：`git revert <merge-sha> -m 1` + `pytest tests/test_layer1_observation_ingestion.py -q --basetemp=.audit-sandbox/pytest-r2a-rollback`

---

## 6. 分 agent 报告索引

主会话子 agent 输出见对话 transcript；维度与 `docs/quality/audit_evidence/round3_batch25/临时报告/ROUND3_BATCH25_AUDIT_AGENT_*.md` 对齐。
