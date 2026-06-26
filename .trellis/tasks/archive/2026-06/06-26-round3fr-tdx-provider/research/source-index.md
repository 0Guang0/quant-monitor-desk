# Source Index — R3FR-03 (v4 薄索引)

> v4 权威索引为 `EXECUTION_INDEX.md`；本文件供 plan.freeze / 追溯兼容。

## §A 血缘

| 来源                               | Trellis 映射                  |
| ---------------------------------- | ----------------------------- |
| `R3FR_03_TDX_PROVIDER_REFACTOR.md` | frozen + EXECUTION_INDEX §0.1 |
| `BATCH_3FR README`                 | plan-boot + frozen §8         |
| `BATCH_3FR_COORDINATOR_PLAYBOOK`   | PLAN_REVIEW §8 文件锁         |

## §B manifest（→ implement.jsonl）

见 `EXECUTION_INDEX.md` §3。

## §C 六类

| 类别         | 归并位置                             |
| ------------ | ------------------------------------ |
| decision     | frozen §8 · Batch posture            |
| contract     | fetch_port · guardrails · registry   |
| business     | frozen §1–§2                         |
| architecture | fetch_ports/normalizers 新边界       |
| rule         | GLOBAL + reference guardrails        |
| wiring       | tdx_manual_probe · gate · probe port |

**索引完整**

## §D 路由

`context_pack.json` + `loop_manifest.json`

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
