# Vertical Slices — B3V-SYNC (/to-issues · Plan 3.5)

> **SSOT 对齐：** `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §0.2 + §6（2026-06-28 quiz）  
> 冻结为 MASTER §8 · 对应任务卡 §5 B02-SYNC-01..06（SYNC-06 拆 06A/B/C）

## SYNC-BOOT..05（不变）

| 序 | ID | 垂直切片 | 交付物（完标准） | 依赖 | AC | MASTER §9 |
|----|-----|----------|------------------|------|-----|-----------|
| 0 | SYNC-BOOT | 基线 RED | 契约/runtime 现状断言 RED（parity + deferred） | — | AC-SYNC-PLAN | 9.0 |
| 1 | SYNC-01 | 契约 support matrix | `sync_job_contract.yaml` 含 `implemented_job_types` / `reserved_job_types` + deferred 元数据 | BOOT | AC-SYNC-002 | 9.1 |
| 2 | SYNC-02 | Runtime parity | 模块常量 `IMPLEMENTED_JOB_TYPES` == 契约 == 可调用 `run_*` 方法集 | SYNC-01 | AC-SYNC-002 | 9.2 |
| 3 | SYNC-03 | Reserved deferred | `run_full_load` / `run_data_quality` / `run_revision_audit` 返回稳定 `DeferredJobTypeError`（code/owner/phase/docs_anchor） | SYNC-02 | AC-SYNC-002 | 9.3 |
| 4 | SYNC-04 | Registry reconcile | `D2-P1-1` proposed delta + 更新 `test_advA3_016` purpose（deferred 非 NIE） | SYNC-03 | AC-SYNC-REG | 9.4 |
| 5 | SYNC-05 | Crash-window 审查 | 文档化 ADR-001 窗口 + 注入 hook 点（`IncrementalJobRunner` 写提交后/COMPLETED 前） | SYNC-03 | AC-SYNC-001 | 9.5 |

## SYNC-06 拆票（quiz 2026-06-28 · 3 GitHub issue）

| Issue | ID | 垂直切片 | 交付物 | 依赖 | AC | MASTER §9 | 路径 B 替代 |
| ----- | -- | -------- | ------ | ---- | -- | --------- | ----------- |
| 1 | **SYNC-06A** | VR-SYNC-001 最小恢复实现 | `recover_stuck_writing_job`（或等价）+ SYNC-05 hook 接线；**不改** `write_contract` / ADR / WriteManager 写模式语义 | SYNC-05 | AC-SYNC-001 | **9.6** | → `research/sync-001-handoff.md` 草稿（不实现恢复） |
| 2 | **SYNC-06B** | crash-window pytest WRITING→COMPLETED | 注入写提交后/COMPLETED 前失败；断言 WRITING+write_id 可恢复 COMPLETED；RED→GREEN 证据 | SYNC-06A | AC-SYNC-001 | **9.7** | **skip**（handoff 票代替关账路径） |
| 3 | **SYNC-06C** | VR-SYNC-001 关账或 handoff 闭合 | 路径 A：`research/registry_proposed_delta.yaml` 关 VR-SYNC-001；路径 B：handoff 定稿 + 精确 re-defer；**主会话** registry 批闭合 | SYNC-06B 或 06A(B) | AC-SYNC-CLOSE | **9.8** | 同左 |

### 路径门控（SYNC-06 系列）

| 条件 | 路径 | 06A | 06B | 06C |
|------|------|-----|-----|-----|
| 注入测试 + 最小 recovery 可在不改 write 契约前提下 GREEN | **路径 A** | 实现 recovery | crash/recovery pytest | proposed delta 关 VR-SYNC-001 |
| 需同事务 COMPLETED 或改 WriteManager 写模式语义 | **路径 B** | handoff 文档票 | skip | handoff 定稿 + re-defer |

## 测试路径替换

| 任务卡 / Playbook 引用 | 实际路径 |
|------------------------|----------|
| `tests/test_sync_runners.py` | **不存在** → `tests/test_sync_orchestrator.py` + 可选 `tests/test_sync_job_contract.py`（新建，仅当 orchestrator 文件过大） |

## Execute 依赖（C04 ← C01）

| 项 | 说明 |
|----|------|
| Plan | 可与 B3V-C01 **并行** Plan |
| Execute | SYNC-06 系列 **须 rebase 已 merge 的 B3V-C01**（`write_contract.yaml` / WriteManager 写模式语义只读对齐） |
| Merge | Wave 0 序 **6**（C05→C06→C01→C02→C03→**C04**） |

## 禁止

- `qmd data` CLI release
- production clean write
- 子 agent 直接 CLOSED registry（仅 proposed delta）
