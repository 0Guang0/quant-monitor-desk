# Vertical Slices — R3FR-07

> Phase 3.5 to-issues

| Slice ID | 名称                 | 交付物                                   | 依赖      |
| -------- | -------------------- | ---------------------------------------- | --------- |
| S-07-0   | Boot 基线            | `execute-evidence/9.0-*.txt`             | —         |
| S-07-1   | 规划叙事清理         | 3F-R README/manifest 无 placeholder 声称 | S-07-0    |
| S-07-2   | data health shim     | `check_daily_bars` redirect + 可选 DRY   | S-07-1    |
| S-07-3   | CLI redirect         | `health_check` 注释 + doc guardrail 测试 | S-07-1    |
| S-07-4   | TDX wrapper redirect | probe 模块注释                           | S-07-1    |
| S-07-5   | 3F-R 关门 / 3G 入口  | ROADMAP · HANDOFF · 3G README · RATING   | S-07-2..4 |
| S-07-6   | guardrails + loop    | guardrails 扩展 · loop_maintain          | S-07-5    |
| S-07-7   | 全量验收             | full pytest                              | S-07-6    |

映射 frozen §9：`9.0`..`9.7` 与上表一一对应。
