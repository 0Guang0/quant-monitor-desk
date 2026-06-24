# Project Overview — B01-C04 staged pilot v3

## 任务一句话

把 v2 硬编码小样本 staged pilot 升级为 **model input whitelist 驱动** 的 v3，覆盖 baostock 日线、cninfo 公告元数据、akshare 校验对照，产出可审计的 raw/staging 证据链。

## 系统位置

```
specs/model_inputs/** (B01-WL)
        ↓ read-only at Execute Boot
backend/app/ops/staged_pilot.py  ← v3 orchestration
        ↓
staged_pilot_fetch_ports.py → DataSourceService → adapters
        ↓
storage/staged_evidence.py + raw_store
        ↓
validators (data_quality, source_conflict) — dry-run
        ↓
.trellis/tasks/.../execute-evidence/* (v3 artifacts)
```

## 关键边界（Playbook §2.6）

| Owns | Must not |
| ---- | -------- |
| `staged_pilot.py` 主体（v3 路径） | FRED/TDX/QMT/Yahoo production |
| baostock/cninfo/akshare registry **proposed delta** | production clean write |
| `tests/test_real_data_staged_pilot_v3.py`（Execute 新建） | `specs/model_inputs/**` 写入 |
| `storage/staged_evidence.py` 窄改 | `data_health.py` 主体 |

## 当前基线（worktree `wt-b01-sp3`）

- v2 已实现：`run_full_staged_pilot_v2`, `APPROVED_PILOT_V2_REQUEST_ENVELOPES`, caps JSON
- v3 未实现：无 `pilot_v3` / whitelist loader 符号
- `specs/model_inputs/**`：**不存在** → Execute 阻塞项

## 合并轨道

Track A 序 5：`feature/round3-real-data-staged-pilot-v3`，前提 **B01-WL 已合并**（playbook §7.2）。
