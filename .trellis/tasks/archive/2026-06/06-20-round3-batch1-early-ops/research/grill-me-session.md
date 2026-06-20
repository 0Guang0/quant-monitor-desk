# Grill-Me Session — Round 3 Batch 1

> Plan Phase 3 · 自主审查（无阻塞性用户问题 — 仓库证据已闭合）

## Q1: `R3-PARTIAL-2` 用 fixture E2E 还是 `run_full_load` skeleton？

**推荐：** fixture FetchPort service-path E2E（已有）+ `test_sync_jobs` full_load create 骨架 — registry 为 OR，且无 user-authorized live vendor。

**结论：** 采纳。AC-E2E-1 不新增 live vendor；§8.4 仅 registry 更新 + 复跑既有测试。

## Q2: `DB-R3-001` 是否必须本批写入 real raw/parquet？

**推荐：** 否 — inspect 输出 documented absence（WARN）+ registry RESOLVED with evidence。

**结论：** 采纳。符合 `db_inspect_cli.md` §10 text UX 示例。

## Q3: v1 是否实现 `backend/app/cli/main.py`？

**推荐：** 否 — 契约允许 transitional `scripts/qmd_ops.py` only；仓库尚无 cli 包。

**结论：** 采纳。Phase F packaging defer Round 5。

## Q4: `R3-EARLY-PROD-SCALE-BENCH` 与已 RESOLVED 的 `R2.6-IMPL-7` 关系？

**推荐：** 本批重跑 smoke 归档证据；`R3-EARLY-PROD-SCALE-BENCH` RESOLVED 并引用 routing gate 证据链。

**结论：** 采纳。

## Q5: Batch 1 是否与 `017` 合并以节省时间？

**推荐：** 否 — `ROUND3_BATCH_IMPLEMENTATION_MAP.md` 明确禁止；验收门不同。

**结论：** 采纳。硬边界。

## 开放问题（阻塞 Plan）

无 — 可进入 §8 冻结与 validate-plan-freeze。
