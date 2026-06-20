# Audit 计划 — Round 3 Batch 2 Layer 1

> 读者：主会话 + A1–A8 子 agent  
> 必读：本文 + `audit.jsonl`；A5 另读 MASTER §2；Execute §10 证据只读。

---

## 0. 元信息

| 字段            | 值                                     |
| --------------- | -------------------------------------- |
| 任务 slug       | `06-20-round3-batch2-layer1`           |
| audit.jsonl     | 第一条 = 本文件                        |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3b2-audit-prod-equiv` |

## 1. 维度 — Agent — Skill 冻结清单

| 维度 | Agent ID         | Skill                                                     | 本任务 | 产出 | 已执行 |
| ---- | ---------------- | --------------------------------------------------------- | ------ | ---- | ------ |
| A1   | audit-spec       | trellis-check + doubt-driven-development                  | 必做   | §3.1 | [x]    |
| A2   | audit-ponytail   | ponytail-review + doubt-driven-development                | 必做   | §3.2 | [x]    |
| A3   | audit-security   | security-and-hardening + doubt-driven-development         | 必做   | §3.3 | [x]    |
| A4   | audit-quality    | code-review-and-quality + doubt-driven-development        | 必做   | §3.4 | [x]    |
| A5   | audit-completion | verification-before-completion + doubt-driven-development | 必做   | §3.5 | [x]    |
| A6   | audit-perf       | systematic-debugging + doubt-driven-development           | 必做   | §3.6 | [x]    |
| A7   | audit-ops        | doubt-driven-development                                  | 必做   | §3.7 | [x]    |
| A8   | audit-test-gap   | testing-guidelines + doubt-driven-development             | 必做   | §3.8 | [x]    |
| A9   | —                | —                                                         | 必做   | §4   | [x]    |

## 2. 维度验证矩阵

| 维  | 验证类型        | 命令 / 检查                                                                                                        | 环境            | 隔离      | 通过条件                             | 证据 → | 已执行 |
| --- | --------------- | ------------------------------------------------------------------------------------------------------------------ | --------------- | --------- | ------------------------------------ | ------ | ------ |
| A1  | read-only       | 对照 `layer1_axis_contract.yaml`、`snapshot_lineage_contract.yaml`、`layer1_global_regime_panel.md` §13、MASTER §2 | local           | 无写      | 无 scope 泄漏（019+/API/live fetch） | §3.1   | [ ]    |
| A2  | review-only     | ponytail-review `backend/app/layer1_axes/`                                                                         | local           | 无写      | 无过度抽象                           | §3.2   | [ ]    |
| A3  | static          | `rg` 直写 clean 表绕过 WriteManager；forbidden SQL                                                                 | local           | 无写      | 无 mutation 路径                     | §3.3   | [ ]    |
| A4  | review-only     | 审 INSUFFICIENT_HISTORY、SHADOW、lineage 持久化、WriteManager 链                                                   | local           | 无写      | 无阻断质量问题                       | §3.4   | [ ]    |
| A5  | trace-ac        | AC-017/018/LINEAGE/WRIT/RES ↔ §8 evidence                                                                          | local           | 无写      | 全 AC ≥4 分可追溯                    | §3.5   | [ ]    |
| A5  | cli-sandbox     | `.audit-sandbox/r3b2-audit` 复跑 layer1 tests                                                                      | audit-sandbox   | tmp DB    | 与 Execute 一致                      | §3.5   | [ ]    |
| A5  | read-only       | 抽检 `execute-evidence/8.2-green.txt` + `8.5-green.txt` 真实性                                                     | local           | 无写      | 非占位符                             | §3.5   | [ ]    |
| A5  | audit-prod-path | 复制 `data/` → `AUDIT_PROD_ROOT/data`；`uv run pytest tests/test_layer1_*.py -q`；prod DB hash 不变                | audit-prod-path | copy only | 与 Execute 声称一致                  | §3.5   | [ ]    |
| A6  | cli-sandbox     | fixture 500 obs feature compute；`AxisFeatureEngine(profile=eco)`；测 elapsed + RSS                                | audit-sandbox   | tmp       | elapsed ≤ 5s；RSS ≤ 512MB            | §3.6   | [ ]    |
| A6  | audit-prod-path | 同上在 `AUDIT_PROD_ROOT` 数据副本上复跑                                                                            | audit-prod-path | copy      | prod 树未修改                        | §3.6   | [ ]    |
| A7  | cli-sandbox     | `init_db` 二次应用 migration 011 策略；DB hash 前后对比                                                            | audit-sandbox   | copy DB   | 无 prod 污染                         | §3.7   | [ ]    |
| A7  | audit-prod-path | 项目 `data/duckdb/` hash 审计前后不变                                                                              | audit-prod-path | read-only | 无污染                               | §3.7   | [ ]    |
| A8  | pytest-isolated | 补边界：空 `spec_root`；全 forbidden 轴；缺 `quality_rules` YAML                                                   | audit-sandbox   | tmp       | 新测绿或 §4.3                        | §3.8   | [ ]    |
| A8  | audit-prod-path | 复跑 module §13 + common_axis_rules SHADOW 三名                                                                    | audit-prod-path | copy      | 全绿                                 | §3.8   | [ ]    |

## 3. Audit Source Trace

| Item ID                      | 原文                                                  | AC            | 证据                                                  |
| ---------------------------- | ----------------------------------------------------- | ------------- | ----------------------------------------------------- |
| `017`                        | `017_*.md` + `layer1_global_regime_panel.md` §5–6,§13 | AC-017-\*     | `test_layer1_axis_loader.py`, migration 011,五轴 YAML |
| `018`                        | `018_*.md` + module §7–10                             | AC-018-\*     | `test_layer1_interpretation.py`                       |
| `R3-EARLY-LINEAGE-CONSUMERS` | `ROUND3_EARLY_CLOSE_PLAN.md` + lineage contract       | AC-LINEAGE-\* | `axis_snapshot_lineage` + lineage tests               |
| Write path                   | `write_manager.md`                                    | AC-WRIT-1     | WriteManager integration test                         |
| Resource                     | `GLOBAL_RESOURCE_LIMITS`                              | AC-RES-1      | resource guard test                                   |
| D-09                         | ADR-0003                                              | AC-018-1      | feature 字段全集                                      |
| Batch 1 gate                 | archived audit                                        | AC-PRE        | handoff                                               |

## 4. Audit DoD

- [x] 7.pre `gitnexus-audit-summary.md`
- [x] A1–A8 完成（含 audit-prod-path 行）
- [x] A9 汇总 PASS / PASS_WITH_FIXES / FAIL
