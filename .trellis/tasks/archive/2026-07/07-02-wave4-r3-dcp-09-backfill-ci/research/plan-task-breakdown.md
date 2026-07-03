# Plan Task Breakdown — R3-DCP-09

## Overview

有界 backfill 产品 CLI + Wave 3 验收脚本 quick/nightly 分层 + GitHub nightly workflow 接 `--run-network` 与 live acceptance findings 门禁。

## Architecture Decisions

| ID   | 决策                                       | 理由                              |
| ---- | ------------------------------------------ | --------------------------------- |
| AD-1 | 复用 `BackfillShardRunner` 不新 runner     | Round2 已验；ponytail             |
| AD-2 | 双层 cap：31 天/片 + invocation max_shards | 防 FullLoad；对齐 smoke benchmark |
| AD-3 | nightly workflow 独立于 PR `ci.yml`        | 真网 flake 不阻塞 PR              |
| AD-4 | findings 按 severity 过滤                  | 修 ACC-LIVE-ACCEPT-NIGHTLY-001    |

## Task List

| CP  | Task                         | Files                                                     | Verify                 |
| --- | ---------------------------- | --------------------------------------------------------- | ---------------------- |
| CP1 | Cap contract + shard planner | `jobs.py`, `bounded_backfill_cap.yaml`, ADR-030           | unit tests             |
| CP2 | CLI backfill                 | `data_commands.py`, `cli/main.py` router                  | CLI tests              |
| CP3 | Replay e2e                   | `test_bounded_backfill_cli_e2e.py`                        | pytest green           |
| CP4 | Acceptance quick             | `wave3_isolated_production_acceptance.py`                 | quick < full time      |
| CP5 | Nightly CI                   | `.github/workflows/nightly.yml`, `docs/ops/nightly_ci.md` | manifest test          |
| CP6 | Live gate                    | `wave3_live_production_acceptance.py`                     | findings severity test |
| CP7 | Registry closeout            | `待修复清单.md`, roadmap                                  | loop_maintain          |

## Checkpoints

1. S00+S01：CLI dry-run 可演示 shard 计划
2. S02：replay e2e 绿
3. S04+S05：nightly 命令清单可本地复现
4. S06：台账四 ID 关账

## Risks

| 风险           | 缓解                                       |
| -------------- | ------------------------------------------ |
| nightly flake  | 单测子集；retry 1；secrets 仅 nightly      |
| cap 误截断数据 | 默认 fail-closed；`--truncate-to-cap` 明示 |
| 与 DCP-05 冲突 | 仅追加 CLI；不改 incremental 路径          |

## Open Questions

（无未决 — 活卡 §3/§6 已界定非目标）
