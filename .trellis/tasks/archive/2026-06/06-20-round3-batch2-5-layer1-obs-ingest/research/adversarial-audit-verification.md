# 对抗性审计核实与修补记录 — Round 3 Batch 2.5

> 2026-06-20 · 主会话 **逐项复核** Agent1（F-01–F-19）+ Agent2（A2-01–A2-25）  
> 复核日期：2026-06-20（第二轮全量核对）

## 闭合状态总览

| 范围               | 项数   | CLOSED | WAIVED | 开放  |
| ------------------ | ------ | ------ | ------ | ----- |
| Agent1 F-01–F-19   | 19     | 19     | 0      | 0     |
| Agent2 A2-01–A2-25 | 25     | 22     | 3      | 0     |
| **合计**           | **44** | **41** | **3**  | **0** |

**WAIVED（非 Plan 阻断）：** A2-08（E11 编译器收窄留后续 PR）、A2-17（to-issues issue 发布 — plan.freeze §3.8）、A2-22（`recommended_slug` display-only — `task.json` notes）。

**Plan 阻断项：** 0（`validate-plan-freeze` exit 0）。

---

## Agent 1 — 逐项闭合（F-01–F-19）

| ID   | 状态   | 修补证据                                                                                                                       |
| ---- | ------ | ------------------------------------------------------------------------------------------------------------------------------ |
| F-01 | CLOSED | `plan-manifest-audit.md` E11a；`integration-ledger.md` pipeline+orchestrator pointer；`MASTER` §3.4 接线；§4 pipeline→只读对照 |
| F-02 | CLOSED | `MASTER` §4 接线默认；§0.6/ledger runners pointer；E11a                                                                        |
| F-03 | CLOSED | `MASTER` §4 + AC-P2-0 冻结 `ENV-E1-DGS10`；`vertical-slices.md` VS-4                                                           |
| F-04 | CLOSED | `original-plan-trace.md` AC 表；`MASTER` §10 AC-GATE 子检查清单（018A §9）                                                     |
| F-05 | CLOSED | `MASTER` §0.4 annex + §0.6 扩展 + §0.6.1 过滤附录                                                                              |
| F-06 | CLOSED | `MASTER` §0.6 去重                                                                                                             |
| F-07 | CLOSED | `MASTER` §8.5 GREEN + §10 Tier A prerequisite；`layer1-ingestion-pipeline-tests.md` §Phase 4                                   |
| F-08 | CLOSED | `audit.jsonl` validation_gate + datasource_service；`AUDIT` §2.2 A3/A4 DbValidationGate                                        |
| F-09 | CLOSED | `MASTER` §3.4 不经 SyncValidationPipeline；§8.1 phase0_db 须含 pipeline 差异节                                                 |
| F-10 | CLOSED | `AUDIT` §3 阶段检查单映射 018A §10                                                                                             |
| F-11 | CLOSED | `implement.jsonl` UNRESOLVED + RESOLVED                                                                                        |
| F-12 | CLOSED | `implement.jsonl` data_sync_command_matrix                                                                                     |
| F-13 | CLOSED | `MASTER` §8.1 矩阵模板 → input-inventory + trace §5                                                                            |
| F-14 | CLOSED | `MASTER` §0.6 已有 platform/capability                                                                                         |
| F-15 | CLOSED | `MASTER` §0.6 config + db_inspector                                                                                            |
| F-16 | CLOSED | AC-P1-1 copy provenance；pipeline-tests Phase 1                                                                                |
| F-17 | CLOSED | `MASTER` §7 Red Flags A4-09                                                                                                    |
| F-18 | CLOSED | pipeline-tests §Phase 1                                                                                                        |
| F-19 | CLOSED | `check.jsonl` 12 条                                                                                                            |

---

## Agent 2 — 逐项闭合（A2-01–A2-25）

| ID    | 状态   | 修补证据                                      |
| ----- | ------ | --------------------------------------------- |
| A2-01 | CLOSED | 本文件；`plan.freeze.md` §3.7 [x]             |
| A2-02 | CLOSED | `AUDIT.plan.md` §2 完整矩阵                   |
| A2-03 | CLOSED | PH-A0–PH-A5 vs A1–A8 分离                     |
| A2-04 | CLOSED | `AUDIT` §2.1/2.2 A5 双行 + §4.5 产出          |
| A2-05 | CLOSED | `AUDIT` §2.2 A6 双行                          |
| A2-06 | CLOSED | `AUDIT` §2.2 A7/A8 双行                       |
| A2-07 | CLOSED | 同 F-01 E11a                                  |
| A2-08 | WAIVED | E11a 文档化；manifest_protocol 后续 PR        |
| A2-09 | CLOSED | `plan.freeze.md` §3.1/§3.2                    |
| A2-10 | CLOSED | `integration-audit.md` PASS_WITH_FIXES        |
| A2-11 | CLOSED | `AUDIT` §3/§4 产出 + 检查单                   |
| A2-12 | CLOSED | `audit.jsonl` 17 条                           |
| A2-13 | CLOSED | `check.jsonl` 12 条                           |
| A2-14 | CLOSED | `MASTER` §12 六列                             |
| A2-15 | CLOSED | 同 F-06                                       |
| A2-16 | CLOSED | `vertical-slices.md` VS-1..7                  |
| A2-17 | WAIVED | `plan.freeze.md` §3.8                         |
| A2-18 | CLOSED | `MASTER` §8.0 Skill artifact-gate 加注        |
| A2-19 | CLOSED | `MASTER` §12 karpathy 8.0 exempt              |
| A2-20 | CLOSED | `MASTER` §8 证据命名约定                      |
| A2-21 | CLOSED | `MASTER` §3.1 qmd CLI HITL OUT_OF_SCOPE       |
| A2-22 | WAIVED | `task.json` notes display-only                |
| A2-23 | CLOSED | `plan-manifest-audit.md` E12 exit 0           |
| A2-24 | CLOSED | `AUDIT` §1.2 combo skills                     |
| A2-25 | CLOSED | PH-A5 vs A5 分离；`MASTER` §8 Audit 列 PH-A\* |

---

## 验证

```text
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest → exit 0
```

## 仍待用户（非审计遗漏）

- `plan.freeze.md` §5 用户批准 → `task.py start`
