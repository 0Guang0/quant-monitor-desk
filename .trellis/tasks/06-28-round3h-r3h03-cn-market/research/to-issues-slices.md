# To-Issues Vertical Slices — R3H-03（Plan 3.5）

> S0–S10 ↔ EXECUTION_INDEX §1 9.x

| Slice | Step | 交付物 | 依赖 |
| ----- | ---- | ------ | ---- |
| S0 | 9.0 | `test_cn_market_adapters.py` 空壳 + tdx 测试扩展 | — |
| S1 | 9.1 | `cn_market.py` + `license_gate.py` + G11/G16 证据契约 | S0 |
| S2 | 9.2 | `baostock_port.py` + replay | S1 |
| S3 | 9.3 | `cninfo_port.py` + replay | S1 |
| S4 | 9.4 | `akshare_port.py` validation-only | S1 |
| S5 | 9.5 | `tdx_pytdx` 加固 + `mootdx_port.py` | S1 |
| S6 | 9.6 | `eastmoney_port.py` + `sina_finance_port.py` | S1 |
| S7 | 9.7 | `ths_ifind` + `qmt_xtdata` + `qmt_xqshare` auth-gated | S1 |
| S8 | 9.8 | registry/coordinator manifest（十源行） | S2–S7 |
| S9 | 9.9 | Layer3/4/5 CN smoke | S2–S4 |
| S10 | 9.10 | 全库 pytest + loop_maintain | S8 |

**并行：** S2–S7 在 S1 绿后可并行；S8 须 S2–S7；S9 可与 S8 部分重叠（仅 smoke 依赖 S2–S4）。

**Phase 3.5 complete**
