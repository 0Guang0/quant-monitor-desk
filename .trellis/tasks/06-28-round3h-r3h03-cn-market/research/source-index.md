# R3H-03 Source Index（A1-005 SSOT）

> 十源 fetch port 与证据链血缘；Repair 增补。完整 AC 见 `EXECUTION_INDEX.md` §0.1/§2。

| source_id | port | normalizer | auth | replay fixture |
| --- | --- | --- | --- | --- |
| baostock | `fetch_ports/baostock_port.py` | `cn_market.py` | cap only | `tests/fixtures/replay/cn_market/baostock/` |
| cninfo | `fetch_ports/cninfo_port.py` | `cn_market.py` | PDF cap | `tests/fixtures/replay/cn_market/cninfo/` |
| akshare | `fetch_ports/akshare_port.py` | `cn_market.py` | validation_only | mock |
| tdx_pytdx | `fetch_ports/tdx_pytdx_port.py` | `tdx.py` | manual probe gate | — |
| mootdx | `fetch_ports/mootdx_port.py` | `cn_market.py` | tdx_fetch_guards | `tests/fixtures/replay/cn_market/tdx/mootdx_*` |
| eastmoney | `fetch_ports/eastmoney_port.py` | `cn_market.py` | validation_only | mock |
| sina_finance | `fetch_ports/sina_finance_port.py` | `cn_market.py` | validation_only | mock |
| ths_ifind | `fetch_ports/ths_ifind_port.py` | `cn_market.py` | `license_gate` | mock |
| qmt_xtdata | `fetch_ports/qmt_xtdata_port.py` | `cn_market.py` | `license_gate` | mock |
| qmt_xqshare | `fetch_ports/qmt_xqshare_port.py` | `cn_market.py` | `license_gate` | mock |

**共享模块：** `auth/license_gate.py` · `cn_validation_mock.py` · `qmt_mock_common.py` · `tdx_fetch_guards.py`
