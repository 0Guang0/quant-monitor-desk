# GitNexus Summary — B01-C04 staged pilot v3 (Plan 1b)

> Plan 阶段基于 `staged_pilot.py` 静态阅读 + v2 archive；Execute 改码前须 MCP `impact()`。

## 核心符号（upstream 关注）

| 符号                                  | 文件                          | 变更意图                               | 风险                |
| ------------------------------------- | ----------------------------- | -------------------------------------- | ------------------- |
| `run_full_staged_pilot_v2`            | `staged_pilot.py`             | v3 平行入口 `run_full_staged_pilot_v3` | 中 — 勿破坏 v2 测试 |
| `validate_pilot_v2_authorization`     | `staged_pilot.py`             | v3 改为 WL+cap 校验                    | 中                  |
| `APPROVED_PILOT_V2_REQUEST_ENVELOPES` | `staged_pilot.py`             | v3 弃用硬编码 envelope                 | 低 — v2 保留        |
| `approved_pilot_v2_requests`          | `staged_pilot.py`             | v3 从 WL 生成 requests                 | 中                  |
| `build_pilot_v2_closeout`             | `staged_pilot.py`             | v3 closeout + readiness matrix         | 低                  |
| fetch ports                           | `staged_pilot_fetch_ports.py` | 可能窄修 cninfo/akshare                | 低                  |

## 执行流（v2 参照 → v3 扩展）

1. Write caps JSON → authorize each request → route preview → fetch (mock/live) → raw manifest → staging manifest → validation report → conflict dry-run → mutation proof → closeout
2. v3 差异：**request 集合来自 WL loader**，非 `APPROVED_PILOT_V2_*`

## 测试锚点

- `tests/test_staged_pilot.py` — v2 回归；v3 新测独立文件
- `tests/test_raw_store.py` — storage 回归

## Execute 前必做

```text
impact(run_full_staged_pilot_v3)  # 实现后
impact(validate_pilot_v3_whitelist_input)  # 实现后
detect_changes()  # commit 前
```
