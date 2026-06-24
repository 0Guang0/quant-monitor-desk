# 对抗性审计 — round3-022-layer4-market（Wave C 022 · Repair 复验）

> **模式：** Post-Repair 对抗性复验（当场修复 OPEN；**无 commit**）  
> **模型：** composer-2.5  
> **分支：** `feature/round3-022-layer4-market` @ `quant-monitor-desk-wt-022-layer4`  
> **日期：** 2026-06-24  
> **权威：** `agents/audit-adversarial-authority.md` + playbook §8.2 + `audit.report.md` / `audit_matrix.json` / `research/audit-evidence/a1–a8.md`

---

## Verdict

| 项 | 值 |
| --- | --- |
| **总判定** | **PASS** |
| **BLOCKING OPEN** | **0** |
| **NON-BLOCKING OPEN** | **0** |
| **书面 DEFER** | **4**（owner / phase / closure_test 齐全） |
| **当场修复** | 2 项元数据 OPEN（见下） |

**主会话 §6 + §8.2：** **可进入验收提交流程** — 技术门禁已绿；**须先** 将 worktree 内 `??` 核心交付（`layer4_markets/*.py`、`test_layer4_market_structure.py`、fixture）`git add` 并 commit（playbook §8.5「分支 worktree 已提交」）。

---

## 当场修复（OPEN → 0）

| # | 来源 | 问题 | 修复 |
| --- | --- | --- | --- |
| 1 | `validate-execute-handoff` | `audit_matrix.final`（`PASS_AFTER_REPAIR`）与 `audit.report.md` 末行 PASS 摘要不一致 | `audit.report.md` 末行追加 `**FINAL: PASS_AFTER_REPAIR**` |
| 2 | `validate-execute-handoff` | `task.json` 仍为 `in_progress` 但 matrix 已标 PASS | `task.json` → `status: review`（Audit/对抗性阶段） |

复跑：`validate-plan-freeze` exit **0**；`validate-execute-handoff` exit **0**。

---

## 对抗性复验矩阵（playbook §8.2）

| 维度 | PASS 条件 | 对抗性结果 | 证据 |
| --- | --- | --- | --- |
| **Plan** | plan-freeze exit 0；MASTER L4 AC；§3.3 索引；staged-only + as_of | **PASS** | `validate-plan-freeze` exit 0；`implement.jsonl` 已含 §6 四 wiring（`market_structure.py` / `lineage.py` / `models.py` / `manifest.yaml`） |
| **实现** | `market_structure.py` 可运行；WriteManager 路径（若触 DB） | **PASS** | `MarketStructureBuilder.build()` 14 测绿；**无 DB 写**（MASTER §3.2 defer） |
| **契约** | 符合 `layer4_market_contract.yaml`；不复制 L5；无交易语义 | **PASS** | boundaries + quality_rules P2/P3 已接线；P1 `session_type` 例外 → DEFER |
| **Lineage** | §15 字段 + no-future-data 测 | **PASS** | `test_marketSnapshot_lineageRequiredFieldsComplete`；breadth **与** calendar 未来观测双测 |
| **测试** | layer4 测全绿；五字段 + §2.2.2；无全市场扫描 | **PASS** | **14 passed**；docstring 五字段齐全；A6 SKIP 已记 |
| **MAP 验证** | layer4 + batch3 gate 绿 | **PASS** | 14 + **2** passed |
| **任务卡验收** | `pytest -q` 全绿；ruff 相关路径 | **PASS** | 全库 exit 0（1 skip）；ruff All checks passed |
| **Audit** | A1–A8；A6 SKIP 在 matrix | **PASS** | 八维证据已读；Repair 闭合 9 项 |
| **边界** | 未改 forbidden 路径 | **PASS** | `git diff master` 无 `staged_pilot` / `mutation_proof` / `staged_evidence` / registry 三件套 |

---

## 门控复跑（sandbox）

| 命令 | exit | 摘要 |
| --- | --- | --- |
| `python .trellis/scripts/task.py validate-plan-freeze <task-dir>` | **0** | Plan freeze passed |
| `python .trellis/scripts/task.py validate-execute-handoff <task-dir>` | **0** | Handoff passed（修复后） |
| `uv run pytest tests/test_layer4_market_structure.py -q` | **0** | **14 passed** |
| `uv run pytest tests/test_batch3_staged_downstream_gate.py -q` | **0** | **2 passed** |
| `uv run pytest -q` | **0** | 全库绿 |
| `uv run ruff check backend/app/layer4_markets tests/test_layer4_market_structure.py` | **0** | All checks passed |

---

## Repair 闭合对抗性抽检

| 原 OPEN ID | Repair 声称 | 对抗性复验 |
| --- | --- | --- |
| A5-E8 | implement.jsonl §6 wiring | **CLOSED** — L58–61 四路径存在；plan-freeze 0 |
| A1-P2 | 非负 volume | **CLOSED** — `_load_breadth_row:376-380` + `test_marketBreadth_rejectsNegativeVolume` |
| A1-P3 | calendar source/quality | **CLOSED** — `_load_calendar_rows:332-335` 强制 `_CALENDAR_SOURCE_FIELDS` |
| AA-022-A8-01 | 非交易日测 | **CLOSED** — `test_marketSnapshot_rejectsNonTradingDay` |
| AA-022-A8-02 | 缺 manifest/calendar | **CLOSED** — 两专用测 |
| AA-022-A8-03 | breadth 缺字段 | **CLOSED** — `test_marketBreadth_rejectsMissingRequiredField` |
| A4-NB-3 | calendar 未来 as_of | **CLOSED** — `test_marketSnapshotRejectsFutureCalendarInput` |
| OOB-A3-1 | bundle_dir 越界 | **CLOSED** — `test_marketAdapter_bundleDirOutsideProject_rejects` |
| A2-mutate-merge | 三 `_mutate_*` 同构 | **CLOSED** — `_mutate_bundle_file` + 薄包装（purpose 不变） |

**未在 Repair 闭合、经对抗性接受为 DEFER：**

| ID | 描述 | owner | phase | closure_test | 合理性 |
| --- | --- | --- | --- | --- | --- |
| A1-P1 | `session_type` 非交易日例外 | Wave D / Batch 6 | multi-session calendar | `test_marketSnapshot_sessionTypeAllowsNonTradingDay` | 022 硬拒绝非交易日与 staged 骨架一致；例外属 Batch 6 |
| EXT-5 | L3/L4 staged manifest ~52 行重复 | Wave C merge coordinator | Batch 6+ `core/staged_bundle.py` | L3+L4 迁移测 + 零重复 rg | **ponytail 梯级 2**；022 镜像 L3 可接受，跨层抽取超 scope |
| A4-NB-2 | 畸形数值 `ValueError` 泄漏 | 022 follow-up | error model slice | `test_marketBreadth_rejectsNonNumericAdvancers` | 主路径 `Layer4MarketError`；边缘解析可 Batch 6 对齐 L3 |
| OOB-A3-4 | symlink 路径天花板 | security hardening | untrusted bundle_dir | `test_stagedBundle_rejectsSymlinkEscape` | 与 L3 同天花板；staged fixture 信任边界内可接受 |

---

## ponytail 对抗性（A2）

| 检查 | 结果 |
| --- | --- |
| mutation helper 合并 | **PASS** — `_mutate_bundle_file` 单点；三薄包装保留语义 |
| 无跨层抽取 | **PASS** — `rg staged_bundle` layer4 无命中；EXT-5 书面 defer |
| `ponytail:` 注释 | **PASS** — `_build`、`_mutate_bundle_file`、`collect_result_field_names` |
| REGISTRY_SEEDS / adapter | **不删** — explicit AC；非 YAGNI 越界 |

---

## 计划外发现（对抗性搜索）

> 已对照 a1–a8 `## 计划外发现`、契约 quality_rules、MASTER 外边界、`market_structure.py` 全分支。

| ID | 级别 | 发现 | 处置 |
| --- | --- | --- | --- |
| AA-022-ADV-01 | INFO | `project_map.generated.json` `layer4_markets.forbidden_claims` 仍为空（A3 OOB-A3-3） | 文档防御；`loop_maintain` Batch 6+ 偿还；**非运行时 OPEN** |
| AA-022-ADV-02 | INFO | 核心交付文件仍为 `git status ??` 未跟踪 | **主会话 commit gate**；非对抗性 BLOCKING |
| — | — | live fetch / WriteManager bypass / registry 写 / 跨 forbidden 路径 | **无发现** |

**显式声明：** 对抗性搜索未发现新的 BLOCKING 或 NON-BLOCKING OPEN；DEFER 4 条均有书面 owner/phase/closure_test。

---

## A1–A8 维度摘要（复验）

| 维 | Repair 后 | 对抗性 |
| --- | --- | --- |
| A1 | PASS | PASS — quality_rules P2/P3 闭合；P1 defer |
| A2 | PASS | PASS — mutate 合并；EXT-5 defer 合理 |
| A3 | PASS | PASS — bundle_dir 测闭合；symlink defer |
| A4 | PASS | PASS — 测试缺口闭合；NB-2 defer |
| A5 | PASS | PASS — plan-freeze + handoff 绿 |
| A6 | SKIP | SKIP — 无 hot path |
| A7 | PASS | PASS — 零 DB 写 |
| A8 | PASS | PASS — 14 测五字段齐全 |

---

## 主会话交接

| 项 | 状态 |
| --- | --- |
| 对抗性审计 PASS | **是** |
| OPEN 归零 | **是**（含当场元数据修复） |
| §8.2 技术行 | **全 PASS** |
| §6 可勾选 | **是**（commit 前） |
| worktree 已提交 | **否** — 主会话须 commit `layer4_markets/**` + tests + fixture |
| GitNexus `detect_changes()` | 主会话 commit 前必跑 |
| `loop_maintain.py` | 主会话 commit 前建议 `--fix`（含 AA-022-ADV-01 可选） |

---

**FINAL: PASS**
