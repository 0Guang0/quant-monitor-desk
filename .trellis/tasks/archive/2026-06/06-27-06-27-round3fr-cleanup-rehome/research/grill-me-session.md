# Grill-Me Session — R3FR-07

> Phase 3 · 对抗性质问与闭合

## Q1: 既然 `health_check` 已经实现，R3FR-07 是不是只改文档？

**A:** 主体是 cleanup/redirect，但不仅是文档。须 (1) 静态测试锁门防 placeholder 叙事回流；(2) runtime shim 加 canonical 指向；(3) 批次级 ROADMAP/HANDOFF/3G 门禁更新。若仅改 README 而无测试，Audit A8 可判「断言式关闭」。

**闭合:** 计划含 `test_r3fr07_legacy_wrapper_cleanup.py` + 扩展 guardrails。

## Q2: `check_daily_bars` 能否直接删除？

**A:** 否。`_checks_from_bundle` 证据路径仍调用；删除会破坏 v2 profile 以外的 evidence 集成测试。任务卡允许 **compatibility redirect**，不允许破坏已绿测试。

**闭合:** 保留函数；docstring + 可选 DRY 到 `data_health_profiles` 共享规则（行为等价）。

## Q3: 会不会在 cleanup 里偷偷做 3G sandbox write？

**A:** 禁止。`BATCH_3FR_HARDENING_RULES` + 活卡 §8。3G 仅更新 README 前置为「satisfied」，不实现 `R3G-01`。

**闭合:** frozen §8 停止条件；allowed files 不含 sandbox write 脚本。

## Q4: `TdxPytdxProbeFetchPort` 还要改代码吗？

**A:** 最小 diff：模块 docstring + 确认 `fetch_payload` 仍纯委托。不在此文件加 pytdx 逻辑。

**闭合:** Step 9.4 仅注释/文档；`test_tdx_live_manual_probe_authorization` 回归。

## Q5: provider catalog 完成度写 R6 会不会夸大？

**A:** 不会。`MODULE_COMPLETION_RATING` 最多升至 `R2_MINIMAL_VERTICAL_SLICE` 或 `R3_STAGED_FIXTURE_CLOSED`，并注明 R3H 才达 production posture。

**闭合:** Step 9.5 明确 rating movement 一行，不写 R6。

## Q6: 并行开 3G 可以吗？

**A:** 不可以。Coordinator Playbook：R3FR-07 last only；3G 严格串行且需 3F-R 条件 A。本任务合并后才开 `R3G-01` Plan/Execute。

**闭合:** 用户审阅本 Plan 后单线程 Execute R3FR-07，再 Plan 3G。

## 未决项（不阻塞 R3FR-07）

- `B2.5-O-05` FRED live — DEFERRED → 3H/Batch6
- `R3-B2.75-REQ2-EM` — DEFERRED
- Trellis slug 双日期前缀 `06-27-06-27-*` — cosmetic，不 rename 以免破坏路径

## Session outcome

**PASS** — 范围收敛为 cleanup+redirect+index；无新 feature；有测试锁门。
