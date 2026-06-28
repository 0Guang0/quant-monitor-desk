# GitNexus Summary — R3H-03（Plan 1b）

> 2026-06-28

## query: CN market baostock cninfo fetch port

**命中流程：**

- `CninfoMetadataStagedFetchPort.fetch_payload` (`ops/staged_pilot_fetch_ports.py`) — **迁移源** → `cninfo_port.py`
- `DataSourceService.fetch` — 所有 port 必经 orchestrator
- `test_adapter_skeletons` — baostock/cninfo skeleton 回归
- `test_staged_pilot` — cninfo staged 属性测试

## impact 锚定（Execute 改码前必跑）

| 符号 / 区域                              | 理由                          | 风险预判   |
| ---------------------------------------- | ----------------------------- | ---------- |
| `cn_market` normalizer（新建）           | G11/G16 证据 SSOT             | MEDIUM     |
| `staged_pilot_fetch_ports` baostock/cninfo | L2 迁出后 deprecate 调用链  | MEDIUM     |
| `tdx_pytdx_port`                         | 已存在；mootdx 应对齐生命周期 | LOW–MEDIUM |
| `route_planner` CN domain rows           | 禁止 silent primary 替换      | MEDIUM     |
| `license_gate`（新建）                   | QMT/iFinD/xqshare 三门        | LOW        |
| `qmt_xtdata` skeleton adapter            | 迁 port 或显式 disabled 边界  | LOW        |

**索引滞后：** `tdx_pytdx_port` 未入 GitNexus 符号表；Execute boot 建议 `node .gitnexus/run.cjs analyze` 后重跑 `impact()`。

## 禁止触碰（他轨）

- `fred_port`, `yahoo_finance_port`, `kalshi` 等 R3H-01/02/04 符号（registry 行亦禁止）
