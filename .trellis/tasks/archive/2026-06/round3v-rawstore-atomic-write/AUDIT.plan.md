# AUDIT 计划 — B3V-STOR RawStore Atomic Write

> 读者：主会话 + A1–A8 · audit.jsonl 第一条 = 本文件

---

## 0. 元信息

| 字段      | 值                              |
| --------- | ------------------------------- |
| 任务 slug | `round3v-rawstore-atomic-write` |
| Owned VR  | `VR-STOR-001`                   |

## 1. 维度 — Skill 冻结

| 维  | Agent            | Skill                                                     | 本任务   | 已执行 |
| --- | ---------------- | --------------------------------------------------------- | -------- | ------ |
| A1  | audit-spec       | trellis-check + doubt-driven-development                  | 必做     | [ ]    |
| A2  | audit-ponytail   | ponytail-review + doubt-driven-development                | 必做     | [ ]    |
| A3  | audit-security   | security-and-hardening + doubt-driven-development         | 必做     | [ ]    |
| A4  | audit-quality    | code-review-and-quality + doubt-driven-development        | 必做     | [ ]    |
| A5  | audit-completion | verification-before-completion + doubt-driven-development | 必做     | [ ]    |
| A6  | audit-perf       | doubt-driven-development                                  | **不用** | [ ]    |
| A7  | audit-ops        | doubt-driven-development                                  | 必做     | [ ]    |
| A8  | audit-test-gap   | testing-guidelines + doubt-driven-development             | 必做     | [ ]    |
| A9  | 主会话           | —                                                         | 必做     | [ ]    |

## 2. 维度验证矩阵

| 维  | 验证类型        | 命令 / 检查                                     | 环境      | 通过条件                      | 已执行 |
| --- | --------------- | ----------------------------------------------- | --------- | ----------------------------- | ------ |
| A1  | read-only       | 对照 B02_03、hardening、MASTER §2/§3            | local     | 无 scope 泄漏；未改 gate/sync | [ ]    |
| A2  | review-only     | ponytail-review `path_compat.py` `raw_store.py` | local     | 最小 diff；无新依赖           | [ ]    |
| A3  | static          | 路径穿越/沙箱仍有效                             | local     | 既有校验测绿                  | [ ]    |
| A4  | review-only     | 原子写逻辑与 temp 命名                          | local     | 无阻断质量问题                | [ ]    |
| A5  | trace-ac        | AC-STOR-01..05 ↔ §9 evidence                    | local     | 切片可追溯                    | [ ]    |
| A5  | cli-sandbox     | `uv run pytest tests/test_raw_store.py -q`      | local/ci  | 与 Execute 一致               | [ ]    |
| A5  | audit-prod-path | `uv run pytest -q`                              | prod-path | 全绿                          | [ ]    |
| A6  | —               | **跳过 — 本地 I/O helper 小 diff**              | —         | SKIP                          | [ ]    |
| A7  | cli-sandbox     | 无 production DB 写                             | local     | 无 prod 写                    | [ ]    |
| A8  | pytest-isolated | crash/idempotency 五字段齐全                    | local     | §5.3 用例绿                   | [ ]    |

### 2.2 A6 SKIP

本任务跳过性能审计 — 原子写 helper 为本地小范围 I/O 加固。

## 3. Audit Source Trace

| Item      | 原文                                                              | AC               | 证据             |
| --------- | ----------------------------------------------------------------- | ---------------- | ---------------- |
| B02_03    | `B02_03_rawstore_atomic_write.md`                                 | AC-STOR-\*       | execute-evidence |
| playbook  | `BATCH_3V_COORDINATOR_PLAYBOOK.md` §8.3                           | 原子性 PASS      | pytest           |
| hardening | `BATCH_3V_HARDENING_RULES.md`                                     | 无 production 写 | boundary         |
| VR index  | `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | VR-STOR-001      | registry delta   |
| gitnexus  | `research/gitnexus-summary.md`                                    | impact MEDIUM    | full pytest      |

## 4. Audit DoD

- [ ] 7.pre `gitnexus-audit-summary.md`
- [ ] A1–A8（A6 SKIP）
- [ ] A9 汇总 PASS / FAIL
