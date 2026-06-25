# Audit Report — round3-qmd-data-cli（B3F-CLI Repair）

> **Repair Agent：** trellis-implement  
> **Worktree：** `quant-monitor-desk-wt-b3f-cli`  
> **分支：** `feature/round3-qmd-data-cli`  
> **基线：** `7f628c9`  
> **日期：** 2026-06-25

---

## 总判定

| 项                | 值              |
| ----------------- | --------------- |
| **Repair 判定**   | **PASS**        |
| **BLOCKING 修复** | **5/5 CLOSED**  |
| **WARN 修复**     | **全部 CLOSED** |
| **OPEN**          | **0**           |
| **A6**            | SKIP            |

---

## BLOCK 闭合摘要

| ID        | 原问题                        | Repair 动作                           |
| --------- | ----------------------------- | ------------------------------------- |
| B-01      | 交付物未 commit               | `50754417` 已提交；Repair 追加 commit |
| B-02      | 核心文件未跟踪                | 同上                                  |
| B-03/B-04 | MASTER §11 宣称全量 pytest 绿 | §11 改为 scoped §8.3/§10 诚实勾选     |
| B-05      | 缺 `AUDIT.plan.md`            | 已补 `AUDIT.plan.md` + `audit.jsonl`  |

---

## WARN 闭合摘要

| ID                             | Repair 动作                                                                                   |
| ------------------------------ | --------------------------------------------------------------------------------------------- |
| A7-PLAN-01 / W-03 / A4-WARN-01 | `init_basic(dry_run=False)` 现执行 `sync_to_db`；新增 `test_initBasic_noDryRun_syncsRegistry` |
| A7-PLAN-03                     | dry-run 提示改为 `qmd-init-db --sync-registry`                                                |
| A7-PLAN-04                     | `AUDIT.plan.md` §2.1 冻结 A7 命令                                                             |
| W-01                           | `test_syncRegistry_cli_syncsYamlToDb` 改用 `uv run qmd-sync-registry`（无 PYTHONPATH）        |
| W-04                           | `data_cli_contract.yaml` `required_tests` 接线 `test_qmd_data_cli.py`                         |
| A8 sync bypass                 | `test_qmdData_sync_defaultDryRun_printsPlan` 固定 `route_preview` mock                        |
| A8 R3F-CLI-03                  | `test_initDb_syncRegistry_oneLiner` 断言 stdout `sync_registry rows=`                         |
| A8 R3F-CLI-04                  | `test_packaging_*` 增加 `ci_ingestion_smoke.py` 无 `sys.path.insert`                          |
| A5 8.3 evidence                | `8.3-green.txt` 含真实 pytest transcript                                                      |
| A4-WARN-06                     | `ci_ingestion_smoke.py` 双次 `init_db_main()` ponytail 注释                                   |

---

## §3 维度摘要

### 3.1 A1 — PASS

- R3F-CLI-01..05 实现与 scoped 测试对齐
- 禁止项：无 `source_health_snapshot` migration；无默认 live
- Playbook §8.3 scoped pytest+ruff 绿（Repair 复验）

### 3.2 A2 — PASS

- `init-basic` / `health` 为文档化占位或权威路径委托；无阻塞 bloat

### 3.3 A3 — PASS

- sync fail-closed、无密钥/SQL 拼接；`init_basic` 守卫缺口已闭合

### 3.4 A4 — PASS

- ruff scoped 绿；`init_basic` 与契约 `writes_allowed_when_confirmed` 一致

### 3.5 A5 — PASS

- §8.3 execute-evidence 含可审计 pytest 输出；handoff exit 0

### 3.6 A6 — SKIP

- 无 perf AC（见 `AUDIT.plan.md`）

### 3.7 A7 — PASS

- `init_db` / `--sync-registry` 两遍幂等；A7 冻结命令已写入 `AUDIT.plan.md` §2.1

### 3.8 A8 — PASS

- `test_qmd_data_cli.py` 8 条 + `test_sync_jobs.py` 回归；五字段齐全；contract `required_tests` 已接线

---

## pytest 复跑（Repair 后）

```bash
uv run pytest tests/test_sync_jobs.py tests/test_qmd_data_cli.py tests/test_data_cli_contract.py -q
# 21 passed, exit 0

uv run ruff check backend/app/cli scripts/init_db.py scripts/sync_registry.py scripts/qmd_ops.py scripts/ci_ingestion_smoke.py
# All checks passed

python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/round3-qmd-data-cli
# exit 0
```

---

## OPEN 清单

| 类别     | count |
| -------- | ----- |
| BLOCKING | **0** |
| WARN     | **0** |

全量 `uv run pytest -q` 归 integration 主会话轨；本分支不宣称。
