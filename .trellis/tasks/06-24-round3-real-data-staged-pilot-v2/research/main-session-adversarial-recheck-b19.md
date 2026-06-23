# 主会话对抗性复核 — B-19 Staged Pilot v2（2026-06-24）

**worktree：** `quant-monitor-desk-wt-r3-pilot-v2`  
**分支：** `feature/round3-real-data-staged-pilot-v2`  
**复核者：** 主会话  
**对照：** `fix-closure.md`、Phase 7 `a3/a6/a8.md`、子 agent [B-19 A3/A6/A8 fix closure](832bca2c-56fc-4010-8d03-97ba995c53ca)

---

## 结论

| 维度 | 判定 |
|------|------|
| Phase 7 A3/A6/A8 BLOCKING | **已闭合**（OOF-A8-01 route `user_auth_required` 等） |
| fix-closure 与代码一致性 | **经本复核修补后一致** |
| Ponytail | **合规**（SSOT budget、共享 guard、无新依赖） |

---

## 对抗性发现与处置

### 1. 已修补（主会话）

| ID | 发现 | 处置 |
|----|------|------|
| MS-B19-01 | **OOB-2 漂移**：`execute-evidence/` 下 v1 工件 `conflict_check_summary.json`、`validation_report_summary.json`、`production_db_no_mutation_proof.md` 以 untracked 形式再现 | 删除三文件；handoff 仅以 `*_v2.*` 为准 |
| MS-B19-02 | `capture_route_preview_matrix_v2` 在 `required_kinds` 已含 `user_auth_required` 后仍有第二段 `skipped/user_auth` 检查 — 永真冗余 | 删除 4 行死代码（ponytail 最小 diff） |

### 2. 已核对无缺口（抽检）

- **OOB-A3-1 / OOF-P1**：`run_full_staged_pilot_v2` 单次 `reset_network_call_budget(limit=25)`；baostock/cninfo 间不 reset；`sharedAcrossCaptures` 测 consumed=2
- **OOF-P2 / OOF-P5**：ResourceGuard HARD_STOP 跳过 live fetch；`resource_guard_caps.json` 含 decision/caps/budget
- **OOF-A8-01**：`route_status_coverage` 含 `user_auth_required`；`qmt_xtdata` → `USER_AUTH_REQUIRED`
- **OOF-A8-02~07**：markdown 测、caps 负向、akshare re_defer、validation `source_used`、manifest Q7 字段 — 均有断言
- **OOB-1**：closeout 三态 `null` 保留；gate 仍 `is True`
- **安全**：无 production clean write；sandbox 隔离；`allow_clean_write` 双 gate

### 3. 维持 defer（非遗漏）

- OOB-A3-3、U-A2-04、OOF-P3/P4/P6、OOF-2/3/4、P7-05 — 与 fix-closure 一致
- v1 测块 docstring 无四元组 — fix-closure 仅承诺 **v2 块 15 测** 补齐，不扩 scope

---

## Ponytail 扫描

| 阶梯 | 结果 |
|------|------|
| YAGNI | 未新拆模块；budget limit 参数化一处 SSOT |
| 复用 | v1 ResourceGuard + mutation_proof 模式照搬 |
| 无新依赖 | 无 |
| 最小 diff | MS 修补：删 v1 工件 + 4 行死代码 |
| 天花板 | consume 粒度、akshare 静态 taxonomy、mutation 多次 COUNT — 已 defer 文档化 |

---

## 验证（本复核后）

| 命令 | 结果 |
|------|------|
| `uv run pytest tests/test_staged_pilot.py -q` | 48 passed |
| `uv run pytest -q` | exit 0 |
