# Plan Boot — round3-readonly-data-health-v2 (B01-DH2)

## 用户目标

在 v1 read-only data health 基础上，新增 Batch 01 证据体检 profile（whitelist / FRED / TDX / staged pilot v3 / rollup），输出 PASS/WARN/FAIL/BLOCKED 只读报告；不 fetch、不写 DB、不建 `source_health_snapshot`。

## 依赖与 gate

| 依赖                                                           | 状态       | Plan 处理                                                                                    |
| -------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------- |
| v1 `data_health.py` 已合并 master                              | 已满足     | 扩展，不重写 v1 规则                                                                         |
| B01-WL `specs/model_inputs/**`                                 | **未合并** | whitelist profile → BLOCKED fixture；Execute 用 `tests/fixtures/data_health/whitelist/`      |
| B01-FRED evidence                                              | 并行开发   | fixture + 合并前对齐 `.trellis/tasks/round3-fred-authorized-sandbox-pilot/execute-evidence/` |
| B01-TDX evidence                                               | 并行开发   | fixture + 合并前对齐 `.trellis/tasks/round3-tdx-manual-probe/execute-evidence/`              |
| B01-SP3 v3 evidence                                            | 并行开发   | fixture + 合并前对齐 `.trellis/tasks/round3-real-data-staged-pilot-v3/execute-evidence/`     |
| master 基线红测 `test_dataHealthIntegration_v2Evidence_bundle` | **已红**   | 纳入 Slice DH2-BASE（§8 序 0）                                                               |

## AC 草稿

- AC-DH2-PROFILE：五 profile + rollup + gate 陈述
- AC-DH2-BLOCKED：缺 whitelist → BLOCKED，非 PASS
- AC-DH2-BOUND：无 fetch / DB 写 / migration / registry 自动闭合
- AC-DH2-BASELINE：v2 integration 测不再假 FAIL（日 K 规则曾运行）
- AC-DH2-TEST：`test_ops_data_health.py` + `test_data_health_v2.py` 语义断言

## 原计划已读

- `R3E_readonly_data_health_v2.md`（forward 卡 B01-C05）
- `R3Y_readonly_data_health_v1.md` + `PROMPT_20`（legacy B01-L03）
- `BATCH_01_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.1 + §3.7 + §2.5/§2.6 + §4 + §8.7
- `BATCH_01_TASK_CARD_MANIFEST.md` + `BATCH_01_HARDENING_RULES.md`
- 四张兄弟 forward 卡：WL / FRED / TDX / SP3（证据 schema 摘要入 source-index）

**Phase P0 complete**
