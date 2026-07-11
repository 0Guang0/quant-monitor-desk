"""阶段性脚本：为 task/ 下 19 个流水线平级 task 生成三件套骨架。

业务价值：统一 Phase 1 按流水线拆票后的目录与文档入口，避免子票与大杂烩 plan。
退役/清理：task-19-phase1-gate 关账且各票 progress 全绿后，可删除本脚本（2026-Q3 或 P1-GATE 后）。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "task"

TASKS: list[tuple[int, str, str, str, str, str]] = [
    (
        1,
        "task-01-source-registry",
        "源注册与 capability",
        "data_sources.md · source_capability_registry.md",
        "02",
        "source_registry · capabilities · enable/disable · F-16/F-17",
    ),
    (
        2,
        "task-02-source-route-plan",
        "SourceRoutePlan 路由计划",
        "source_route_plan.md · source_route_contract.yaml",
        "03",
        "SourceRoutePlanner · route_grade · F-07/F-14 路由侧",
    ),
    (
        3,
        "task-03-resource-guard",
        "ResourceGuard",
        "performance_limits.md · resource_limits.yaml",
        "04",
        "eco/normal/batch · PAUSE · F-19",
    ),
    (
        4,
        "task-04-datasource-fetch",
        "DataSourceService 正式抓取",
        "data_sources.md · qmt_xtdata_adapter.md",
        "05",
        "Service.fetch · fetch_port · F-01",
    ),
    (
        5,
        "task-05-raw-store",
        "Raw 层与 fetch_log",
        "local_file_system.md · 04_data_architecture.md",
        "06",
        "raw · file_registry · fetch_log",
    ),
    (
        6,
        "task-06-staging",
        "Staging 暂存",
        "duckdb_and_parquet.md · data_sync_orchestrator.md §13.2",
        "07",
        "staging 表 · STAGED 状态衔接",
    ),
    (
        7,
        "task-07-data-quality-validator",
        "DataQualityValidator",
        "data_validation_and_conflict.md",
        "08",
        "ValidationReport · data_quality_log",
    ),
    (
        8,
        "task-08-source-conflict-validator",
        "SourceConflictValidator",
        "data_validation_and_conflict.md · source_conflict_rules.yaml",
        "09",
        "冲突阈值 · escalation",
    ),
    (
        9,
        "task-09-write-manager",
        "WriteManager 入库",
        "write_manager.md · lock_and_concurrency_policy.md",
        "10",
        "唯一 clean 写口 · write_audit_log",
    ),
    (
        10,
        "task-10-sync-orchestrator",
        "DataSyncOrchestrator 编排核心",
        "data_sync_orchestrator.md §13.1–13.2 · §13.9",
        "11",
        "状态机 · data_sync_job · 管线接缝",
    ),
    (
        11,
        "task-11-job-incremental",
        "IncrementalUpdateJob",
        "data_sync_orchestrator.md §12.3",
        "12",
        "cursor/watermark · 不重复主键",
    ),
    (
        12,
        "task-12-job-backfill",
        "BackfillJob",
        "data_sync_orchestrator.md §12.4",
        "13",
        "分片/cap · F-18",
    ),
    (
        13,
        "task-13-job-full-load",
        "FullLoadJob",
        "data_sync_orchestrator.md §12.2",
        "14",
        "初始化全量语义",
    ),
    (
        14,
        "task-14-job-reconcile",
        "ReconcileJob",
        "data_sync_orchestrator.md §12.6",
        "15",
        "冲突后双源重抓",
    ),
    (
        15,
        "task-15-job-revision-audit",
        "RevisionAuditJob",
        "data_sync_orchestrator.md §12.5 · §13.4.4",
        "16",
        "revision diff · F-08",
    ),
    (
        16,
        "task-16-job-data-quality",
        "DataQualityJob",
        "data_sync_orchestrator.md §13.4.6",
        "17",
        "须调 task-07 · F-09",
    ),
    (
        17,
        "task-17-cli-data-commands",
        "CLI 四命令",
        "data_cli_contract.yaml",
        "18",
        "AcceptanceReport · F-03 · 接缝正名",
    ),
    (
        18,
        "task-18-scheduler",
        "Scheduler",
        "sync_scheduler_profiles.yaml · §13.6",
        "19",
        "daily_close · F-06 · 禁 synthetic PASS",
    ),
    (
        19,
        "task-19-phase1-gate",
        "P1-GATE 总关账",
        "PHASE1_PRD.md · data_cli_contract.yaml",
        "—",
        "daily_close 整单 · G1–G8 · 不承载模块修复",
    ),
]


def _plan(seq: int, slug: str, title: str, authority: str, next_task: str, scope: str) -> str:
    dep = f"task-{seq - 1:02d}" if seq > 1 else "无"
    nxt = f"task-{next_task}" if next_task != "—" else "（关账终点）"
    return f"""# {slug} · Implementation Plan

> **序号：** {seq:02d}/19 · **阶段：** {title}
> **前置：** {dep} 关账后方可开工本票
> **后继：** {nxt}
> **权威：** `MIGRATION_MAP.md` 索引 → {authority}

---

## 目标

将 **{title}** 做到与设计文档一致的 **R4 成品形态**（本步范围内）。

## 范围

- {scope}

## 不在本票

- 下游步骤的实现（见 `TASK_PIPELINE_INDEX.md` 后继 task）
- 除非本步接缝明确要求，不修改其他 task 的 findings

## 关账 AC（R4）

- [ ] 回读本步 design 权威，逐条有实现或 ponytail+升级路径
- [ ] `findings.md` 本票条目全部 ∈ {{已修复, 按设计, 阶段外置（须登记）}}
- [ ] 本步至少有 **一条** 可运行验证（pytest 或 CLI）证明行为，非空壳
- [ ] `uv run pytest -q` 全绿（关账日复验）
- [ ] 已更新 `progress.md`

## 允许触及（开工前填写/收窄）

```text
（实现时按 GitNexus impact 补充路径）
```

## 依赖索引

- 总顺序：`../TASK_PIPELINE_INDEX.md`
"""


def _findings(slug: str) -> str:
    return f"""# {slug} · Findings

> **本票只记本步问题。** 全局索引见 `task-19-phase1-gate/PHASE1_COMPLETION_INVENTORY.md`。

---

## 开放项

| ID | 现象 | 标签 | disposition | 证据 |
|----|------|------|-------------|------|
| — | （审计/实现后填写） | | 待修复 | |

---

## 已关闭 / 按设计

| ID | 摘要 | disposition | 证据 |
|----|------|-------------|------|
| — | | | |
"""


def _progress(slug: str) -> str:
    return f"""# {slug} · Progress

> **更新：** 2026-07-10 · 骨架创建

| 项 | 状态 |
|----|------|
| 本票开工 | ⏳ 待前置关账 |
| task_plan AC | ⏳ |
| findings 清零 | ⏳ |
| pytest 关账复验 | ⏳ |
"""


def main() -> None:
    for seq, slug, title, authority, next_task, scope in TASKS:
        d = ROOT / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "task_plan.md").write_text(
            _plan(seq, slug, title, authority, next_task, scope), encoding="utf-8"
        )
        (d / "findings.md").write_text(_findings(slug), encoding="utf-8")
        (d / "progress.md").write_text(_progress(slug), encoding="utf-8")
    print(f"scaffolded {len(TASKS)} tasks under {ROOT}")


if __name__ == "__main__":
    main()
